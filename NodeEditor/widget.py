import heapq
from typing import Dict, Any
import dearpygui.dearpygui as dpg
from collections import defaultdict, deque
import traceback

import uuid6

from .node import NodeType, NodeManager


class NodeEditor:
    @staticmethod
    def _link_callback(sender, app_data, user_data):
        output_attr_uuid, input_attr_uuid = app_data

        try:
            input_attr = dpg.get_item_user_data(input_attr_uuid)
            output_attr = dpg.get_item_user_data(output_attr_uuid)

            if input_attr and output_attr:
                # Clear existing connection on input if any
                input_attr.clear_connection()
                # Add new connection
                output_attr.add_child(sender, input_attr)
        except Exception as e:
            print(f"Error creating link: {e}")

    @staticmethod
    def _delink_callback(sender, app_data, user_data):
        link_id = app_data
        try:
            # Get link configuration to find connected attributes
            link_conf = dpg.get_item_configuration(link_id)
            output_attr_id = link_conf["attr_1"]
            input_attr_id = link_conf["attr_2"]

            # Get attribute objects and clear connection
            input_attr = dpg.get_item_user_data(input_attr_id)
            output_attr = dpg.get_item_user_data(output_attr_id)

            if input_attr and output_attr:
                output_attr.remove_child(input_attr)
        except Exception as e:
            print(f"Error removing link: {e}")

    def __init__(self, NM: NodeManager):
        self._nodes = []
        self.uuid = uuid6.uuid7().hex
        self.parent = None
        self._node_generators = {}  # Registry for node generators
        self.nm = NM

    def register_node_generator(self, node_type: str, generator_func):
        """Register a node generator function for loading"""
        self._node_generators[node_type] = generator_func

    def add_node(self, node):
        self._nodes.append(node)
        return True

    def remove_node_by_UUID(self, UUID):
        self._nodes = [item for item in self._nodes if item[1] != UUID]

    def _find_node_by_id(self, node_id):
        """Find node tuple by node ID"""
        for NID, UUID, node in self._nodes:
            if node.uuid == node_id:
                return NID, UUID, node
        return None

    def _safe_delete_item(self, item_id):
        """Safely delete a DPG item"""
        try:
            if dpg.does_item_exist(item_id):
                dpg.delete_item(item_id)
        except:
            pass

    def _delete_selected(self, sender, app_data):
        """Enhanced deletion with better error handling"""
        try:
            selected_nodes = dpg.get_selected_nodes(self.uuid) or []
            selected_links = dpg.get_selected_links(self.uuid) or []

            # Handle selected links first
            for link_id in selected_links:
                try:
                    if dpg.does_item_exist(link_id):
                        link_conf = dpg.get_item_configuration(link_id)
                        output_attr_id = link_conf.get("attr_1")
                        input_attr_id = link_conf.get("attr_2")

                        if output_attr_id and input_attr_id:
                            input_attr = dpg.get_item_user_data(input_attr_id)
                            output_attr = dpg.get_item_user_data(output_attr_id)

                            if input_attr and output_attr:
                                output_attr.remove_child(input_attr)

                        dpg.delete_item(link_id)
                except Exception as e:
                    raise Exception(f"Error deleting link {link_id}: {e}")

            # Handle selected nodes
            nodes_to_remove = []
            for node_id in selected_nodes:
                NID, UUID, node = self._find_node_by_id(node_id)
                if node:
                    nodes_to_remove.append((NID, UUID, node))

            # Remove nodes from internal list and clear connections
            for NID, UUID, node in nodes_to_remove:
                try:
                    # Clear all connections
                    node.clear_all_connections()

                    # Remove from internal list
                    if any(item[1] == UUID for item in self._nodes):
                        self.remove_node_by_UUID(UUID)

                    # Delete the visual node (this will cascade delete attributes)
                    self._safe_delete_item(node.uuid)
                except Exception as e:
                    raise Exception(f"Error deleting node {node.label}: {e}")

        except Exception as e:
            raise Exception(f"Error in delete operation: {e}")

    def _right_click_menu(self):
        """Add right-click context menu for easier deletion"""
        if dpg.does_item_exist("context_menu"):
            dpg.delete_item("context_menu")
        with dpg.window(label="Context Menu", tag="context_menu"):
            if dpg.add_button(label="Delete Selected", callback=self._delete_selected):
                dpg.hide_item("context_menu")

    def on_drop(self, sender, app_data, user_data):
        source, nodeID, data = app_data

        generator = self.nm.get(nodeID)
        if generator:
            node = generator(source.label, data)

            node.submit(self.uuid, self.parent)
            self.add_node((nodeID, uuid6.uuid7().hex, node))

    def save(self) -> Dict[str, Any]:
        """Export the node graph to dictionary format"""
        # Collect connections
        connections = []
        for NID, UUID, node in self._nodes:
            for output_attr in node._output_attributes:
                for input_attr in output_attr._children:
                    connections.append({
                        'output_attr_uuid': output_attr.uuid,
                        'input_attr_uuid': input_attr.uuid
                    })

        # Save nodes with their NodeManager IDs
        nodes_data = []
        for NID, UUID, node in self._nodes:
            node_dict = node.to_dict()
            node_dict['node_id'] = NID
            node_dict['node_uuid'] = UUID

            nodes_data.append(node_dict)

        return {
            'version': '1.0',
            'nodes': nodes_data,
            'connections': connections
        }

    def load(self, data: Dict[str, Any], clear_existing: bool = True):
        """Import node graph from dictionary format"""
        try:
            if clear_existing:
                self.clear_graph()

            # Create nodes first
            uuid_mapping = {}  # old_uuid -> new_node/attr

            for node_data in data.get('nodes', []):
                # Get node ID from saved data
                node_id = node_data.get('node_id')
                node_uuid = node_data.get('node_uuid')

                if node_id and node_id in self.nm.nodes:
                    # Use the registered node factory/class from NodeManager
                    node_factory = self.nm.get(node_id)

                    node = node_factory(node_data.get('label', 'Node'), node_data.get('data', {}))

                    node.load_from_dict(node_data)
                else:
                    node = None

                # Map old UUIDs to new objects
                uuid_mapping[node_data['uuid']] = node

                # Map attribute UUIDs
                for i, attr_data in enumerate(node_data.get('input_attributes', [])):
                    if i < len(node._input_attributes):
                        uuid_mapping[attr_data['uuid']] = node._input_attributes[i]

                for i, attr_data in enumerate(node_data.get('output_attributes', [])):
                    if i < len(node._output_attributes):
                        uuid_mapping[attr_data['uuid']] = node._output_attributes[i]

                # Set position if available
                if 'position' in node_data:
                    node._load_position = node_data['position']

                self.add_node((node_id, node_uuid, node))

            # Recreate nodes in DPG if editor is already submitted
            if dpg.does_item_exist(self.uuid):
                # Clear existing visual nodes
                children = dpg.get_item_children(self.uuid, slot=1) or []
                for child in children:
                    self._safe_delete_item(child)

                # Submit new nodes
                for NID, UUID, node in self._nodes:
                    node.submit(self.uuid, self.parent)

                    # Set position if available
                    if hasattr(node, '_load_position'):
                        try:
                            dpg.set_item_pos(node.uuid, node._load_position)
                        except:
                            pass
                        delattr(node, '_load_position')

            # Recreate connections
            for conn_data in data.get('connections', []):
                try:
                    output_attr = uuid_mapping.get(conn_data['output_attr_uuid'])
                    input_attr = uuid_mapping.get(conn_data['input_attr_uuid'])

                    if output_attr and input_attr and hasattr(output_attr, 'add_child'):
                        # Clear existing connection on input if any
                        input_attr.clear_connection()
                        # Add new connection
                        if dpg.does_item_exist(self.uuid):
                            output_attr.add_child(self.uuid, input_attr)
                        else:
                            # Store connection for later when editor is submitted
                            output_attr._children.append(input_attr)
                            input_attr.set_parent(output_attr)

                except Exception as e:
                    raise e

            return True

        except Exception as e:
            traceback.print_exc()
            return False

    def clear_graph(self):
        """Clear all nodes and connections"""
        # Clear all connections first
        for NID, UUID, node in self._nodes[:]:  # Create copy to avoid modification during iteration
            node.clear_all_connections()
            if dpg.does_item_exist(node.uuid):
                self._safe_delete_item(node.uuid)

        self._nodes.clear()

    def on_mouse_click(self, sender, app_data):
        if not dpg.is_item_hovered(self.uuid):
            return

        if app_data == dpg.mvMouseButton_Right:
            self._right_click_menu()

    def on_key_press(self, sender, app_data):
        if not dpg.is_item_hovered(self.uuid):
            return

        if app_data == dpg.mvKey_Delete:
            self._delete_selected(sender, app_data)

    def submit(self, parent, width=-160, minimap=True):
        self.parent = parent

        with dpg.child_window(width=width, parent=parent, user_data=self,
                              drop_callback=lambda s, a, u: dpg.get_item_user_data(s).on_drop(s, a, u)):
            with dpg.node_editor(tag=self.uuid,
                                 callback=NodeEditor._link_callback,
                                 delink_callback=NodeEditor._delink_callback,
                                 width=-1, height=-1, minimap=minimap,
                                 minimap_location=dpg.mvNodeMiniMap_Location_BottomRight):
                for node in self._nodes:
                    node.submit(self.uuid, self.parent)

                    # Set position if it was loaded
                    if hasattr(node, '_load_position'):
                        try:
                            dpg.set_item_pos(node.uuid, node._load_position)
                        except:
                            pass
                        delattr(node, '_load_position')

    def _build_execution_graph(self):
        """Build a directed graph for topological sorting"""
        graph = defaultdict(list)  # node -> [dependent_nodes]
        in_degree = defaultdict(int)  # node -> number of dependencies

        # Initialize all nodes
        for NID, UUID, node in self._nodes:
            in_degree[node] = 0

        # Build dependency graph
        for NID, UUID, node in self._nodes:
            for output_attr in node._output_attributes:
                for input_attr in output_attr._children:
                    # Find the node that owns this input attribute
                    for NID, UUID, target in self._nodes:
                        if input_attr in target._input_attributes:
                            graph[node].append(target)
                            in_degree[target] += 1
                            break

        return graph, in_degree

    def _topological_sort(self):
        """Perform topological sort with priority support"""
        graph, in_degree = self._build_execution_graph()

        # Use a priority queue instead of regular queue
        # Store tuples of (-priority, insertion_order, node)
        # Negative priority because heapq is a min-heap (we want higher priority first)
        heap = []
        counter = 0  # For stable sorting when priorities are equal

        for NID, UUID, node in self._nodes:
            if in_degree[node] == 0:
                priority = getattr(node, 'priority', 0) or 0
                heapq.heappush(heap, (-priority, counter, node))
                counter += 1

        execution_order = []
        while heap:
            _, _, current = heapq.heappop(heap)
            execution_order.append(current)

            # Reduce in-degree of dependent nodes
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    priority = getattr(dependent, 'priority', 0) or 0
                    heapq.heappush(heap, (-priority, counter, dependent))
                    counter += 1

        # Check for cycles
        if len(execution_order) != len(self._nodes):
            return self._nodes

        return execution_order

    def _setup_node_helpers(self, node, execution_order, current_index, executed_nodes, execution_count, data, final_data):
        """Setup helper methods for a node"""
        node.execute_next_nodes = lambda n=node, idx=current_index: self._execute_next_nodes(n, execution_order, idx, executed_nodes, execution_count, data, final_data)
        node.execute_connected_next_nodes = lambda n=node, idx=current_index: self._execute_connected_next_nodes(n, execution_order, idx, executed_nodes, execution_count, data, final_data)
        node.execute_connected_next_nodes_multiple = lambda times, n=node, idx=current_index: self._execute_connected_next_nodes_multiple(n, execution_order, idx, executed_nodes, execution_count, data, final_data, times)
        node.get_execution_count = lambda n=node: execution_count[n]

    def process(self, data, no_sort=False):
        """Enhanced process function with topological sorting and self-execution support"""
        # Reset execution state for all nodes
        for NID, UUID, node in self._nodes:
            node.reset_execution()

        if not self._nodes:
            return data

        # Get execution order using topological sort
        if no_sort:
            execution_order = [item[0] for item in self._nodes]
        else:
            execution_order = self._topological_sort()

        # Track which nodes have been executed
        # For self_execute nodes, we track execution count instead
        executed_nodes = set()
        execution_count = defaultdict(int)  # Track how many times each node has executed

        # Execute nodes in proper order
        final_data = []
        for i, node in enumerate(execution_order):
            # For self_execute nodes, allow multiple executions
            is_self_execute = hasattr(node, 'self_execute') and node.self_execute

            # Skip if already executed (only for non-self-executing nodes)
            if node in executed_nodes and not is_self_execute:
                continue

            try:
                # Provide helper functions to ALL nodes (not just self_execute ones)
                # This ensures nested execution calls work properly
                self._setup_node_helpers(node, execution_order, i, executed_nodes, execution_count, data, final_data)

                # Execute the current node
                if node._node_type == NodeType.INPUT:
                    result = node.execute(data)
                elif node._node_type == NodeType.PROCESS:
                    result = node.execute(None)
                elif node._node_type == NodeType.OUTPUT:
                    result = node.execute(None)
                    final_data.append(result)
                else:
                    result = node.execute(data)
                    final_data.append(result)

                executed_nodes.add(node)
                execution_count[node] += 1

            except Exception as e:
                node.setTitleError(str(e))
                raise e

        # Return the final processed frame or a default frame
        if final_data:
            return final_data
        else:
            return data

    def _execute_connected_next_nodes_multiple(self, current_node, execution_order, current_index, executed_nodes,
                                               execution_count, data, final_data, times):
        """Execute connected next nodes multiple times (for loop-like behavior)"""
        all_results = []

        for iteration in range(times):
            iteration_results = self._execute_connected_next_nodes(
                current_node, execution_order, current_index,
                executed_nodes, execution_count, data, final_data
            )
            all_results.append(iteration_results)

        return all_results

    def _execute_connected_next_nodes(self, current_node, execution_order, current_index, executed_nodes,
                                      execution_count, data, final_data):
        """Execute only the directly connected next nodes (children)
        This ensures dependencies are met before execution"""
        next_results = []

        # Get directly connected nodes
        connected_nodes = self._get_connected_next_nodes(current_node)

        for next_node in connected_nodes:
            # Check if node can be re-executed
            is_self_execute = hasattr(next_node, 'self_execute') and next_node.self_execute

            # First, ensure all dependencies of this node are executed
            self._ensure_dependencies_executed(next_node, execution_order, executed_nodes, execution_count, data, final_data)

            # Execute the connected node (allow re-execution for self_execute nodes)
            if next_node not in executed_nodes or is_self_execute:
                try:
                    # Setup helper methods for the node being executed
                    self._setup_node_helpers(next_node, execution_order, current_index,
                                             executed_nodes, execution_count, data, final_data)

                    if next_node._node_type == NodeType.INPUT:
                        result = next_node.execute(data)
                    elif next_node._node_type == NodeType.PROCESS:
                        result = next_node.execute(None)
                    elif next_node._node_type == NodeType.OUTPUT:
                        result = next_node.execute(None)
                        final_data.append(result)
                    else:
                        result = next_node.execute(data)

                    executed_nodes.add(next_node)
                    execution_count[next_node] += 1
                    next_results.append(result)
                except Exception as e:
                    next_node.setTitleError(str(e))
                    raise e

        return next_results

    def _ensure_dependencies_executed(self, node, execution_order, executed_nodes, execution_count, data, final_data):
        """Ensure all dependencies (parent nodes) of a node are executed before the node itself"""
        # Get all parent nodes (nodes that provide input to this node)
        parent_nodes = self._get_connected_past_nodes(node)

        for parent_node in parent_nodes:
            # Check if parent can be re-executed
            is_self_execute = hasattr(parent_node, 'self_execute') and parent_node.self_execute

            if parent_node not in executed_nodes or is_self_execute:
                # Recursively ensure parent's dependencies are met
                self._ensure_dependencies_executed(parent_node, execution_order, executed_nodes, execution_count, data,
                                                   final_data)

                # Execute the parent node
                try:
                    if parent_node._node_type == NodeType.INPUT:
                        result = parent_node.execute(data)
                    elif parent_node._node_type == NodeType.PROCESS:
                        result = parent_node.execute(None)
                    elif parent_node._node_type == NodeType.OUTPUT:
                        result = parent_node.execute(None)
                        final_data.append(result)
                    else:
                        result = parent_node.execute(data)

                    executed_nodes.add(parent_node)
                    execution_count[parent_node] += 1
                except Exception as e:
                    parent_node.setTitleError(str(e))
                    raise e

    def _execute_next_nodes(self, current_node, execution_order, current_index, executed_nodes, execution_count, data,
                            final_data):
        """Execute all nodes that come after the current node in topological order"""
        next_results = []
        for i in range(current_index + 1, len(execution_order)):
            node = execution_order[i]

            # Allow re-execution for self_execute nodes
            is_self_execute = hasattr(node, 'self_execute') and node.self_execute

            if node not in executed_nodes or is_self_execute:
                try:
                    if node._node_type == NodeType.INPUT:
                        result = node.execute(data)
                    elif node._node_type == NodeType.PROCESS:
                        result = node.execute(None)
                    elif node._node_type == NodeType.OUTPUT:
                        result = node.execute(None)
                        final_data.append(result)
                    else:
                        result = node.execute(data)

                    executed_nodes.add(node)
                    execution_count[node] += 1
                    next_results.append(result)
                except Exception as e:
                    node.setTitleError(str(e))
                    raise e

        return next_results

    def _get_connected_past_nodes(self, node):
        """Get list of nodes that are directly connected as inputs to this node"""
        past_nodes = []

        # Check all input attributes of the current node
        for input_attr in node._input_attributes:
            # Get the parent output attribute
            if input_attr._parent:
                # Find which node owns this output attribute
                for NID, UUID, parent_node in self._nodes:
                    if input_attr._parent in parent_node._output_attributes:
                        past_nodes.append(parent_node)
                        break

        return past_nodes

    def _get_connected_next_nodes(self, node):
        """Get list of nodes that are directly connected as outputs from this node"""
        next_nodes = []

        # Check all output attributes of the current node
        for output_attr in node._output_attributes:
            # Get all children (input attributes connected to this output)
            for input_attr in output_attr._children:
                # Find which node owns this input attribute
                for NID, UUID, child_node in self._nodes:
                    if input_attr in child_node._input_attributes:
                        if child_node not in next_nodes:
                            next_nodes.append(child_node)
                        break

        return next_nodes


class DragSource:
    def __init__(self, label: str, nodeID, data, category: str = None):
        self.label = label
        self.category = category
        self.nodeID = nodeID
        self._data = data

    def submit(self, parent):
        dpg.add_button(label=self.label, parent=parent, width=-1)

        with dpg.drag_payload(parent=dpg.last_item(), drag_data=(self, self.nodeID, self._data)):
            dpg.add_text(self.label)


class DragSourceContainer:
    def __init__(self, label: str, width: int = 150, height: int = -1):
        self._label = label
        self._width = width
        self._height = height
        self._uuid = uuid6.uuid7().hex
        self._children = []  # drag sources

    def add_drag_source(self, source: DragSource):
        self._children.append(source)

    def _group_by_category(self):
        """Group drag sources by their category"""
        categories = {}
        for child in self._children:
            category = child.category
            if category not in categories:
                categories[category] = []
            categories[category].append(child)
        return categories

    def submit(self, parent):
        with dpg.child_window(parent=parent, width=self._width, height=self._height, tag=self._uuid,
                              menubar=True) as child_parent:
            with dpg.menu_bar():
                dpg.add_menu(label=self._label)

            # Group children by category and create collapsing headers
            categories = self._group_by_category()

            for category_name, sources in categories.items():
                if category_name:
                    with dpg.tree_node(label=category_name, parent=child_parent, default_open=True) as category_collaps:
                        for source in sources:
                            source.submit(category_collaps)
                else:
                    for source in sources:
                        source.submit(child_parent)
from typing import Dict, Any
import dearpygui.dearpygui as dpg
from collections import defaultdict, deque
import traceback


class OutputNodeAttribute:
    def __init__(self, label: str = "output"):
        self._label = label
        self.uuid = dpg.generate_uuid()
        self._children = []  # output attributes
        self._data = None
        self.custom = None

    def add_child(self, parent, child):
        # Check if connection already exists
        if child not in self._children:
            dpg.add_node_link(self.uuid, child.uuid, parent=parent)
            child.set_parent(self)
            self._children.append(child)

    def remove_child(self, child):
        if child in self._children:
            self._children.remove(child)
            child.set_parent(None)
            child._data = None

    def execute(self, data):
        self._data = data
        for child in self._children:
            child._data = self._data

    def clear_connections(self):
        for child in self._children[:]:  # Create a copy to avoid modification during iteration
            self.remove_child(child)
        self._children = []
        self._data = None

    def submit(self, parent):
        with dpg.node_attribute(parent=parent, attribute_type=dpg.mvNode_Attr_Output,
                                user_data=self, id=self.uuid, label=self._label):
            if self.custom:
                self.custom()
            else:
                dpg.add_text(self._label)

    def to_dict(self) -> Dict[str, Any]:
        """Convert output attribute to dictionary format"""
        return {
            'label': self._label,
            'uuid': self.uuid,
            'type': 'output'
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OutputNodeAttribute':
        """Create output attribute from dictionary"""
        attr = cls(data['label'])
        attr.uuid = data['uuid']
        return attr


class InputNodeAttribute:
    def __init__(self, label: str = "input"):
        self._label = label
        self.uuid = dpg.generate_uuid()
        self._parent = None
        self._data = None

    def get_data(self):
        return self._data

    def set_parent(self, parent: OutputNodeAttribute):
        self._parent = parent

    def clear_connection(self):
        if self._parent:
            self._parent.remove_child(self)
        self._parent = None
        self._data = None

    def submit(self, parent):
        with dpg.node_attribute(parent=parent, user_data=self, id=self.uuid):
            dpg.add_text(self._label)

    def to_dict(self) -> Dict[str, Any]:
        """Convert input attribute to dictionary format"""
        return {
            'label': self._label,
            'uuid': self.uuid,
            'type': 'input'
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InputNodeAttribute':
        """Create input attribute from dictionary"""
        attr = cls(data['label'])
        attr.uuid = data['uuid']
        return attr


class Node:
    def __init__(self, label: str, data, process_func=None):
        self.label = label
        self.uuid = dpg.generate_uuid()
        self.static_uuid = dpg.generate_uuid()
        self._input_attributes = []
        self._output_attributes = []
        self._data = data
        self._process_func = process_func  # Custom processing function
        self._executed = False  # For tracking execution in render cycle
        self._node_type = self.__class__.__name__  # Store node type for reconstruction

    def clear_all_connections(self):
        # Clear all input connections
        for input_attr in self._input_attributes:
            input_attr.clear_connection()

        # Clear all output connections
        for output_attr in self._output_attributes:
            output_attr.clear_connections()

    def add_input_attribute(self, attribute: InputNodeAttribute):
        self._input_attributes.append(attribute)

    def add_output_attribute(self, attribute: OutputNodeAttribute):
        self._output_attributes.append(attribute)

    def process(self, data):
        pass

    def reset_execution(self):
        """Reset execution state for new render cycle"""
        self._executed = False

    def execute(self, data=None):
        """Execute node and propagate data to outputs"""
        if self._executed:
            return data

        self._executed = True

        # Process the data
        output_data = self.process(data)

        return output_data

    def custom(self):
        pass

    def submit(self, parent, mparent):
        with dpg.node(parent=parent, label=self.label, tag=self.uuid):
            for attribute in self._input_attributes:
                attribute.submit(self.uuid)

            with dpg.node_attribute(parent=self.uuid, attribute_type=dpg.mvNode_Attr_Static,
                                    user_data=self, tag=self.static_uuid):
                self.custom()

            for attribute in self._output_attributes:
                attribute.submit(self.uuid)

        pos = dpg.get_mouse_pos(local=False)
        ref_node = dpg.get_item_children(mparent, slot=1)[0]
        ref_screen_pos = dpg.get_item_rect_min(ref_node)

        pos[0] = pos[0] - (ref_screen_pos[0] + 150)
        pos[1] = pos[1] - (ref_screen_pos[1])

        dpg.set_item_pos(self.uuid, pos)

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary format"""
        # Get node position if it exists in DPG
        position = [0, 0]
        try:
            if dpg.does_item_exist(self.uuid):
                position = list(dpg.get_item_pos(self.uuid))
        except:
            pass

        return {
            'label': self.label,
            'uuid': self.uuid,
            'static_uuid': self.static_uuid,
            'node_type': self._node_type,
            'data': self._data,
            'position': position,
            'input_attributes': [attr.to_dict() for attr in self._input_attributes],
            'output_attributes': [attr.to_dict() for attr in self._output_attributes]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """Create node from dictionary"""
        node = cls(data['label'], data['data'])
        node.uuid = data['uuid']
        node.static_uuid = data['static_uuid']

        # Recreate input attributes
        for attr_data in data['input_attributes']:
            attr = InputNodeAttribute.from_dict(attr_data)
            node.add_input_attribute(attr)

        # Recreate output attributes
        for attr_data in data['output_attributes']:
            attr = OutputNodeAttribute.from_dict(attr_data)
            node.add_output_attribute(attr)

        return node


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

    def __init__(self):
        self._nodes = []
        self.uuid = dpg.generate_uuid()
        self.parent = None
        self._node_generators = {}  # Registry for node generators

    def register_node_generator(self, node_type: str, generator_func):
        """Register a node generator function for loading"""
        self._node_generators[node_type] = generator_func

    def add_node(self, node):
        self._nodes.append(node)
        return True

    def remove_node(self, node):
        if node in self._nodes:
            # Clear all connections before removing the node
            node.clear_all_connections()
            self._nodes.remove(node)

    def _find_node_by_id(self, node_id):
        """Find node tuple by node ID"""
        for node in self._nodes:
            if node.uuid == node_id:
                return node
        return None

    def _find_attribute_by_id(self, attr_id):
        """Find attribute by UUID across all nodes"""
        for node in self._nodes:
            for attr in node._input_attributes + node._output_attributes:
                if attr.uuid == attr_id:
                    return attr
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
        if not dpg.is_item_hovered(self.uuid):
            return

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
                    print(f"Error deleting link {link_id}: {e}")

            # Handle selected nodes
            nodes_to_remove = []
            for node_id in selected_nodes:
                node = self._find_node_by_id(node_id)
                if node:
                    nodes_to_remove.append(node)

            # Remove nodes from internal list and clear connections
            for node in nodes_to_remove:
                try:
                    # Clear all connections
                    node.clear_all_connections()

                    # Remove from internal list
                    if node in self._nodes:
                        self._nodes.remove(node)

                    # Delete the visual node (this will cascade delete attributes)
                    self._safe_delete_item(node.uuid)

                except Exception as e:
                    print(f"Error deleting node {node.label}: {e}")

        except Exception as e:
            print(f"Error in delete operation: {e}")

    def _right_click_menu(self, sender, app_data):
        """Add right-click context menu for easier deletion"""
        if dpg.does_item_exist("context_menu"):
            dpg.delete_item("context_menu")

        with dpg.window(label="Context Menu", popup=True, tag="context_menu"):
            if dpg.add_button(label="Delete Selected", callback=self._delete_selected):
                dpg.hide_item("context_menu")

    def on_drop(self, sender, app_data, user_data):
        source, generator, data = app_data
        node = generator(source.label, data)

        node.submit(self.uuid, self.parent)
        self.add_node(node)

    def _build_execution_graph(self):
        """Build a directed graph for topological sorting"""
        graph = defaultdict(list)  # node -> [dependent_nodes]
        in_degree = defaultdict(int)  # node -> number of dependencies

        # Initialize all nodes
        for node in self._nodes:
            in_degree[node] = 0

        # Build dependency graph
        for node in self._nodes:
            for output_attr in node._output_attributes:
                for input_attr in output_attr._children:
                    # Find the node that owns this input attribute
                    for target in self._nodes:
                        if input_attr in target._input_attributes:
                            graph[node].append(target)
                            in_degree[target] += 1
                            break

        return graph, in_degree

    def _topological_sort(self):
        """Perform topological sort to determine execution order"""
        graph, in_degree = self._build_execution_graph()

        # Start with nodes that have no dependencies
        queue = deque()
        for node in self._nodes:
            if in_degree[node] == 0:
                queue.append(node)

        execution_order = []
        while queue:
            current = queue.popleft()
            execution_order.append(current)

            # Reduce in-degree of dependent nodes
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for cycles
        if len(execution_order) != len(self._nodes):
            print("Warning: Circular dependency detected in node graph!")
            return self._nodes

        return execution_order

    def save(self) -> Dict[str, Any]:
        """Export the node graph to dictionary format"""
        # Collect connections
        connections = []
        for node in self._nodes:
            for output_attr in node._output_attributes:
                for input_attr in output_attr._children:
                    connections.append({
                        'output_attr_uuid': output_attr.uuid,
                        'input_attr_uuid': input_attr.uuid
                    })

        return {
            'version': '1.0',
            'nodes': [node.to_dict() for node in self._nodes],
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
                # Create node using registered generator or fallback to base Node class
                node_type = node_data.get('node_type', 'Node')

                if node_type in self._node_generators:
                    node = self._node_generators[node_type](node_data['label'], node_data['data'])
                else:
                    node = Node.from_dict(node_data)

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
                    # Position will be set after submitting to DPG
                    node._load_position = node_data['position']

                self.add_node(node)

            # Recreate nodes in DPG if editor is already submitted
            if dpg.does_item_exist(self.uuid):
                # Clear existing visual nodes
                children = dpg.get_item_children(self.uuid, slot=1) or []
                for child in children:
                    self._safe_delete_item(child)

                # Submit new nodes
                for node in self._nodes:
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
                    print(f"Error recreating connection: {e}")

            print(f"Loaded {len(self._nodes)} nodes and {len(data.get('connections', []))} connections")
            return True

        except Exception as e:
            print(f"Error loading graph: {e}")
            traceback.print_exc()
            return False

    def clear_graph(self):
        """Clear all nodes and connections"""
        # Clear all connections first
        for node in self._nodes[:]:  # Create copy to avoid modification during iteration
            node.clear_all_connections()
            if dpg.does_item_exist(node.uuid):
                self._safe_delete_item(node.uuid)

        self._nodes.clear()

    def submit(self, parent, width=-160):
        self.parent = parent

        with dpg.handler_registry():
            dpg.add_key_down_handler(dpg.mvKey_Delete, callback=self._delete_selected)
            dpg.add_mouse_click_handler(dpg.mvMouseButton_Right, callback=self._right_click_menu)

        with dpg.child_window(width=width, parent=parent, user_data=self,
                              drop_callback=lambda s, a, u: dpg.get_item_user_data(s).on_drop(s, a, u)):
            with dpg.node_editor(tag=self.uuid,
                                 callback=NodeEditor._link_callback,
                                 delink_callback=NodeEditor._delink_callback,
                                 width=-1, height=-1):
                for node in self._nodes:
                    node.submit(self.uuid, self.parent)

                    # Set position if it was loaded
                    if hasattr(node, '_load_position'):
                        try:
                            dpg.set_item_pos(node.uuid, node._load_position)
                        except:
                            pass
                        delattr(node, '_load_position')

    def process(self, data):
        """Enhanced process function with topological sorting and better error handling"""
        try:
            # Reset execution state for all nodes
            for node in self._nodes:
                node.reset_execution()

            if not self._nodes:
                return data

            # Get execution order using topological sort
            execution_order = self._topological_sort()

            # Execute nodes in proper order
            final_data = data
            for node in execution_order:
                try:
                    final_data = node.execute(data)
                except Exception as e:
                    print(f"Error executing node {node.label}: {e}")
                    traceback.print_exc()

            # Return the final processed frame or a default frame
            if final_data is not None:
                return final_data
            else:
                return data

        except Exception as e:
            print(f"Error in render pipeline: {e}")
            traceback.print_exc()

class DragSource:
    def __init__(self, label: str, node_generator, data, category: str = None):
        self.label = label
        self.category = category
        self._generator = node_generator
        self._data = data

    def submit(self, parent):
        dpg.add_button(label=self.label, parent=parent, width=-1)

        with dpg.drag_payload(parent=dpg.last_item(), drag_data=(self, self._generator, self._data)):
            dpg.add_text(self.label)

class DragSourceContainer:
    def __init__(self, label: str, width: int = 150, height: int = -1):
        self._label = label
        self._width = width
        self._height = height
        self._uuid = dpg.generate_uuid()
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
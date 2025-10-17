import time
import dearpygui.dearpygui as dpg
from typing import Dict, Any
import collections

class NodeType:
    INPUT = 0 # Can get data from system but not send output data to system
    PROCESS = 1 # No data from system and not send output data to system
    OUTPUT = 2 # No data from system but send output data to system
    IPO = 3 # Can get data from system and can send output data to system

class OutputNodeAttribute:
    def __init__(self, label: str = "output", id=None):
        self._label = label
        self.uuid = dpg.generate_uuid()
        self._children = []  # output attributes
        self._data = None
        self.custom = None

        if not id:
            self.id = label + str(self.uuid)
        else:
            self.id = id

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

    def set_data(self, data):
        self._data = data
        for child in self._children:
            child.buffer.append(data)

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
            "id": self.id,
            'uuid': self.uuid,
            'type': 'output'
        }

class InputNodeAttribute:
    def __init__(self, label: str = "input", id=None, buffersize=10):
        self._label = label
        self.uuid = dpg.generate_uuid()
        self._parent = None
        self.last_data = None

        self.buffer = collections.deque(maxlen=buffersize)

        if not id:
            self.id = label + str(self.uuid)
        else:
            self.id = id

    def get_data(self):
        try:
            data = self.buffer.popleft()
        except IndexError:
            data = self.last_data

        return data

    def set_parent(self, parent: OutputNodeAttribute):
        self._parent = parent

    def clear_connection(self):
        if self._parent:
            self._parent.remove_child(self)
        self._parent = None
        self.buffer.clear()
        self.last_data = None

    def submit(self, parent):
        with dpg.node_attribute(parent=parent, user_data=self, id=self.uuid):
            dpg.add_text(self._label)

    def to_dict(self) -> Dict[str, Any]:
        """Convert input attribute to dictionary format"""
        return {
            'label': self._label,
            "id": self.id,
            'uuid': self.uuid,
            'type': 'input'
        }


class Node:
    def __init__(self, label: str, data, nodetype=NodeType.IPO, priority=0):
        self.label = label
        self.uuid = dpg.generate_uuid()
        self.static_uuid = dpg.generate_uuid()
        self._input_attributes = []
        self._output_attributes = []
        self._data = data
        self._executed = False
        self._node_type = nodetype
        self.is_error = False
        self.init_pos = None
        self.show_info = True
        self.priority = priority
        self.output_topic = None
        self.input_topic = None
        self._is_submitted = False  # Track if node is rendered

        # for Self-execute node
        self.self_execute = False
        self.execute_next_nodes = None
        self.execute_connected_next_nodes = None
        self.execute_connected_next_nodes_multiple = None
        self.get_execution_count = None

        self.internal_data = {}

    def onCreate(self):
        pass

    def onRemove(self):
        pass

    def clear_all_connections(self):
        # Clear all input connections
        for input_attr in self._input_attributes:
            input_attr.clear_connection()

        # Clear all output connections
        for output_attr in self._output_attributes:
            output_attr.clear_connections()

    def add_input_attribute(self, attribute: InputNodeAttribute, dynamic=False):
        """Add input attribute, optionally rendering it if node is already submitted"""
        self._input_attributes.append(attribute)

        if dynamic and self._is_submitted:
            # Find the position to insert (before static attribute)
            attribute.submit(self.uuid)
            # Reorder to place before static content
            dpg.move_item(attribute.uuid, parent=self.uuid, before=self.static_uuid)

    def add_output_attribute(self, attribute: OutputNodeAttribute, dynamic=False):
        """Add output attribute, optionally rendering it if node is already submitted"""
        self._output_attributes.append(attribute)

        if dynamic and self._is_submitted:
            # Output attributes go after static content
            attribute.submit(self.uuid)

    def remove_input_attribute(self, attribute: InputNodeAttribute):
        """Remove input attribute and clean up connections"""
        if attribute in self._input_attributes:
            # Clear connections first
            attribute.clear_connection()

            # Remove from list
            self._input_attributes.remove(attribute)

            # Delete DPG item if it exists
            if self._is_submitted and dpg.does_item_exist(attribute.uuid):
                dpg.delete_item(attribute.uuid)

    def remove_output_attribute(self, attribute: OutputNodeAttribute):
        """Remove output attribute and clean up connections"""
        if attribute in self._output_attributes:
            # Clear connections first
            attribute.clear_connections()

            # Remove from list
            self._output_attributes.remove(attribute)

            # Delete DPG item if it exists
            if self._is_submitted and dpg.does_item_exist(attribute.uuid):
                dpg.delete_item(attribute.uuid)

    def remove_input_attribute_by_index(self, index: int):
        """Remove input attribute by index"""
        if 0 <= index < len(self._input_attributes):
            self.remove_input_attribute(self._input_attributes[index])

    def remove_output_attribute_by_index(self, index: int):
        """Remove output attribute by index"""
        if 0 <= index < len(self._output_attributes):
            self.remove_output_attribute(self._output_attributes[index])

    def get_input_attribute(self, index: int):
        """Get input attribute by index"""
        if 0 <= index < len(self._input_attributes):
            return self._input_attributes[index]
        return None

    def get_output_attribute(self, index: int):
        """Get output attribute by index"""
        if 0 <= index < len(self._output_attributes):
            return self._output_attributes[index]
        return None

    def clear_all_output_attribute(self):
        for output_attr in self._output_attributes:
            output_attr.clear_connections()

        for attr in self._output_attributes:
            dpg.delete_item(attr.uuid)

        self._output_attributes = []

    def clear_all_input_attribute(self):
        for input_attr in self._input_attributes:
            input_attr.clear_connection()

        for attr in self._input_attributes:
            dpg.delete_item(attr.uuid)

        self._input_attributes = []

    def process(self, data):
        pass

    def reset_execution(self):
        """Reset execution state for new render cycle"""
        self._executed = False
        self.is_error = False

    def execute(self, data=None):
        """Execute node and propagate data to outputs"""
        if self._executed:
            return data

        workingt1 = time.time()

        # Process the data
        output_data = self.process(data)

        if self.show_info:
            dpg.configure_item(self.uuid, label=f"{self.label} ({int((time.time() - workingt1) * 1000)} ms)")

        self._executed = True

        return output_data

    def custom(self):
        pass

    def setTitleError(self, title):
        self.is_error = True
        if self.show_info:
            dpg.configure_item(self.uuid, label=f"{self.label} ({title})")

    def submit(self, parent, mparent):
        with dpg.node(parent=parent, label=self.label, tag=self.uuid):
            for attribute in self._input_attributes:
                attribute.submit(self.uuid)

            with dpg.node_attribute(parent=self.uuid, attribute_type=dpg.mvNode_Attr_Static,
                                    user_data=self, tag=self.static_uuid):
                self.custom()

            for attribute in self._output_attributes:
                attribute.submit(self.uuid)

        if not self.init_pos:
            pos = dpg.get_mouse_pos(local=False)
        else:
            dpg.set_item_pos(self.uuid, self.init_pos)

        self._is_submitted = True
        self.onCreate()

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
            'internal_data': self.internal_data,
            'input_attributes': [attr.to_dict() for attr in self._input_attributes],
            'output_attributes': [attr.to_dict() for attr in self._output_attributes]
        }

    def _update_attributes(self, existing_attrs, new_attrs):
        # Create a quick lookup table from existing attributes by ID
        attr_map = {attr.id: attr for attr in existing_attrs}

        for attr_data in new_attrs:
            attr = attr_map.get(attr_data["id"])
            if attr:
                attr.label = attr_data["label"]
                #attr.uuid = attr_data["uuid"]

    def load_from_dict(self, data: Dict[str, Any]):
        """Create node from dictionary"""
        self.static_uuid = data['static_uuid']
        self.internal_data = data['internal_data']
        self.init_pos = data['position']
        self._node_type = data['node_type']
        #self.uuid = data['uuid']

        # Recreate input attributes
        self._update_attributes(self._input_attributes, data["input_attributes"])
        self._update_attributes(self._output_attributes, data["output_attributes"])

class NodeManager:
    def __init__(self):
        self.nodes = {}

    def register(self, id: str, node_factory):
        """Register a node with a given ID"""
        self.nodes[id] = node_factory

    def unregister(self, id: str):
        """Remove a node by ID"""
        if id in self.nodes:
            del self.nodes[id]
            return True
        return False

    def get(self, id: str):
        """Get a node by ID"""
        return self.nodes.get(id, None)
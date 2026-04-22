from __future__ import annotations
from client.models.elements    import FlowchartElement
from client.models.connections import Connection


class FlowchartDocument:
    def __init__(self, name="Без названия"):
        self.name        = name
        self.elements    = []
        self.connections = []
        self._selected_id      = None
        self._selected_conn_id = None

    def add_element(self, el):
        self.elements.append(el)

    def remove_element(self, element_id):
        el = self.get_element(element_id)
        if el is None:
            return None
        self.elements = [e for e in self.elements if e.id != element_id]
        self.connections = [
            c for c in self.connections
            if c.source_id != element_id and c.target_id != element_id
        ]
        if self._selected_id == element_id:
            self._selected_id = None
        return el

    def get_element(self, element_id):
        for el in self.elements:
            if el.id == element_id:
                return el
        return None

    def element_at_position(self, x, y):
        for el in reversed(self.elements):
            if el.contains_point(x, y):
                return el
        return None

    def add_connection(self, conn):
        self.connections.append(conn)

    def connection_exists(self, source_id, target_id):
        return any(
            c.source_id == source_id and c.target_id == target_id
            for c in self.connections
        )

    def get_connection(self, conn_id):
        for c in self.connections:
            if c.id == conn_id:
                return c
        return None

    def set_selected(self, element_id):
        self._selected_id      = element_id
        self._selected_conn_id = None   

    def get_selected(self):
        if self._selected_id:
            return self.get_element(self._selected_id)
        return None

    def set_selected_connection(self, conn_id):
        self._selected_conn_id = conn_id
        self._selected_id      = None   

    def get_selected_connection(self):
        if self._selected_conn_id:
            return self.get_connection(self._selected_conn_id)
        return None

    def clear(self):
        self.elements.clear()
        self.connections.clear()
        self._selected_id      = None
        self._selected_conn_id = None

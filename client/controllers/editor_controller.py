"""
Контроллер редактора (MVC: Controller).

Связывает модель (FlowchartDocument) с видами (CanvasView, PropertiesPanel).
Реагирует на сигналы View и изменяет Model.

"""

from __future__ import annotations
import uuid

from client.models.elements              import FlowchartElement, ElementType
from client.models.connections           import Connection
from client.views.canvas                 import CanvasView, CanvasMode
from client.views.properties             import PropertiesPanel
from client.views.main_window            import MainWindow
from client.factories.element_factory    import TemplateFactory

# Смещение при добавлении, чтобы элемент был центрирован под курсором
_HALF_W = FlowchartElement.DEFAULT_W / 2
_HALF_H = FlowchartElement.DEFAULT_H / 2


class EditorController:


    def __init__(self, window: MainWindow) -> None:
        self.window     = window
        self.doc        = window.document
        self.canvas     = window.canvas
        self.properties = window.properties


        self._connect_signals()

    def _connect_signals(self) -> None:
        self.canvas.element_clicked.connect(self._on_element_clicked)
        self.canvas.canvas_clicked.connect(self._on_canvas_clicked)
        self.canvas.element_moved.connect(self._on_element_moved)
        self.canvas.connection_requested.connect(self._on_connection_requested)
        self.canvas.element_double_clicked.connect(self._on_double_clicked)
        self.canvas.delete_pressed.connect(self._on_delete)
        self.canvas.connection_clicked.connect(self._on_connection_clicked)

        self.properties.property_changed.connect(self._on_property_changed)

        self.window.template_requested.connect(self._on_template_requested)

    # Canvas - Controller 

    def _on_element_clicked(self, element_id: str) -> None:
        self.doc.set_selected(element_id)
        el = self.doc.get_element(element_id)
        if el:
            self.properties.show_element(el)
        self.canvas.update()
        self.window.update_status(
            f"Выбран: «{el.text}» ({el.element_type.value})" if el else ""
        )

    def _on_canvas_clicked(self, x: float, y: float) -> None:
        if self.canvas.mode == CanvasMode.ADD and self.canvas.add_type:
            el = FlowchartElement(
                element_type=self.canvas.add_type,
                x=x - _HALF_W,
                y=y - _HALF_H,
            )
            self.doc.add_element(el)
            self.doc.set_selected(el.id)
            self.properties.show_element(el)
            self.window.reset_toolbar_to_select()   # Режим SELECT + тулбар
            self.canvas.update()
            self.window.update_status(f"Добавлен: {el.element_type.value}")
            self.window.update_counter(len(self.doc.elements))
        else:
            # Клик по пустому месту снимает выделение
            self.doc.set_selected(None)
            self.properties.clear()
            self.canvas.update()

    def _on_element_moved(self, element_id: str, x: float, y: float) -> None:
        el = self.doc.get_element(element_id)
        if el:
            el.x, el.y = x, y
        self.window.update_status("Элемент перемещён")

    def _on_connection_requested(self, source_id: str, target_id: str) -> None:
        if self.doc.connection_exists(source_id, target_id):
            self.window.update_status("Соединение уже существует")
            return
        conn = Connection(source_id=source_id, target_id=target_id)
        self.doc.add_connection(conn)
        self.window.reset_toolbar_to_select()
        self.canvas.update()
        self.window.update_status("Соединение добавлено")

    def _on_double_clicked(self, element_id: str) -> None:
        # Двойной клик переход в режим редактирования текста через панель
        self._on_element_clicked(element_id)
        self.properties._text_edit.setFocus()
        self.properties._text_edit.selectAll()

    def _on_connection_clicked(self, conn_id: str) -> None:
        self.doc.set_selected_connection(conn_id)
        conn = self.doc.get_selected_connection()
        if conn:
            self.properties.show_connection(conn)
        self.canvas.update()
        self.window.update_status("Выбрано соединение")

    def _on_delete(self) -> None:
        el = self.doc.get_selected()
        if el is None:
            return
        self.doc.remove_element(el.id)
        self.properties.clear()
        self.canvas.update()
        self.window.update_status("Элемент удалён")
        self.window.update_counter(len(self.doc.elements))

    # Templates - Controller

    def _on_template_requested(self, name: str) -> None:
        factories = {
            "sequence":   TemplateFactory.create_sequence,
            "if_else":    TemplateFactory.create_if_else,
            "while_loop": TemplateFactory.create_while_loop,
            "io_process": TemplateFactory.create_io_process,
        }
        factory = factories.get(name)
        if factory is None:
            return
        elements, connections = factory()
        for el in elements:
            self.doc.add_element(el)
        for conn in connections:
            self.doc.add_connection(conn)
        self.canvas.update()
        self.window.update_counter(len(self.doc.elements))
        self.window.update_status(f"Шаблон добавлен")

    #  Properties - Controller

    def _on_property_changed(self, element_id: str, prop: str, value) -> None:
        if prop == "conn.label":
            conn = self.doc.get_connection(element_id)
            if conn:
                conn.label = value
                self.canvas.update()
            return

        el = self.doc.get_element(element_id)
        if el is None:
            return

        if prop == "text":
            el.text = value
        elif prop.startswith("style."):
            attr = prop.split(".", 1)[1]
            setattr(el.style, attr, value)
        self.canvas.update()


from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QColorDialog, QFrame, QComboBox, QStackedWidget,
)
from PyQt6.QtCore import pyqtSignal

if TYPE_CHECKING:
    from client.models.elements    import FlowchartElement
    from client.models.connections import Connection

_MODE_ELEMENT    = 0
_MODE_CONNECTION = 1


class PropertiesPanel(QWidget):
    """Боковая панель — свойства выделенного элемента или соединения."""

    property_changed = pyqtSignal(str, str, object)  # id, prop_name, value

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_id: str | None = None
        self._building = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Свойства")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #BDBDBD;")
        layout.addWidget(sep)

        # Переключатель страниц: элемент / соединение
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_element_page())   # индекс 0
        self._stack.addWidget(self._build_connection_page()) # индекс 1
        layout.addWidget(self._stack)

        layout.addStretch()

        self._set_enabled(False)

    # Страница элемента

    def _build_element_page(self) -> QWidget:
        page   = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        layout.addWidget(QLabel("Текст:"))
        self._text_edit = QLineEdit()
        self._text_edit.setPlaceholderText("Введите текст...")
        self._text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._text_edit)

        layout.addWidget(QLabel("Цвет фона:"))
        self._color_btn = QPushButton("Выбрать цвет")
        self._color_btn.clicked.connect(self._on_color_clicked)
        layout.addWidget(self._color_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #BDBDBD;")
        layout.addWidget(sep)

        layout.addWidget(QLabel("Тип соединения:"))
        self._conn_type_combo = QComboBox()
        self._conn_type_combo.addItems(["──► Со стрелкой"])
        self._conn_type_combo.setToolTip("Другие типы появятся в следующей версии")
        layout.addWidget(self._conn_type_combo)

        layout.addStretch()
        return page

    # Страница соединения 

    def _build_connection_page(self) -> QWidget:
        page   = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        lbl = QLabel("Соединение выбрано")
        lbl.setStyleSheet("color: #1976D2; font-style: italic;")
        layout.addWidget(lbl)

        layout.addWidget(QLabel("Подпись на линии:"))
        self._conn_label_edit = QLineEdit()
        self._conn_label_edit.setPlaceholderText("Например: Да / Нет / ...")
        self._conn_label_edit.textChanged.connect(self._on_conn_label_changed)
        layout.addWidget(self._conn_label_edit)

        layout.addStretch()
        return page

    # Публичный API 

    def show_element(self, element: "FlowchartElement") -> None:
        self._current_id = element.id
        self._building   = True
        self._text_edit.setText(element.text)
        self._color_btn.setStyleSheet(
            f"background: {element.style.fill_color}; color: #212121;"
        )
        self._building = False
        self._stack.setCurrentIndex(_MODE_ELEMENT)
        self._set_enabled(True)

    def show_connection(self, conn: "Connection") -> None:
        self._current_id = conn.id
        self._building   = True
        self._conn_label_edit.setText(conn.label)
        self._building   = False
        self._stack.setCurrentIndex(_MODE_CONNECTION)
        self._set_enabled(True)

    def clear(self) -> None:
        self._current_id = None
        self._set_enabled(False)

    # Внутренние слоты 

    def _set_enabled(self, enabled: bool) -> None:
        self._text_edit.setEnabled(enabled)
        self._color_btn.setEnabled(enabled)
        self._conn_label_edit.setEnabled(enabled)

    def _on_text_changed(self, text: str) -> None:
        if not self._building and self._current_id:
            self.property_changed.emit(self._current_id, "text", text)

    def _on_color_clicked(self) -> None:
        if not self._current_id:
            return
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self._color_btn.setStyleSheet(
                f"background: {color.name()}; color: #212121;"
            )
            self.property_changed.emit(
                self._current_id, "style.fill_color", color.name()
            )

    def _on_conn_label_changed(self, text: str) -> None:
        if not self._building and self._current_id:
            self.property_changed.emit(self._current_id, "conn.label", text)

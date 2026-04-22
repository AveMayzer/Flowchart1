"""
Главное окно приложения.

"""

from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QToolBar, QLabel, QStatusBar, QSplitter,
    QMessageBox, QMenuBar,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui  import QAction, QKeySequence

from client.models.elements    import ElementType
from client.models.document    import FlowchartDocument
from client.views.canvas       import CanvasView, CanvasMode
from client.views.properties   import PropertiesPanel

if TYPE_CHECKING:
    pass

# Кнопки тулбара: (текст, ElementType или None, подсказка)
_TOOLBAR_ITEMS = [
    ("↖ Выбор",     None,                   "Выделение и перемещение (S)"),
    ("⬛ Процесс",   ElementType.PROCESS,    "Добавить: прямоугольник"),
    ("◇ Условие",   ElementType.DECISION,   "Добавить: ромб"),
    ("⬭ Терм.",     ElementType.TERMINATOR, "Добавить: эллипс"),
    ("▱ Ввод/Вывод",ElementType.IO,         "Добавить: параллелограмм"),
    ("→ Связь",     "connect",              "Соединить два элемента (C)"),
]


_TEMPLATES = [
    ("Последовательность",   "sequence"),
    ("Ветвление if-else",    "if_else"),
    ("Цикл while",           "while_loop"),
    ("Ввод-Обработка-Вывод", "io_process"),
]


class MainWindow(QMainWindow):
    """Главное окно редактора блок-схем."""

    template_requested = pyqtSignal(str)   # имя шаблона → контроллер

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Редактор блок-схем (demo)")
        self.setMinimumSize(900, 600)

        self.document   = FlowchartDocument()
        self.canvas     = CanvasView(self.document)
        self.properties = PropertiesPanel()

        self._build_menubar()
        self._build_toolbar()
        self._build_central()
        self._build_statusbar()

    def _build_menubar(self) -> None:
        mb = self.menuBar()
        tmpl_menu = mb.addMenu("Шаблоны")
        for label, name in _TEMPLATES:
            act = QAction(label, self)
            act.triggered.connect(
                lambda _checked, n=name: self.template_requested.emit(n)
            )
            tmpl_menu.addAction(act)

    def _build_toolbar(self) -> None:
        tb = QToolBar("Инструменты")
        tb.setMovable(False)
        self.addToolBar(tb)

        self._mode_actions: list[QAction] = []

        for label, payload, tip in _TOOLBAR_ITEMS:
            act = QAction(label, self)
            act.setToolTip(tip)
            act.setCheckable(True)
            act.triggered.connect(
                lambda _checked, p=payload, a=act: self._activate_mode(p, a)
            )
            tb.addAction(act)
            self._mode_actions.append(act)

        tb.addSeparator()

        del_act = QAction("🗑 Удалить", self)
        del_act.setShortcut(QKeySequence.StandardKey.Delete)
        del_act.setToolTip("Удалить выбранный элемент (Delete)")
        del_act.triggered.connect(self._on_delete)
        tb.addAction(del_act)

        tb.addSeparator()

        clear_act = QAction("✕ Очистить", self)
        clear_act.setToolTip("Удалить все элементы")
        clear_act.triggered.connect(self._on_clear)
        tb.addAction(clear_act)

        # По умолчанию — режим выбора
        self._mode_actions[0].setChecked(True)

    def _build_central(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.properties)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

    def _build_statusbar(self) -> None:
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status_label = QLabel("Готово")
        sb.addWidget(self._status_label)
        self._counter_label = QLabel("Элементов: 0")
        self._counter_label.setStyleSheet("color: #757575; margin-right: 8px;")
        sb.addPermanentWidget(self._counter_label)

    def update_counter(self, count: int) -> None:
        self._counter_label.setText(f"Элементов: {count}")

    #  Слоты

    def _activate_mode(self, payload, active_action: QAction) -> None:
        """Переключить режим холста. Вызывается лямбдой каждой кнопки тулбара."""
        for act in self._mode_actions:
            act.setChecked(act is active_action)

        if payload is None:
            self.canvas.set_mode(CanvasMode.SELECT)
            self._status_label.setText("Режим: выбор")
        elif payload == "connect":
            self.canvas.set_mode(CanvasMode.CONNECT)
            self._status_label.setText("Режим: соединение — кликните источник, затем цель")
        else:
            self.canvas.set_mode(CanvasMode.ADD, add_type=payload)
            self._status_label.setText(f"Режим: добавление — {payload.value}")

    def reset_toolbar_to_select(self) -> None:
        """Сбросить тулбар на кнопку «Выбор» (вызывается контроллером)."""
        self._activate_mode(None, self._mode_actions[0])

    def _on_delete(self) -> None:
        self.canvas.delete_pressed.emit()

    def _on_clear(self) -> None:
        reply = QMessageBox.question(
            self, "Очистить?",
            "Удалить все элементы и соединения?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.document.clear()
            self.properties.clear()
            self.canvas.update()
            self._status_label.setText("Холст очищен")

    def update_status(self, text: str) -> None:
        self._status_label.setText(text)

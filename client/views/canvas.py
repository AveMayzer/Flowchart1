"""
Холст — отрисовка блок-схемы и обработка мыши.

"""

from __future__ import annotations
import math
from enum import Enum, auto
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore    import Qt, QPointF, pyqtSignal, QRectF
from PyQt6.QtGui     import (
    QPainter, QPen, QBrush, QColor, QFont,
    QMouseEvent, QKeyEvent, QPolygonF, QPainterPath,
)

from client.models.elements import FlowchartElement, ElementType

if TYPE_CHECKING:
    from client.models.document import FlowchartDocument

# Цвета холста

_BG_COLOR   = "#F7F9FC"   # фон
_GRID_COLOR = "#DDE5F0"   # сетка


class CanvasMode(Enum):
    SELECT  = auto()
    ADD     = auto()
    CONNECT = auto()


class CanvasView(QWidget):
    """Виджет холста."""

    # Сигналы → Controller
    element_clicked        = pyqtSignal(str)
    canvas_clicked         = pyqtSignal(float, float)
    element_moved          = pyqtSignal(str, float, float)
    connection_requested   = pyqtSignal(str, str)
    connection_clicked     = pyqtSignal(str)   # ID соединения
    element_double_clicked = pyqtSignal(str)
    delete_pressed         = pyqtSignal()

    def __init__(self, document: "FlowchartDocument", parent=None) -> None:
        super().__init__(parent)
        self.doc  = document
        self.mode = CanvasMode.SELECT
        self.add_type: ElementType | None = None

        self._dragging      = False
        self._drag_id:       str | None    = None
        self._drag_start:    QPointF | None = None
        self._drag_el_start: tuple[float, float] = (0.0, 0.0)

        self._connecting     = False
        self._connect_src:   str | None    = None
        self._connect_mouse: QPointF | None = None

        self._hover_id: str | None = None

        self.setMinimumSize(700, 500)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # Отрисовка 

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Фон 
        painter.fillRect(self.rect(), QColor(_BG_COLOR))

        self._draw_grid(painter)

        for conn in self.doc.connections:
            self._draw_connection(painter, conn)

        # Временная линия при создании соединения
        if self._connecting and self._connect_src and self._connect_mouse:
            src = self.doc.get_element(self._connect_src)
            if src:
                sx, sy = src.get_center()
                sp = QPointF(sx, sy)
                pen = QPen(QColor("#1976D2"), 2, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawLine(sp, self._connect_mouse)
                painter.setBrush(QBrush(QColor("#1976D2")))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(sp, 5, 5)

        for el in self.doc.elements:
            self._draw_element(painter, el)

        painter.end()

    def _draw_grid(self, painter: QPainter) -> None:
        grid = 30
        painter.setPen(QPen(QColor(_GRID_COLOR), 1))
        w, h = self.width(), self.height()
        for x in range(0, w, grid):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, grid):
            painter.drawLine(0, y, w, y)

    def _draw_element(self, painter: QPainter, el: FlowchartElement) -> None:
        selected = (self.doc.get_selected() is not None
                    and self.doc.get_selected().id == el.id)
        hovered  = self._hover_id == el.id

        fill   = QColor(el.style.fill_color)
        border = QColor(el.style.border_color)
        if selected:
            border = QColor("#E73936")
        elif hovered:
            border = QColor("#1976D2")

        bw  = el.style.border_width + (1 if selected else 0)
        painter.setPen(QPen(border, bw))
        painter.setBrush(QBrush(fill))

        x, y, w, h = el.x, el.y, el.width, el.height
        cx, cy = el.get_center()

        if el.element_type == ElementType.PROCESS:
            painter.drawRoundedRect(QRectF(x, y, w, h), 4, 4)

        elif el.element_type == ElementType.DECISION:
            painter.drawPolygon(QPolygonF([
                QPointF(cx, y), QPointF(x + w, cy),
                QPointF(cx, y + h), QPointF(x, cy),
            ]))

        elif el.element_type == ElementType.TERMINATOR:
            painter.drawEllipse(QRectF(x, y, w, h))

        elif el.element_type == ElementType.IO:
            off = 20
            painter.drawPolygon(QPolygonF([
                QPointF(x + off, y), QPointF(x + w, y),
                QPointF(x + w - off, y + h), QPointF(x, y + h),
            ]))

        painter.setPen(QColor(el.style.text_color))
        painter.setFont(QFont("Arial", el.style.font_size))
        painter.drawText(QRectF(x, y, w, h), Qt.AlignmentFlag.AlignCenter, el.text)

    def _draw_connection(self, painter: QPainter, conn) -> None:
        src = self.doc.get_element(conn.source_id)
        tgt = self.doc.get_element(conn.target_id)
        if src is None or tgt is None:
            return

        tcx, tcy = tgt.get_center()
        scx, scy = src.get_center()
        sp = self._element_edge_point(QPointF(tcx, tcy), src)
        tp = self._element_edge_point(QPointF(scx, scy), tgt)

        selected_conn = self.doc.get_selected_connection()
        is_selected   = selected_conn is not None and selected_conn.id == conn.id

        painter.save()
        color = QColor("#E93225") if is_selected else QColor(conn.color)
        pen   = QPen(color, 3 if is_selected else 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(sp, tp)

        self._draw_arrowhead(painter, sp, tp, color)

        if conn.label:
            mid = QPointF((sp.x() + tp.x()) / 2, (sp.y() + tp.y()) / 2)
            painter.setPen(color)
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold if is_selected else QFont.Weight.Normal))
            painter.drawText(mid + QPointF(4, -4), conn.label)

        painter.restore()

    @staticmethod
    def _element_edge_point(from_pt: QPointF, el: FlowchartElement) -> QPointF:
        """Точка выхода линии из центра el в направлении from_pt — на краю bbox."""
        cx, cy = el.get_center()
        dx = cx - from_pt.x()
        dy = cy - from_pt.y()
        if abs(dx) < 0.001 and abs(dy) < 0.001:
            return QPointF(cx, cy)

        hw, hh = el.width / 2, el.height / 2
        t_min = float("inf")

        if abs(dx) > 0.001:
            for ex in (cx - hw, cx + hw):
                t = (ex - from_pt.x()) / dx
                if t > 0:
                    y_t = from_pt.y() + t * dy
                    if cy - hh <= y_t <= cy + hh:
                        t_min = min(t_min, t)

        if abs(dy) > 0.001:
            for ey in (cy - hh, cy + hh):
                t = (ey - from_pt.y()) / dy
                if t > 0:
                    x_t = from_pt.x() + t * dx
                    if cx - hw <= x_t <= cx + hw:
                        t_min = min(t_min, t)

        if t_min == float("inf"):
            return QPointF(cx, cy)
        return QPointF(from_pt.x() + t_min * dx, from_pt.y() + t_min * dy)

    @staticmethod
    def _draw_arrowhead(painter: QPainter, start: QPointF,
                        end: QPointF, color: QColor) -> None:
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1:
            return
        ux, uy = dx / length, dy / length
        size = 12
        p1 = QPointF(end.x() - size * ux + size * 0.4 * uy,
                     end.y() - size * uy - size * 0.4 * ux)
        p2 = QPointF(end.x() - size * ux - size * 0.4 * uy,
                     end.y() - size * uy + size * 0.4 * ux)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(QPolygonF([end, p1, p2]))

    #  Клавиатура 

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete:
            self.delete_pressed.emit()
        else:
            super().keyPressEvent(event)

    # Мышь 

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus()
        if event.button() != Qt.MouseButton.LeftButton:
            return

        mx, my = event.position().x(), event.position().y()

        if self.mode == CanvasMode.SELECT:
            el = self.doc.element_at_position(mx, my)
            if el:
                self.element_clicked.emit(el.id)
                self._dragging      = True
                self._drag_id       = el.id
                self._drag_start    = QPointF(event.position())
                self._drag_el_start = (el.x, el.y)
            else:
                conn = self._connection_at_position(mx, my)
                if conn:
                    self.connection_clicked.emit(conn.id)
                else:
                    self.canvas_clicked.emit(mx, my)

        elif self.mode == CanvasMode.ADD:
            self.canvas_clicked.emit(mx, my)

        elif self.mode == CanvasMode.CONNECT:
            el = self.doc.element_at_position(mx, my)
            if el:
                self._connecting    = True
                self._connect_src   = el.id
                self._connect_mouse = QPointF(event.position())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        mx, my = event.position().x(), event.position().y()

        if self._dragging and self._drag_id and self._drag_start:
            delta = QPointF(event.position()) - self._drag_start
            new_x = self._drag_el_start[0] + delta.x()
            new_y = self._drag_el_start[1] + delta.y()
            el = self.doc.get_element(self._drag_id)
            if el:
                el.x, el.y = new_x, new_y
                self.update()
            return

        if self._connecting:
            self._connect_mouse = QPointF(event.position())
            self.update()
            return

        el = self.doc.element_at_position(mx, my)
        new_hover = el.id if el else None
        if new_hover != self._hover_id:
            self._hover_id = new_hover
            self.update()
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if new_hover
            else Qt.CursorShape.ArrowCursor
        )

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return

        if self._dragging and self._drag_id:
            el = self.doc.get_element(self._drag_id)
            if el:
                self.element_moved.emit(self._drag_id, el.x, el.y)
            self._dragging = False
            self._drag_id  = None

        if self._connecting and self._connect_src:
            mx, my = event.position().x(), event.position().y()
            tgt = self.doc.element_at_position(mx, my)
            if tgt and tgt.id != self._connect_src:
                self.connection_requested.emit(self._connect_src, tgt.id)
            self._connecting    = False
            self._connect_src   = None
            self._connect_mouse = None
            self.update()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        mx, my = event.position().x(), event.position().y()
        el = self.doc.element_at_position(mx, my)
        if el:
            self.element_double_clicked.emit(el.id)

    def _connection_at_position(self, mx: float, my: float):
        """Возвращает соединение, на которое кликнул пользователь (или None)."""
        threshold = 7
        for conn in self.doc.connections:
            src = self.doc.get_element(conn.source_id)
            tgt = self.doc.get_element(conn.target_id)
            if not src or not tgt:
                continue
            tcx, tcy = tgt.get_center()
            scx, scy = src.get_center()
            sp = self._element_edge_point(QPointF(tcx, tcy), src)
            tp = self._element_edge_point(QPointF(scx, scy), tgt)
            if self._point_segment_dist(mx, my, sp, tp) < threshold:
                return conn
        return None

    @staticmethod
    def _point_segment_dist(px: float, py: float,
                            a: QPointF, b: QPointF) -> float:
        """Расстояние от точки (px, py) до отрезка [a, b]."""
        ax, ay = a.x(), a.y()
        dx, dy = b.x() - ax, b.y() - ay
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq < 1e-6:
            return math.sqrt((px - ax) ** 2 + (py - ay) ** 2)
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg_len_sq))
        cx, cy = ax + t * dx, ay + t * dy
        return math.sqrt((px - cx) ** 2 + (py - cy) ** 2)

    def set_mode(self, mode: CanvasMode, add_type: ElementType | None = None) -> None:
        self.mode     = mode
        self.add_type = add_type
        cursors = {
            CanvasMode.SELECT:  Qt.CursorShape.ArrowCursor,
            CanvasMode.ADD:     Qt.CursorShape.PointingHandCursor,
            CanvasMode.CONNECT: Qt.CursorShape.CrossCursor,
        }
        self.setCursor(cursors.get(mode, Qt.CursorShape.ArrowCursor))

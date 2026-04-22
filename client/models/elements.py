from __future__ import annotations
import uuid
from dataclasses import dataclass
from enum import Enum 


class ElementType(Enum):
    PROCESS    = "Процесс"
    DECISION   = "Условие"
    TERMINATOR = "Терминатор"
    IO         = "Ввод/Вывод"


@dataclass
class ElementStyle:
    fill_color:   str = "#BBDEFB"
    border_color: str = "#1565C0"
    text_color:   str = "#212121"
    border_width: int = 2
    font_size:    int = 11


class FlowchartElement:
    DEFAULT_W = 140
    DEFAULT_H = 60

    def __init__(self, element_type, x=0, y=0, text="", width=DEFAULT_W, height=DEFAULT_H, element_id=None):
        self.id           = element_id or str(uuid.uuid4())
        self.element_type = element_type
        self.x            = x
        self.y            = y
        self.width        = width
        self.height       = height
        self.text         = text or element_type.value.capitalize()
        self.style        = ElementStyle()

    def get_center(self):
        return self.x + self.width / 2, self.y + self.height / 2

    def contains_point(self, px, py):
        return self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height

    def to_dict(self):
        return {
            "id":           self.id,
            "type":         self.element_type.value,
            "x":            self.x,
            "y":            self.y,
            "width":        self.width,
            "height":       self.height,
            "text":         self.text,
            "fill_color":   self.style.fill_color,
            "border_color": self.style.border_color,
        }

    @classmethod
    def from_dict(cls, data):
        el = cls(
            element_type=ElementType(data["type"]),
            x=data.get("x", 0),
            y=data.get("y", 0),
            text=data.get("text", ""),
            width=data.get("width", cls.DEFAULT_W),
            height=data.get("height", cls.DEFAULT_H),
            element_id=data.get("id"),
        )
        el.style.fill_color   = data.get("fill_color",   el.style.fill_color)
        el.style.border_color = data.get("border_color", el.style.border_color)
        return el

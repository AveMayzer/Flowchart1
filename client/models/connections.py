from __future__ import annotations
import uuid
from dataclasses import dataclass, field


@dataclass
class Connection:
    source_id: str
    target_id: str
    label:     str = ""
    color:     str = "#455A64"
    id:        str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self):
        return {
            "id":        self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "label":     self.label,
            "color":     self.color,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            label=data.get("label", ""),
            color=data.get("color", "#555555"),
            id=data.get("id", str(uuid.uuid4())),
        )

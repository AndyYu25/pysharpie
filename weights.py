"""Port of calc/weights.rs — MiscWgts."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MiscWgts:
    vital: int = 0
    hull: int = 0
    on: int = 0
    above: int = 0
    void: int = 0

    def wgt(self) -> int:
        return self.vital + self.hull + self.on + self.above + self.void

    @classmethod
    def from_dict(cls, data: dict) -> "MiscWgts":
        """Parse a .ship wgts object."""
        return cls(
            vital=int(data.get("vital", 0)),
            hull=int(data.get("hull", 0)),
            on=int(data.get("on", 0)),
            above=int(data.get("above", 0)),
            void=int(data.get("void", 0)),
        )

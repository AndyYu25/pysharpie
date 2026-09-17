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

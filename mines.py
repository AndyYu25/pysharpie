"""Port of calc/mines.rs — Mines, MineType (calc core only)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .units import Measurement, Units, UnitType
from .utils import POUND2TON


def _mw(v: float) -> Measurement:
    return Measurement(v, UnitType.WEIGHT, Units.IMPERIAL)


class MineType(Enum):
    STERN_RAILS = "SternRails"
    BOW_TUBES = "BowTubes"
    STERN_TUBES = "SternTubes"
    SIDE_TUBES = "SideTubes"

    @classmethod
    def default(cls) -> "MineType":
        return cls.STERN_RAILS

    def label(self) -> str:
        return {
            MineType.STERN_RAILS: "Above water - Stern racks/rails",
            MineType.BOW_TUBES: "Below water - bow tubes",
            MineType.STERN_TUBES: "Below water - stern tubes",
            MineType.SIDE_TUBES: "Below water - side tubes",
        }[self]

    def __str__(self) -> str:
        return self.label()

    def index(self) -> int:
        return MineType.ALL().index(self)

    @classmethod
    def ALL(cls) -> list["MineType"]:
        return [cls.STERN_RAILS, cls.BOW_TUBES, cls.STERN_TUBES, cls.SIDE_TUBES]

    @classmethod
    def all_labels(cls) -> list[str]:
        return [v.label() for v in cls.ALL()]

    @classmethod
    def from_index(cls, index: int) -> "MineType":
        all_v = cls.ALL()
        return all_v[index] if 0 <= index < len(all_v) else cls.default()

    @classmethod
    def from_str(cls, index: str) -> "MineType":
        try:
            return cls.from_index(int(str(index).strip()))
        except (ValueError, AttributeError):
            return cls.default()

    @classmethod
    def from_name(cls, name: str) -> "MineType":
        from .utils import enum_from_name

        return enum_from_name(cls, name, cls.default())

    def wgt_factor(self) -> float:
        return 0.25 if self is MineType.STERN_RAILS else 1.0


@dataclass
class Mines:
    units: Units = Units.IMPERIAL
    year: int = 0
    num: int = 0
    reload: int = 0
    wgt: Measurement = field(default_factory=lambda: _mw(0.0))
    kind: MineType = MineType.STERN_RAILS

    def wgt_all(self) -> float:
        return self.wgt_weaps() + self.wgt_mounts()

    def wgt_weaps(self) -> float:
        return float(self.num + self.reload) * self.wgt.imp() / POUND2TON

    def wgt_mounts(self) -> float:
        return self.wgt_weaps() * self.kind.wgt_factor()

    @classmethod
    def from_dict(cls, data: dict) -> "Mines":
        """Parse a .ship mines object."""
        from .units import Units as _Units

        return cls(
            units=_Units.from_name(data.get("units", "")),
            year=int(data.get("year", 0)),
            num=int(data.get("num", 0)),
            reload=int(data.get("reload", 0)),
            wgt=Measurement.from_dict(data.get("wgt") or {"v": 0.0}, UnitType.WEIGHT),
            kind=MineType.from_name(data.get("kind", "SternRails")),
        )

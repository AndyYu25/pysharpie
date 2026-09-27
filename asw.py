"""Port of calc/asw.rs — ASW, ASWType (calc core only)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .units import Measurement, Units, UnitType
from .utils import POUND2TON


def _mw(v: float) -> Measurement:
    return Measurement(v, UnitType.WEIGHT, Units.IMPERIAL)


class ASWType(Enum):
    STERN_RACKS = "SternRacks"
    THROWERS = "Throwers"
    HEDGEHOGS = "Hedgehogs"
    SQUID_MORTARS = "SquidMortars"

    @classmethod
    def default(cls) -> "ASWType":
        return cls.STERN_RACKS

    def label(self) -> str:
        return {
            ASWType.STERN_RACKS: "Stern depth charge racks",
            ASWType.THROWERS: "Depth charge throwers",
            ASWType.HEDGEHOGS: "Hedgehog style A/S mortars",
            ASWType.SQUID_MORTARS: "Squid style A/S mortars",
        }[self]

    def __str__(self) -> str:
        return self.label()

    def index(self) -> int:
        return ASWType.ALL().index(self)

    @classmethod
    def ALL(cls) -> list["ASWType"]:
        return [cls.STERN_RACKS, cls.THROWERS, cls.HEDGEHOGS, cls.SQUID_MORTARS]

    @classmethod
    def all_labels(cls) -> list[str]:
        return [v.label() for v in cls.ALL()]

    @classmethod
    def from_index(cls, index: int) -> "ASWType":
        all_v = cls.ALL()
        return all_v[index] if 0 <= index < len(all_v) else cls.default()

    @classmethod
    def from_str(cls, index: str) -> "ASWType":
        try:
            return cls.from_index(int(str(index).strip()))
        except (ValueError, AttributeError):
            return cls.default()

    @classmethod
    def from_name(cls, name: str) -> "ASWType":
        from .utils import enum_from_name

        return enum_from_name(cls, name, cls.default())

    def mount_wgt_factor(self) -> float:
        return {
            ASWType.STERN_RACKS: 0.25,
            ASWType.THROWERS: 0.5,
            ASWType.HEDGEHOGS: 0.5,
            ASWType.SQUID_MORTARS: 10.0,
        }[self]


@dataclass
class ASW:
    units: Units = Units.IMPERIAL
    year: int = 0
    num: int = 0
    reload: int = 0
    wgt: Measurement = field(default_factory=lambda: _mw(0.0))
    kind: ASWType = ASWType.STERN_RACKS

    def wgt_all(self) -> float:
        return self.wgt_weaps() + self.wgt_mounts()

    def wgt_weaps(self) -> float:
        return float(self.num + self.reload) * self.wgt.imp() / POUND2TON

    def wgt_mounts(self) -> float:
        return self.wgt_weaps() * self.kind.mount_wgt_factor()

    @classmethod
    def from_dict(cls, data: dict) -> "ASW":
        """Parse a .ship ASW object."""
        from .units import Units as _Units

        return cls(
            units=_Units.from_name(data.get("units", "")),
            year=int(data.get("year", 0)),
            num=int(data.get("num", 0)),
            reload=int(data.get("reload", 0)),
            wgt=Measurement.from_dict(data.get("wgt") or {"v": 0.0}, UnitType.WEIGHT),
            kind=ASWType.from_name(data.get("kind", "SternRacks")),
        )

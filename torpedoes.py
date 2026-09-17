"""Port of calc/torpedoes.rs — Torpedoes, TorpedoMountType (calc core only)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from .units import Measurement, Units, UnitType

_PI = math.pi


def _ms(v: float) -> Measurement:
    return Measurement(v, UnitType.LENGTH_SMALL, Units.IMPERIAL)


def _ml(v: float) -> Measurement:
    return Measurement(v, UnitType.LENGTH_LONG, Units.IMPERIAL)


class TorpedoMountType(Enum):
    FIXED_TUBES = "FixedTubes"
    DECK_SIDE_TUBES = "DeckSideTubes"
    CENTER_TUBES = "CenterTubes"
    DECK_RELOADS = "DeckReloads"
    BOW_TUBES = "BowTubes"
    STERN_TUBES = "SternTubes"
    BOW_AND_STERN_TUBES = "BowAndSternTubes"
    SUBMERGED_SIDE_TUBES = "SubmergedSideTubes"
    SUBMERGED_RELOADS = "SubmergedReloads"

    @classmethod
    def default(cls) -> "TorpedoMountType":
        return cls.FIXED_TUBES

    def label(self) -> str:
        return {
            TorpedoMountType.FIXED_TUBES: "deck mounted carriage/fixed tube",
            TorpedoMountType.DECK_SIDE_TUBES: "deck mounted side rotating tube",
            TorpedoMountType.CENTER_TUBES: "deck mounted centre rotating tube",
            TorpedoMountType.DECK_RELOADS: "deck mounted reload",
            TorpedoMountType.BOW_TUBES: "submerged bow tube",
            TorpedoMountType.STERN_TUBES: "submerged stern tube",
            TorpedoMountType.BOW_AND_STERN_TUBES: "submerged bow & stern tube",
            TorpedoMountType.SUBMERGED_SIDE_TUBES: "submerged side tube",
            TorpedoMountType.SUBMERGED_RELOADS: "below water reload",
        }[self]

    def __str__(self) -> str:
        return self.label()

    def index(self) -> int:
        return TorpedoMountType.ALL().index(self)

    @classmethod
    def ALL(cls) -> list["TorpedoMountType"]:
        return [
            cls.FIXED_TUBES,
            cls.DECK_SIDE_TUBES,
            cls.CENTER_TUBES,
            cls.DECK_RELOADS,
            cls.BOW_TUBES,
            cls.STERN_TUBES,
            cls.BOW_AND_STERN_TUBES,
            cls.SUBMERGED_SIDE_TUBES,
            cls.SUBMERGED_RELOADS,
        ]

    @classmethod
    def all_labels(cls) -> list[str]:
        return [v.label() for v in cls.ALL()]

    @classmethod
    def from_index(cls, index: int) -> "TorpedoMountType":
        all_v = cls.ALL()
        return all_v[index] if 0 <= index < len(all_v) else cls.default()

    @classmethod
    def from_str(cls, index: str) -> "TorpedoMountType":
        try:
            return cls.from_index(int(str(index).strip()))
        except (ValueError, AttributeError):
            return cls.default()

    def wgt_factor(self) -> float:
        if self in (TorpedoMountType.FIXED_TUBES, TorpedoMountType.DECK_RELOADS, TorpedoMountType.SUBMERGED_RELOADS):
            return 0.25
        return 1.0

    def hull_space(self, length: float, diam: float) -> float:
        if self in (
            TorpedoMountType.FIXED_TUBES,
            TorpedoMountType.DECK_SIDE_TUBES,
            TorpedoMountType.CENTER_TUBES,
            TorpedoMountType.DECK_RELOADS,
        ):
            return 0.0
        if self is TorpedoMountType.SUBMERGED_RELOADS:
            return length * 1.5 * (diam * 1.5 / 12.0) ** 2.0
        return length * 2.5 * (diam * 2.75 / 12.0) ** 2.0

    def deck_space(self, b: float, num: int, length: float, diam: float, mounts: int) -> float:
        if mounts == 0:
            return 0.0
        n = float(num)
        m = float(mounts)
        if self is TorpedoMountType.FIXED_TUBES:
            return length * diam / 12.0 * n
        if self is TorpedoMountType.DECK_SIDE_TUBES:
            return (
                ((length**2.0 + (((n / m) * diam / 12.0) + (n / m - 1.0) * 0.5) ** 2.0) ** 0.5 * 0.5) ** 2.0
            ) * _PI + (((n / m) * diam / 12.0) + (n / m - 1.0) * 0.5) * 0.5 * length
        if self is TorpedoMountType.CENTER_TUBES:
            x = length**2.0
            y = ((n / m) * diam / 12.0 + (n / m - 1.0) * 0.5) ** 2.0
            return math.sqrt(x + y) * b * m
        if self is TorpedoMountType.DECK_RELOADS:
            return length * 1.5 * (diam + 6.0) / 12.0 * n
        return 0.0


@dataclass
class Torpedoes:
    units: Units = Units.IMPERIAL
    year: int = 0
    mounts: int = 0
    kind: TorpedoMountType = TorpedoMountType.FIXED_TUBES
    num: int = 0
    diam: Measurement = field(default_factory=lambda: _ms(0.0))
    len: Measurement = field(default_factory=lambda: _ml(0.0))

    def wgt(self) -> float:
        return self.wgt_weaps() + self.wgt_mounts()

    def wgt_weaps(self) -> float:
        divisor = (max(1907.0 - float(self.year), 0.0) + 25.0) * 937.0
        if divisor == 0.0:
            return 0.0
        return (
            _PI * self.diam.imp() ** 2.0 * self.len.imp() / divisor
            + (float(self.year) - 1890.0) * 0.004
        ) * float(self.num)

    def wgt_mounts(self) -> float:
        return self.kind.wgt_factor() * self.wgt_weaps()

    def hull_space(self) -> float:
        return self.kind.hull_space(self.len.imp(), self.diam.imp()) * float(self.num)

    def deck_space(self, b: float) -> float:
        return self.kind.deck_space(b, self.num, self.len.imp(), self.diam.imp(), self.mounts)

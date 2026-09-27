"""Port of calc/armor.rs — Armor, Belt, CT, Deck (+ enums)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar

from .units import Measurement, Units, UnitType


def _ms(v: float) -> Measurement:
    return Measurement(v, UnitType.LENGTH_SMALL, Units.IMPERIAL)


def _ml(v: float) -> Measurement:
    return Measurement(v, UnitType.LENGTH_LONG, Units.IMPERIAL)


class BulkheadType(Enum):
    ADDITIONAL = "Additional"
    STRENGTHENED = "Strengthened"

    @classmethod
    def default(cls) -> "BulkheadType":
        return cls.ADDITIONAL

    def label(self) -> str:
        return {
            BulkheadType.ADDITIONAL: "Additional bulkheads",
            BulkheadType.STRENGTHENED: "Strengthened bulkheads",
        }[self]

    def __str__(self) -> str:
        return {
            BulkheadType.ADDITIONAL: "Additional damage containing bulkheads",
            BulkheadType.STRENGTHENED: "Strengthened structural bulkheads",
        }[self]

    def index(self) -> int:
        return BulkheadType.ALL().index(self)

    @classmethod
    def ALL(cls) -> list["BulkheadType"]:
        return [cls.ADDITIONAL, cls.STRENGTHENED]

    @classmethod
    def all_labels(cls) -> list[str]:
        return [v.label() for v in cls.ALL()]

    @classmethod
    def from_index(cls, index: int) -> "BulkheadType":
        all_v = cls.ALL()
        return all_v[index] if 0 <= index < len(all_v) else cls.default()

    @classmethod
    def from_str(cls, index: str) -> "BulkheadType":
        try:
            return cls.from_index(int(str(index).strip()))
        except (ValueError, AttributeError):
            return cls.default()

    @classmethod
    def from_name(cls, name: str) -> "BulkheadType":
        from .utils import enum_from_name

        return enum_from_name(cls, name, cls.default())


class BeltType(Enum):
    MAIN = "Main"
    END = "End"
    UPPER = "Upper"
    BULGE = "Bulge"
    BULKHEAD = "Bulkhead"

    @classmethod
    def from_name(cls, name: str) -> "BeltType":
        from .utils import enum_from_name

        return enum_from_name(cls, name, cls.MAIN)


class DeckType(Enum):
    MULTIPLE_ARMORED = "MultipleArmored"
    SINGLE_ARMORED = "SingleArmored"
    MULTIPLE_PROTECTED = "MultipleProtected"
    SINGLE_PROTECTED = "SingleProtected"
    BOX_OVER_MACHINERY = "BoxOverMachinery"
    BOX_OVER_MAGAZINE = "BoxOverMagazine"
    BOX_OVER_BOTH = "BoxOverBoth"

    @classmethod
    def default(cls) -> "DeckType":
        return cls.MULTIPLE_ARMORED

    def label(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return {
            DeckType.MULTIPLE_ARMORED: "Armoured deck - multiple decks",
            DeckType.SINGLE_ARMORED: "Armoured deck - single deck",
            DeckType.MULTIPLE_PROTECTED: "Protected deck - multiple decks",
            DeckType.SINGLE_PROTECTED: "Protected deck - single deck",
            DeckType.BOX_OVER_MACHINERY: "Box over machinery",
            DeckType.BOX_OVER_MAGAZINE: "Box over magazines",
            DeckType.BOX_OVER_BOTH: "Box over machinery & magazines",
        }[self]

    def index(self) -> int:
        return DeckType.ALL().index(self)

    @classmethod
    def ALL(cls) -> list["DeckType"]:
        return [
            cls.MULTIPLE_ARMORED,
            cls.SINGLE_ARMORED,
            cls.MULTIPLE_PROTECTED,
            cls.SINGLE_PROTECTED,
            cls.BOX_OVER_MACHINERY,
            cls.BOX_OVER_MAGAZINE,
            cls.BOX_OVER_BOTH,
        ]

    @classmethod
    def all_labels(cls) -> list[str]:
        return [v.label() for v in cls.ALL()]

    @classmethod
    def from_index(cls, index: int) -> "DeckType":
        all_v = cls.ALL()
        return all_v[index] if 0 <= index < len(all_v) else cls.default()

    @classmethod
    def from_str(cls, index: str) -> "DeckType":
        try:
            return cls.from_index(int(str(index).strip()))
        except (ValueError, AttributeError):
            return cls.default()

    @classmethod
    def from_name(cls, name: str) -> "DeckType":
        from .utils import enum_from_name

        return enum_from_name(cls, name, cls.default())

    def wgt_factor(
        self,
        d: float,
        lwl: float,
        b: float,
        fc_len: float,
        qd_len: float,
        wp: float,
        cwp: float,
        wgt_engine: float,
        wgt_mag: float,
    ) -> float:
        if d == 0.0:
            return 0.0
        if self in (
            DeckType.MULTIPLE_ARMORED,
            DeckType.SINGLE_ARMORED,
            DeckType.MULTIPLE_PROTECTED,
            DeckType.SINGLE_PROTECTED,
        ):
            return (
                wp
                - (fc_len * 2.0) ** (1.0 - cwp**2.0) * b * lwl * fc_len / 2.0
                - (
                    qd_len ** (1.0 - cwp) * b * lwl * qd_len * 0.25
                    + (
                        qd_len ** (1.0 - cwp)
                        + (qd_len * 2.0) ** (1.0 - cwp)
                    )
                    * b
                    * lwl
                    * qd_len
                    * 0.25
                )
            ) * 1.01
        if self is DeckType.BOX_OVER_MACHINERY:
            return (wgt_engine * 3.0 / (d * 0.94) * 0.65 * lwl + 16.0) * (b + 16.0) - 256.0
        if self is DeckType.BOX_OVER_MAGAZINE:
            return (wgt_mag / (d * 0.94) * 0.65 * lwl + 16.0) * (b + 16.0) - 256.0
        # BoxOverBoth
        return ((wgt_engine * 3.0 + wgt_mag) / (d * 0.94) * 0.65 * lwl + 16.0) * (b + 16.0) - 256.0


@dataclass
class Belt:
    thick: Measurement = field(default_factory=lambda: _ms(0.0))
    len: Measurement = field(default_factory=lambda: _ml(0.0))
    hgt: Measurement = field(default_factory=lambda: _ml(0.0))
    kind: BeltType = BeltType.MAIN

    @classmethod
    def new(cls, kind: BeltType) -> "Belt":
        return cls(thick=_ms(0.0), len=_ml(0.0), hgt=_ml(0.0), kind=kind)

    @classmethod
    def from_dict(cls, data: dict) -> "Belt":
        """Parse a .ship belt object."""
        kind = BeltType.from_name(data.get("kind", "Main"))
        return cls(
            thick=Measurement.from_dict(data.get("thick") or {"v": 0.0}, UnitType.LENGTH_SMALL),
            len=Measurement.from_dict(data.get("len") or {"v": 0.0}, UnitType.LENGTH_LONG),
            hgt=Measurement.from_dict(data.get("hgt") or {"v": 0.0}, UnitType.LENGTH_LONG),
            kind=kind,
        )

    def wgt(self, lwl: float, cwp: float, b: float) -> float:
        length = self.len.imp()
        hgt = self.hgt.imp()
        thick = self.thick.imp()
        if lwl == 0.0:
            return 0.0
        if self.kind in (BeltType.MAIN, BeltType.UPPER):
            beam_bulkhead = (1.0 - length / lwl) ** (1.0 - cwp) * b
        else:
            beam_bulkhead = 0.0
        return (length + beam_bulkhead) * hgt * thick * Armor.INCH * 2.0


@dataclass
class CT:
    thick: Measurement = field(default_factory=lambda: _ms(0.0))

    def wgt(self, d: float) -> float:
        return 10.0 * (d / 10_000.0) ** (2.0 / 3.0) * self.thick.imp()

    @classmethod
    def from_dict(cls, data: dict) -> "CT":
        """Parse a .ship `{"thick": {...}}` conning tower object."""
        return cls(
            thick=Measurement.from_dict(data.get("thick") or {"v": 0.0}, UnitType.LENGTH_SMALL)
        )


@dataclass
class Deck:
    fc: Measurement = field(default_factory=lambda: _ms(0.0))
    md: Measurement = field(default_factory=lambda: _ms(0.0))
    qd: Measurement = field(default_factory=lambda: _ms(0.0))
    kind: DeckType = DeckType.MULTIPLE_ARMORED

    def wgt(self, hull, wgt_mag: float, wgt_engine: float) -> float:
        d = hull.d()
        lwl = hull.lwl().imp()
        b = hull.b.imp()
        fc_len = hull.freeboard.fc_len
        qd_len = hull.freeboard.qd_len
        cwp = hull.cwp()
        wp = hull.wp().imp()
        main_deck = self.kind.wgt_factor(d, lwl, b, fc_len, qd_len, wp, cwp, wgt_engine, wgt_mag)
        fc_deck = (fc_len * 2.0) ** (1.0 - cwp**2.0) * b * lwl * fc_len * 0.5
        qd_deck = qd_len ** (1.0 - cwp) * b * lwl * qd_len / 4.0 * (2.0 + 2.0 ** (1.0 - cwp))
        return (main_deck * self.md.imp() + fc_deck * self.fc.imp() + qd_deck * self.qd.imp()) * Armor.INCH

    @classmethod
    def from_dict(cls, data: dict) -> "Deck":
        """Parse a .ship deck object."""
        ms = UnitType.LENGTH_SMALL
        return cls(
            fc=Measurement.from_dict(data.get("fc") or {"v": 0.0}, ms),
            md=Measurement.from_dict(data.get("md") or {"v": 0.0}, ms),
            qd=Measurement.from_dict(data.get("qd") or {"v": 0.0}, ms),
            kind=DeckType.from_name(data.get("kind", "MultipleArmored")),
        )


@dataclass
class Armor:
    units: Units = Units.IMPERIAL
    main: Belt = field(default_factory=lambda: Belt.new(BeltType.MAIN))
    end: Belt = field(default_factory=lambda: Belt.new(BeltType.END))
    upper: Belt = field(default_factory=lambda: Belt.new(BeltType.UPPER))
    incline: float = 0.0
    bulge: Belt = field(default_factory=lambda: Belt.new(BeltType.BULGE))
    bulkhead: Belt = field(default_factory=lambda: Belt.new(BeltType.BULKHEAD))
    bh_kind: BulkheadType = BulkheadType.ADDITIONAL
    bh_beam: Measurement = field(default_factory=lambda: _ml(0.0))
    deck: Deck = field(default_factory=Deck)
    ct_fwd: CT = field(default_factory=CT)
    ct_aft: CT = field(default_factory=CT)

    INCH: ClassVar[float] = 0.0185

    def wgt(self, hull, wgt_mag: float, wgt_engine: float) -> float:
        lwl = hull.lwl().imp()
        cwp = hull.cwp()
        b = hull.b.imp()
        d = hull.d()
        return (
            self.main.wgt(lwl, cwp, b)
            + self.end.wgt(lwl, cwp, b)
            + self.upper.wgt(lwl, cwp, b)
            + self.bulge.wgt(lwl, cwp, b)
            + self.bulkhead.wgt(lwl, cwp, b)
            + self.deck.wgt(hull, wgt_mag, wgt_engine)
            + self.ct_fwd.wgt(d)
            + self.ct_aft.wgt(d)
        )

    def belt_coverage(self, lwl: float) -> float:
        if lwl == 0.0:
            return 0.0
        return self.main.len.imp() / (lwl * 0.65)

    def max_belt_hgt(self, t: float, dist: float) -> float:
        radians = self.incline * math.pi / 180.0
        if abs(math.cos(radians)) == 0.0:
            return 0.0
        return (t + dist) * (1.0 / abs(math.cos(radians))) + 0.02

    @classmethod
    def from_dict(cls, data: dict) -> "Armor":
        """Parse a .ship armor object."""
        from .units import Units as _Units

        return cls(
            units=_Units.from_name(data.get("units", "")),
            main=Belt.from_dict(data.get("main") or {}),
            end=Belt.from_dict(data.get("end") or {"kind": "End"}),
            upper=Belt.from_dict(data.get("upper") or {"kind": "Upper"}),
            incline=float(data.get("incline", 0.0)),
            bulge=Belt.from_dict(data.get("bulge") or {"kind": "Bulge"}),
            bulkhead=Belt.from_dict(data.get("bulkhead") or {"kind": "Bulkhead"}),
            bh_kind=BulkheadType.from_name(data.get("bh_kind", "Additional")),
            bh_beam=Measurement.from_dict(data.get("bh_beam") or {"v": 0.0}, UnitType.LENGTH_LONG),
            deck=Deck.from_dict(data.get("deck") or {}),
            ct_fwd=CT.from_dict(data.get("ct_fwd") or {}),
            ct_aft=CT.from_dict(data.get("ct_aft") or {}),
        )

"""Port of calc/hull.rs — Hull, Displacement, Length, SternType, BowType."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar

from .freeboard import Freeboard
from .units import Measurement, Units, UnitType
from .utils import rmax, rmin, rpow, rsqrt


class Displacement:
    """Normal displacement: Cb (block coeff) or D (tons)."""

    def __init__(self, kind: str, value: float):
        assert kind in ("Cb", "D")
        self.kind = kind
        self.value = float(value)

    @classmethod
    def cb(cls, v: float) -> "Displacement":
        return cls("Cb", v)

    @classmethod
    def d(cls, v: float) -> "Displacement":
        return cls("D", v)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Displacement) and self.kind == other.kind and self.value == other.value

    def __repr__(self) -> str:
        return f"Displacement.{self.kind}({self.value!r})"

    @classmethod
    def from_dict(cls, data: dict) -> "Displacement":
        """Parse .ship `{"Cb": x}` or `{"D": x}`."""
        if "Cb" in data:
            return cls.cb(float(data["Cb"]))
        return cls.d(float(data.get("D", 0.0)))


class Length:
    """Hull length: Lwl or Loa."""

    def __init__(self, kind: str, value: Measurement):
        assert kind in ("Lwl", "Loa")
        self.kind = kind
        self.value = value

    @classmethod
    def lwl(cls, v: Measurement) -> "Length":
        return cls("Lwl", v)

    @classmethod
    def loa(cls, v: Measurement) -> "Length":
        return cls("Loa", v)

    def __repr__(self) -> str:
        return f"Length.{self.kind}({self.value!r})"

    @classmethod
    def from_dict(cls, data: dict) -> "Length":
        """Parse .ship `{"Lwl": {...}}` or `{"Loa": {...}}`."""
        ml = UnitType.LENGTH_LONG
        if "Lwl" in data:
            return cls.lwl(Measurement.from_dict(data["Lwl"] or {"v": 0.0}, ml))
        return cls.loa(Measurement.from_dict(data.get("Loa") or {"v": 0.0}, ml))


_STERN_LABELS = {
    "CRUISER": "Cruiser stern",
    "TRANSM_SM": "Transom stern - small",
    "TRANSM_LG": "Transom stern - large",
    "ROUND": "Round stern",
}
_STERN_DISPLAYS = {
    "CRUISER": "a cruiser stern",
    "TRANSM_SM": "a small transom stern",
    "TRANSM_LG": "a large transom stern",
    "ROUND": "a round stern",
}


class SternType(Enum):
    # Declaration order is display order; sship index order is:
    # Cruiser=0, TransomSm=1, TransomLg=2, Round=3.
    CRUISER = "Cruiser"
    TRANSM_SM = "TransomSm"
    TRANSM_LG = "TransomLg"
    ROUND = "Round"

    @classmethod
    def default(cls) -> "SternType":
        return cls.CRUISER

    def label(self) -> str:
        return _STERN_LABELS[self.name]

    def __str__(self) -> str:
        return _STERN_DISPLAYS[self.name]

    def index(self) -> int:
        return SternType.ALL().index(self)

    @classmethod
    def ALL(cls) -> list["SternType"]:
        return [cls.CRUISER, cls.TRANSM_SM, cls.TRANSM_LG, cls.ROUND]

    @classmethod
    def all_labels(cls) -> list[str]:
        return [v.label() for v in cls.ALL()]

    @classmethod
    def from_index(cls, index: int) -> "SternType":
        all_v = cls.ALL()
        if 0 <= index < len(all_v):
            return all_v[index]
        return cls.default()

    @classmethod
    def from_str(cls, index: str) -> "SternType":
        try:
            i = int(index.strip())
        except (ValueError, AttributeError):
            return cls.default()
        all_v = cls.ALL()
        if 0 <= i < len(all_v):
            return all_v[i]
        return cls.default()

    @classmethod
    def from_name(cls, name: str) -> "SternType":
        """Parse serde variant name from .ship files ("TransomSm", ...)."""
        from .utils import enum_from_name

        return enum_from_name(cls, name, cls.default())

    def wp_calc(self) -> tuple[float, float]:
        if self is SternType.TRANSM_SM:
            return (0.262, 0.79)
        if self is SternType.TRANSM_LG:
            return (0.262, 0.81)
        return (0.262, 0.76)

    def leff(self, lwl: float, bb: float, cs: float) -> float:
        if cs == 0.0:
            return 0.0
        if self is SternType.TRANSM_SM:
            return bb * 0.5 / cs + lwl
        if self is SternType.TRANSM_LG:
            return bb / cs + lwl
        return lwl


class BowType:
    """Ram/BulbForward carry a Measurement; others carry none."""

    NORMAL = "Normal"
    BULB_STRAIGHT = "BulbStraight"
    BULB_FORWARD = "BulbForward"
    RAM = "Ram"

    _ORDER = ["Normal", "BulbStraight", "BulbForward", "Ram"]
    _LABELS = {
        "Normal": "Normal bow",
        "BulbStraight": "Bulbous bow - straight",
        "BulbForward": "Bulbous bow - forward",
        "Ram": "Ram Bow",
    }
    _DISPLAYS = {
        "Normal": "a normal bow",
        "BulbStraight": "a straight bulbous bow",
        "BulbForward": "an extended bulbous bow",
        "Ram": "a ram bow",
    }

    def __init__(self, kind: str = "Normal", extra: Measurement | None = None):
        assert kind in BowType._ORDER
        self.kind = kind
        if extra is None:
            extra = Measurement(0.0, UnitType.LENGTH_LONG, Units.IMPERIAL)
        self.extra = extra

    @classmethod
    def default(cls) -> "BowType":
        return cls("Normal")

    @classmethod
    def normal(cls) -> "BowType":
        return cls("Normal")

    @classmethod
    def bulb_straight(cls) -> "BowType":
        return cls("BulbStraight")

    @classmethod
    def bulb_forward(cls, m: Measurement) -> "BowType":
        return cls("BulbForward", m)

    @classmethod
    def ram(cls, m: Measurement) -> "BowType":
        return cls("Ram", m)

    def label(self) -> str:
        return BowType._LABELS[self.kind]

    def __str__(self) -> str:
        return BowType._DISPLAYS[self.kind]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BowType):
            return NotImplemented
        if self.kind != other.kind:
            return False
        if self.kind in ("Ram", "BulbForward"):
            return self.extra == other.extra
        return True

    def __repr__(self) -> str:
        return f"BowType.{self.kind}({self.extra!r})"

    def index(self) -> int:
        return BowType._ORDER.index(self.kind)

    @classmethod
    def ALL(cls) -> list["BowType"]:
        z = Measurement(0.0, UnitType.LENGTH_LONG, Units.IMPERIAL)
        return [cls("Normal"), cls("BulbStraight"), cls("BulbForward", z), cls("Ram", z)]

    @classmethod
    def all_labels(cls) -> list[str]:
        return [v.label() for v in cls.ALL()]

    @classmethod
    def from_index(cls, index: int) -> "BowType":
        all_v = cls.ALL()
        if 0 <= index < len(all_v):
            return all_v[index]
        return cls.default()

    @classmethod
    def from_str(cls, index: str) -> "BowType":
        try:
            i = int(str(index).strip())
        except (ValueError, AttributeError):
            return cls.default()
        return cls.from_index(i)

    @classmethod
    def from_dict(cls, data) -> "BowType":
        """Parse .ship bow_type: plain name, or serde `{"Ram": {...}}`."""
        ml = UnitType.LENGTH_LONG
        if isinstance(data, dict):
            for kind in ("Ram", "BulbForward"):
                if kind in data:
                    m = Measurement.from_dict(data[kind] or {"v": 0.0}, ml)
                    return cls(kind, m)
            return cls.default()
        name = str(data).strip()
        if name in ("Ram", "BulbForward"):
            return cls(name, Measurement(0.0, ml, Units.IMPERIAL))
        if name == "BulbStraight":
            return cls.bulb_straight()
        if name == "Normal":
            return cls.normal()
        return cls.default()

    def ram_len(self) -> Measurement:
        if self.kind in ("Ram", "BulbForward"):
            return self.extra
        return Measurement(0.0, UnitType.LENGTH_LONG, Units.IMPERIAL)


def _m(v: float) -> Measurement:
    return Measurement(v, UnitType.LENGTH_LONG, Units.IMPERIAL)


@dataclass
class Hull:
    units: Units = Units.IMPERIAL
    disp: Displacement = field(default_factory=lambda: Displacement.cb(0.550))
    len: Length = field(default_factory=lambda: Length.lwl(Measurement(0.0, UnitType.LENGTH_LONG, Units.IMPERIAL)))
    b: Measurement = field(default_factory=lambda: _m(0.0))
    bb: Measurement = field(default_factory=lambda: _m(0.0))
    t: Measurement = field(default_factory=lambda: _m(0.0))
    boxy: bool = False
    bow_type: BowType = field(default_factory=BowType.default)
    stern_type: SternType = SternType.CRUISER
    stern_overhang: Measurement = field(default_factory=lambda: _m(0.0))
    freeboard: Freeboard = field(default_factory=Freeboard)
    bow_angle: float = 0.0

    FT3_PER_TON_SEA: ClassVar[float] = 35.0

    def set_shafts(self, shafts: int) -> None:
        self.boxy = shafts < 2

    def freeboard_desc(self) -> str:
        fb = self.freeboard
        if fb.fc_aft == fb.fd_fwd and fb.fd_aft == fb.ad_fwd and fb.ad_aft == fb.qd_fwd:
            return "a flush deck"
        parts: list[str] = []
        if fb.fc_aft.imp() > fb.fd_fwd.imp():
            parts.append("raised forecastle")
        elif fb.fc_aft.imp() < fb.fd_fwd.imp():
            parts.append("low forecastle")
        if fb.fd_aft.imp() > fb.ad_fwd.imp():
            parts.append("rise forward of midbreak")
        elif fb.fd_aft.imp() < fb.ad_fwd.imp():
            parts.append("rise aft of midbreak")
        if fb.ad_aft.imp() > fb.qd_fwd.imp():
            parts.append("low quarterdeck")
        elif fb.ad_aft.imp() < fb.qd_fwd.imp():
            parts.append("raised quarterdeck")
        return ", ".join(parts)

    def cs(self) -> float:
        if self.lwl().imp() == 0.0:
            return 0.0
        return 0.4 * rpow(self.bb.imp() / self.lwl().imp() * 6.0, 1.0 / 3.0) * rsqrt(self.cb() / 0.52)

    @staticmethod
    def cm(block: float) -> float:
        if block == 0.0:
            return 1.006
        return 1.006 - 0.0056 * rpow(block, -3.56)

    @staticmethod
    def cp(block: float) -> float:
        cm = Hull.cm(block)
        if cm == 0.0:
            return 0.0
        return block / cm

    def cb(self) -> float:
        if self.disp.kind == "Cb":
            return self.disp.value
        return self.cb_calc(self.disp.value, self.t.imp())

    def cb_calc(self, d: float, t: float) -> float:
        volume = self.lwl().imp() * self.bb.imp() * t
        if volume == 0.0:
            return 0.0
        return rmin(rmax(d * self.FT3_PER_TON_SEA / volume, 0.0), 1.0)

    def set_cb(self, cb: float) -> float:
        self.disp = Displacement.cb(cb)
        return cb

    def d(self) -> float:
        if self.disp.kind == "D":
            return self.disp.value
        return self.d_calc(self.disp.value)

    def d_calc(self, cb: float) -> float:
        return cb * self.lwl().imp() * self.bb.imp() * self.t.imp() / self.FT3_PER_TON_SEA

    def set_d(self, d: float) -> float:
        self.disp = Displacement.d(d)
        return d

    def cwp(self) -> float:
        cp = Hull.cp(rmax(self.cb(), 0.4))
        if self.stern_type in (SternType.TRANSM_LG, SternType.TRANSM_SM):
            a, f = self.stern_type.wp_calc()
        elif self.boxy or self.cb() >= 0.75:
            a, f = (0.175, 0.875)
        else:
            a, f = self.stern_type.wp_calc()
        cwp = min(a + f * cp, 1.0)
        if self.cb() < 0.4:
            cwp -= 0.0281 - (self.cb() - 0.3) ** 1.55
        return cwp

    def wp(self) -> Measurement:
        return Measurement(self.cwp() * self.lwl().imp() * self.b.imp(), UnitType.AREA, Units.IMPERIAL)

    def ws(self) -> float:
        if self.t.imp() == 0.0:
            return 0.0
        return self.lwl().imp() * self.t.imp() * 1.7 + (self.d() * self.FT3_PER_TON_SEA / self.t.imp())

    def set_lwl(self, length: float, units: Units) -> float:
        self.len = Length.lwl(Measurement(length, UnitType.LENGTH_LONG, units))
        return length

    def lwl(self) -> Measurement:
        if self.len.kind == "Lwl":
            return self.len.value
        loa = self.len.value
        return Measurement(
            loa.imp() - max(max(self.bow_type.ram_len().imp(), self.stem_len()), 0.0)
            - max(self.stern_overhang.imp(), 0.0),
            UnitType.LENGTH_LONG,
            Units.IMPERIAL,
        )

    def loa(self) -> Measurement:
        if self.len.kind == "Loa":
            return self.len.value
        lwl = self.len.value
        return Measurement(
            lwl.imp() + max(max(self.bow_type.ram_len().imp(), self.stem_len()), 0.0)
            + max(self.stern_overhang.imp(), 0.0),
            UnitType.LENGTH_LONG,
            Units.IMPERIAL,
        )

    def leff(self) -> float:
        return self.stern_type.leff(self.lwl().imp(), self.bb.imp(), self.cs())

    def t_calc(self, d: float) -> float:
        return self.t.imp() + (d - self.d()) / (self.wp().imp() / self.FT3_PER_TON_SEA)

    def ts(self) -> float:
        return (Hull.cm(self.cb()) * 2.0 - 1.0) * self.t.imp()

    def stem_len(self) -> float:
        if abs(self.bow_angle) >= 90.0:
            return 0.0
        return self.freeboard.fc_fwd.imp() * math.tan(self.bow_angle * math.pi / 180.0)

    def is_wet_fwd(self) -> bool:
        return self.freeboard.fc_fwd.imp() < (1.1 * math.sqrt(self.lwl().imp()))

    def free_cap(self, cap_calc_broadside: bool) -> float:
        if self.b.imp() == 0.0:
            return 0.0
        if self.freeboard.average().imp() > (self.b.imp() / 3.0):
            return self.freeboard.average().imp() ** 2.0 * 3.0 / self.b.imp()
        if cap_calc_broadside:
            return self.freeboard.average().imp() - 6.0
        return self.freeboard.average().imp()

    def vn(self) -> float:
        return rsqrt(self.leff())

    def len2beam(self) -> float:
        if self.bb.imp() == 0.0:
            return 0.0
        return self.lwl().imp() / self.bb.imp()

    @classmethod
    def from_dict(cls, data: dict) -> "Hull":
        """Parse a .ship hull object (freeboard fields are inlined)."""
        from .units import Units as _Units

        ml = UnitType.LENGTH_LONG

        def get(key: str) -> Measurement:
            return Measurement.from_dict(data.get(key) or {"v": 0.0}, ml)

        return cls(
            units=_Units.from_name(data.get("units", "")),
            disp=Displacement.from_dict(data.get("disp") or {"Cb": 0.0}),
            len=Length.from_dict(data.get("len") or {"Lwl": {"v": 0.0}}),
            b=get("b"),
            bb=get("bb"),
            t=get("t"),
            bow_type=BowType.from_dict(data.get("bow_type", "Normal")),
            stern_type=SternType.from_name(data.get("stern_type", "Cruiser")),
            stern_overhang=get("stern_overhang"),
            freeboard=Freeboard.from_dict(data),
            bow_angle=float(data.get("bow_angle", 0.0)),
        )

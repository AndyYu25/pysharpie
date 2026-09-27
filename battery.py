"""Port of calc/battery.rs — Battery/SubBattery + gun enums (calc core only).

Out of scope (report prose): Battery.desc/long_desc, internals output.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from .armor import Armor
from .units import Measurement, Units, UnitType
from .utils import POUND2TON, rhalf, rmax, year_adj

_PI = math.pi


def _ms(v: float) -> Measurement:
    return Measurement(v, UnitType.LENGTH_SMALL, Units.IMPERIAL)


class GunType(Enum):
    MUZZLE_LOADING = "MuzzleLoading"
    BREECH_LOADING = "BreechLoading"
    QUICK_FIRING = "QuickFiring"
    ANTI_AIR = "AntiAir"
    DUAL_PURPOSE = "DualPurpose"
    RAPID_FIRE = "RapidFire"
    MACHINE_GUN = "MachineGun"

    @classmethod
    def default(cls) -> "GunType":
        return cls.BREECH_LOADING

    def label(self) -> str:
        return {
            GunType.MUZZLE_LOADING: "Muzzle loading gun",
            GunType.BREECH_LOADING: "Breech loading gun",
            GunType.QUICK_FIRING: "Quick firing gun",
            GunType.ANTI_AIR: "Anti-air gun",
            GunType.DUAL_PURPOSE: "Dual purpose gun",
            GunType.RAPID_FIRE: "Auto rapid fire gun",
            GunType.MACHINE_GUN: "Machine gun",
        }[self]

    def __str__(self) -> str:
        return {
            GunType.MUZZLE_LOADING: "Muzzle loading",
            GunType.BREECH_LOADING: "Breech loading",
            GunType.QUICK_FIRING: "Quick firing",
            GunType.ANTI_AIR: "Anti-air",
            GunType.DUAL_PURPOSE: "Dual purpose",
            GunType.RAPID_FIRE: "Auto rapid fire",
            GunType.MACHINE_GUN: "Machine",
        }[self]

    def index(self) -> int:
        return GunType.ALL().index(self)

    @classmethod
    def ALL(cls) -> list["GunType"]:
        return [
            cls.MUZZLE_LOADING,
            cls.BREECH_LOADING,
            cls.QUICK_FIRING,
            cls.ANTI_AIR,
            cls.DUAL_PURPOSE,
            cls.RAPID_FIRE,
            cls.MACHINE_GUN,
        ]

    @classmethod
    def all_labels(cls) -> list[str]:
        return [v.label() for v in cls.ALL()]

    @classmethod
    def from_index(cls, index: int) -> "GunType":
        all_v = cls.ALL()
        return all_v[index] if 0 <= index < len(all_v) else cls.default()

    @classmethod
    def from_str(cls, index: str) -> "GunType":
        try:
            return cls.from_index(int(str(index).strip()))
        except (ValueError, AttributeError):
            return cls.default()

    @classmethod
    def from_name(cls, name: str) -> "GunType":
        from .utils import enum_from_name

        return enum_from_name(cls, name, cls.default())

    def armor_face_wgt(self, armor_back: float) -> float:
        wgt = {
            GunType.MUZZLE_LOADING: 1.0,
            GunType.BREECH_LOADING: 1.0,
            GunType.QUICK_FIRING: 1.0,
            GunType.ANTI_AIR: 0.333,
            GunType.DUAL_PURPOSE: 1.0,
            GunType.RAPID_FIRE: 1.0,
            GunType.MACHINE_GUN: 1.0,
        }[self]
        if armor_back == 0.0:
            wgt *= {
                GunType.MUZZLE_LOADING: 1.0,
                GunType.BREECH_LOADING: 1.0,
                GunType.QUICK_FIRING: 1.0,
                GunType.ANTI_AIR: 1.0,
                GunType.DUAL_PURPOSE: 1.0,
                GunType.RAPID_FIRE: 1.0,
                GunType.MACHINE_GUN: 0.333,
            }[self]
        return wgt

    def wgt_sm(self) -> float:
        return {
            GunType.MUZZLE_LOADING: 0.9,
            GunType.BREECH_LOADING: 1.0,
            GunType.QUICK_FIRING: 1.35,
            GunType.ANTI_AIR: 1.44,
            GunType.DUAL_PURPOSE: 1.57,
            GunType.RAPID_FIRE: 2.16,
            GunType.MACHINE_GUN: 1.0,
        }[self]

    def wgt_lg(self) -> float:
        return {
            GunType.MUZZLE_LOADING: 0.98,
            GunType.BREECH_LOADING: 1.0,
            GunType.QUICK_FIRING: 1.0,
            GunType.ANTI_AIR: 1.0,
            GunType.DUAL_PURPOSE: 1.1,
            GunType.RAPID_FIRE: 1.5,
            GunType.MACHINE_GUN: 1.0,
        }[self]


class MountType(Enum):
    BROADSIDE = "Broadside"
    COLES_TURRET = "ColesTurret"
    OPEN_BARBETTE = "OpenBarbette"
    CLOSED_BARBETTE = "ClosedBarbette"
    DECK_AND_HOIST = "DeckAndHoist"
    DECK = "Deck"
    CASEMATE = "Casemate"

    @classmethod
    def default(cls) -> "MountType":
        return cls.DECK

    def label(self) -> str:
        return {
            MountType.BROADSIDE: "in broadside mount",
            MountType.COLES_TURRET: "in Coles/Ericsson turret mount",
            MountType.OPEN_BARBETTE: "in open barbette mount",
            MountType.CLOSED_BARBETTE: "in turret on barbette mount",
            MountType.DECK_AND_HOIST: "in deck and hoist mount",
            MountType.DECK: "in deck mount",
            MountType.CASEMATE: "in casemate mount",
        }[self]

    def __str__(self) -> str:
        return {
            MountType.BROADSIDE: "broadside",
            MountType.COLES_TURRET: "Coles/Ericsson turret",
            MountType.OPEN_BARBETTE: "open barbette",
            MountType.CLOSED_BARBETTE: "turret on barbette",
            MountType.DECK_AND_HOIST: "deck and hoist",
            MountType.DECK: "deck",
            MountType.CASEMATE: "casemate",
        }[self]

    def index(self) -> int:
        return MountType.ALL().index(self)

    @classmethod
    def ALL(cls) -> list["MountType"]:
        return [
            cls.BROADSIDE,
            cls.COLES_TURRET,
            cls.OPEN_BARBETTE,
            cls.CLOSED_BARBETTE,
            cls.DECK_AND_HOIST,
            cls.DECK,
            cls.CASEMATE,
        ]

    @classmethod
    def all_labels(cls) -> list[str]:
        return [v.label() for v in cls.ALL()]

    @classmethod
    def from_index(cls, index: int) -> "MountType":
        all_v = cls.ALL()
        return all_v[index] if 0 <= index < len(all_v) else cls.default()

    @classmethod
    def from_str(cls, index: str) -> "MountType":
        try:
            return cls.from_index(int(str(index).strip()))
        except (ValueError, AttributeError):
            return cls.default()

    @classmethod
    def from_name(cls, name: str) -> "MountType":
        from .utils import enum_from_name

        return enum_from_name(cls, name, cls.default())

    def gunhouse_hgt_factor(self) -> float:
        return 2.0 if self is MountType.COLES_TURRET else 1.0

    def armor_face_wgt(self, armor_back: float) -> float:
        wgt = {
            MountType.BROADSIDE: 1.0,
            MountType.COLES_TURRET: _PI / 2.0,
            MountType.OPEN_BARBETTE: 0.0,
            MountType.CLOSED_BARBETTE: 0.5,
            MountType.DECK_AND_HOIST: 0.5,
            MountType.DECK: 0.5,
            MountType.CASEMATE: 1.0,
        }[self]
        if armor_back == 0.0:
            wgt += {
                MountType.BROADSIDE: 0.0,
                MountType.COLES_TURRET: 0.0,
                MountType.OPEN_BARBETTE: 0.0,
                MountType.CLOSED_BARBETTE: 1.0,
                MountType.DECK_AND_HOIST: 1.0,
                MountType.DECK: 1.0,
                MountType.CASEMATE: 0.0,
            }[self]
        return wgt

    def armor_back_wgt(self) -> tuple[float, float]:
        a = {
            MountType.BROADSIDE: 0.0,
            MountType.COLES_TURRET: 0.0,
            MountType.OPEN_BARBETTE: 0.0,
            MountType.CLOSED_BARBETTE: 2.5,
            MountType.DECK_AND_HOIST: 2.5,
            MountType.DECK: 2.5,
            MountType.CASEMATE: 0.0,
        }[self]
        b = {
            MountType.BROADSIDE: 0.75,
            MountType.COLES_TURRET: 1.0,
            MountType.OPEN_BARBETTE: 0.75,
            MountType.CLOSED_BARBETTE: 0.75,
            MountType.DECK_AND_HOIST: 0.75,
            MountType.DECK: 0.75,
            MountType.CASEMATE: 0.75,
        }[self]
        return (a, b)

    def armor_barb_wgt(self) -> float:
        return {
            MountType.BROADSIDE: 0.0,
            MountType.COLES_TURRET: 0.0,
            MountType.OPEN_BARBETTE: 0.6416,
            MountType.CLOSED_BARBETTE: 0.5,
            MountType.DECK_AND_HOIST: 0.1,
            MountType.DECK: 0.0,
            MountType.CASEMATE: 0.1,
        }[self]

    def wgt(self) -> float:
        return {
            MountType.BROADSIDE: 0.83,
            MountType.COLES_TURRET: 3.5,
            MountType.OPEN_BARBETTE: 3.33,
            MountType.CLOSED_BARBETTE: 3.5,
            MountType.DECK_AND_HOIST: 3.15,
            MountType.DECK: 1.08,
            MountType.CASEMATE: 1.08,
        }[self]

    def wgt_adj(self) -> float:
        return {
            MountType.BROADSIDE: 0.5,
            MountType.COLES_TURRET: 1.0,
            MountType.OPEN_BARBETTE: 0.7,
            MountType.CLOSED_BARBETTE: 1.0,
            MountType.DECK_AND_HOIST: 1.0,
            MountType.DECK: 0.5,
            MountType.CASEMATE: 0.5,
        }[self]


class GunDistributionType(Enum):
    NONE = "None"
    CENTERLINE_EVEN = "CenterlineEven"
    CENTERLINE_ENDS_FD = "CenterlineEndsFD"
    CENTERLINE_ENDS_AD = "CenterlineEndsAD"
    CENTERLINE_FD_FWD = "CenterlineFDFwd"
    CENTERLINE_FD = "CenterlineFD"
    CENTERLINE_FD_AFT = "CenterlineFDAft"
    CENTERLINE_AD_FWD = "CenterlineADFwd"
    CENTERLINE_AD = "CenterlineAD"
    CENTERLINE_AD_AFT = "CenterlineADAft"
    SIDES_EVEN = "SidesEven"
    SIDES_ENDS_FD = "SidesEndsFD"
    SIDES_ENDS_AD = "SidesEndsAD"
    SIDES_FD_FWD = "SidesFDFwd"
    SIDES_FD = "SidesFD"
    SIDES_FD_AFT = "SidesFDAft"
    SIDES_AD_FWD = "SidesADFwd"
    SIDES_AD = "SidesAD"
    SIDES_AD_AFT = "SidesADAft"

    @classmethod
    def default(cls) -> "GunDistributionType":
        return cls.NONE

    def label(self) -> str:
        return {
            GunDistributionType.CENTERLINE_EVEN: "Centreline - distributed",
            GunDistributionType.CENTERLINE_ENDS_FD: "Centreline - ends (fore >= aft)",
            GunDistributionType.CENTERLINE_ENDS_AD: "Centreline - ends (aft >= fore)",
            GunDistributionType.CENTERLINE_FD_FWD: "Centreline - fore deck forward",
            GunDistributionType.CENTERLINE_FD: "Centreline - fore deck",
            GunDistributionType.CENTERLINE_FD_AFT: "Centreline - fore deck aft",
            GunDistributionType.CENTERLINE_AD_FWD: "Centreline - aft deck forward",
            GunDistributionType.CENTERLINE_AD: "Centreline - aft deck",
            GunDistributionType.CENTERLINE_AD_AFT: "Centreline - aft deck aft",
            GunDistributionType.SIDES_EVEN: "Sides - distributed",
            GunDistributionType.SIDES_ENDS_FD: "Sides - ends (fore >= aft)",
            GunDistributionType.SIDES_ENDS_AD: "Sides - ends (aft >= fore)",
            GunDistributionType.SIDES_FD_FWD: "Sides - fore deck forward",
            GunDistributionType.SIDES_FD: "Sides - fore deck",
            GunDistributionType.SIDES_FD_AFT: "Sides - fore deck aft",
            GunDistributionType.SIDES_AD_FWD: "Sides - aft deck forward",
            GunDistributionType.SIDES_AD: "Sides - aft deck",
            GunDistributionType.SIDES_AD_AFT: "Sides - aft deck aft",
            GunDistributionType.NONE: "None",
        }[self]

    def __str__(self) -> str:
        return self.label()

    def index(self) -> int:
        return GunDistributionType.ALL().index(self)

    @classmethod
    def ALL(cls) -> list["GunDistributionType"]:
        # sship index order (choice_enum declaration order)
        return [
            cls.CENTERLINE_EVEN,
            cls.CENTERLINE_ENDS_FD,
            cls.CENTERLINE_ENDS_AD,
            cls.CENTERLINE_FD_FWD,
            cls.CENTERLINE_FD,
            cls.CENTERLINE_FD_AFT,
            cls.CENTERLINE_AD_FWD,
            cls.CENTERLINE_AD,
            cls.CENTERLINE_AD_AFT,
            cls.SIDES_EVEN,
            cls.SIDES_ENDS_FD,
            cls.SIDES_ENDS_AD,
            cls.SIDES_FD_FWD,
            cls.SIDES_FD,
            cls.SIDES_FD_AFT,
            cls.SIDES_AD_FWD,
            cls.SIDES_AD,
            cls.SIDES_AD_AFT,
            cls.NONE,
        ]

    @classmethod
    def all_labels(cls) -> list[str]:
        return [v.label() for v in cls.ALL()]

    @classmethod
    def from_index(cls, index: int) -> "GunDistributionType":
        all_v = cls.ALL()
        return all_v[index] if 0 <= index < len(all_v) else cls.default()

    @classmethod
    def from_str(cls, index: str) -> "GunDistributionType":
        try:
            return cls.from_index(int(str(index).strip()))
        except (ValueError, AttributeError):
            return cls.default()

    @classmethod
    def from_name(cls, name: str) -> "GunDistributionType":
        from .utils import enum_from_name

        return enum_from_name(cls, name, cls.default())

    def super_aft(self) -> bool:
        return self in (
            GunDistributionType.CENTERLINE_ENDS_AD,
            GunDistributionType.CENTERLINE_AD_FWD,
            GunDistributionType.CENTERLINE_AD,
            GunDistributionType.CENTERLINE_AD_AFT,
            GunDistributionType.SIDES_ENDS_AD,
            GunDistributionType.SIDES_AD_FWD,
            GunDistributionType.SIDES_AD,
            GunDistributionType.SIDES_AD_AFT,
        )

    def mounts_fwd(self, tot: int, fwd_len: float) -> int:
        half = rhalf

        if self is GunDistributionType.NONE:
            return 0
        if self in (
            GunDistributionType.CENTERLINE_FD_FWD,
            GunDistributionType.CENTERLINE_FD,
            GunDistributionType.CENTERLINE_FD_AFT,
            GunDistributionType.CENTERLINE_AD_FWD,
            GunDistributionType.SIDES_FD_FWD,
            GunDistributionType.SIDES_FD,
            GunDistributionType.SIDES_FD_AFT,
        ):
            return tot
        if self in (
            GunDistributionType.CENTERLINE_AD,
            GunDistributionType.CENTERLINE_AD_AFT,
            GunDistributionType.SIDES_AD_FWD,
            GunDistributionType.SIDES_AD,
            GunDistributionType.SIDES_AD_AFT,
        ):
            return 0
        if self in (GunDistributionType.CENTERLINE_ENDS_FD, GunDistributionType.SIDES_ENDS_FD):
            return tot if tot == 1 else half(tot)
        if self in (GunDistributionType.CENTERLINE_ENDS_AD, GunDistributionType.SIDES_ENDS_AD):
            return 0 if tot == 1 else tot - half(tot)
        # Even
        if tot == 1 and fwd_len >= 0.5:
            return tot
        if fwd_len >= 0.5:
            return half(tot)
        if tot == 1 and fwd_len < 0.5:
            return 0
        return tot - half(tot)

    def free(self, num_mounts: int, hull) -> float:
        if num_mounts == 0:
            return 0.0
        fwd = float(self.mounts_fwd(num_mounts, hull.freeboard.fc_len + hull.freeboard.fd_len))
        tot = float(num_mounts)
        fd = hull.freeboard.fd()
        ad = hull.freeboard.ad()
        fd_fwd = hull.freeboard.fd_fwd.imp()
        fd_aft = hull.freeboard.fd_aft.imp()
        ad_fwd = hull.freeboard.ad_fwd.imp()
        ad_aft = hull.freeboard.ad_aft.imp()
        if self in (GunDistributionType.CENTERLINE_EVEN, GunDistributionType.SIDES_EVEN):
            return (fwd * fd + (tot - fwd) * ad) / tot
        if self in (
            GunDistributionType.CENTERLINE_ENDS_FD,
            GunDistributionType.CENTERLINE_ENDS_AD,
            GunDistributionType.SIDES_ENDS_FD,
            GunDistributionType.SIDES_ENDS_AD,
        ):
            fwd_part = fwd * ((fd_fwd - fd) / fwd * 0.5 + (fd_fwd + fd) * 0.5) if fwd > 0.0 else 0.0
            return (fwd_part + (tot - fwd) * ((ad_aft - ad) * 1.0 / (tot - fwd) * 0.5 + (ad_aft + ad) * 0.5)) / tot
        if self in (GunDistributionType.CENTERLINE_FD_FWD, GunDistributionType.SIDES_FD_FWD):
            return (fd_fwd - fd) / fwd * 0.5 + (fd_fwd + fd) * 0.5 if fwd > 0.0 else 0.0
        if self in (GunDistributionType.CENTERLINE_FD, GunDistributionType.SIDES_FD):
            return fd
        if self in (GunDistributionType.CENTERLINE_FD_AFT, GunDistributionType.SIDES_FD_AFT):
            return (fd_aft - fd) / fwd * 0.5 + (fd_aft + fd) * 0.5 if fwd > 0.0 else 0.0
        if self in (GunDistributionType.CENTERLINE_AD_FWD, GunDistributionType.SIDES_AD_FWD):
            return (ad_fwd - ad) / (tot - fwd) * 0.5 + (ad_fwd + ad) * 0.5 if (tot - fwd) > 0.0 else 0.0
        if self in (GunDistributionType.CENTERLINE_AD, GunDistributionType.SIDES_AD):
            return ad
        if self in (GunDistributionType.CENTERLINE_AD_AFT, GunDistributionType.SIDES_AD_AFT):
            return (ad_aft - ad) / (tot - fwd) * 0.5 + (ad_aft + ad) * 0.5 if (tot - fwd) > 0.0 else 0.0
        return 0.0

    def _gun_position(self, fd_len: float, ad_len: float) -> float:
        return {
            GunDistributionType.CENTERLINE_FD_FWD: 0.25 * fd_len,
            GunDistributionType.CENTERLINE_FD: 0.5 * fd_len,
            GunDistributionType.CENTERLINE_FD_AFT: 0.75 * fd_len,
            GunDistributionType.CENTERLINE_AD_FWD: 0.25 * ad_len,
            GunDistributionType.CENTERLINE_AD: 0.5 * ad_len,
            GunDistributionType.CENTERLINE_AD_AFT: 0.75 * ad_len,
            GunDistributionType.SIDES_FD_FWD: 0.25 * fd_len,
            GunDistributionType.SIDES_FD: 0.5 * fd_len,
            GunDistributionType.SIDES_FD_AFT: 0.75 * fd_len,
            GunDistributionType.SIDES_AD_FWD: 0.25 * ad_len,
            GunDistributionType.SIDES_AD: 0.5 * ad_len,
            GunDistributionType.SIDES_AD_AFT: 0.75 * ad_len,
        }.get(self, 0.0)

    def g1_gun_position(self, fd_len: float, ad_len: float) -> float:
        if self in (
            GunDistributionType.CENTERLINE_EVEN,
            GunDistributionType.CENTERLINE_ENDS_FD,
            GunDistributionType.CENTERLINE_ENDS_AD,
            GunDistributionType.SIDES_EVEN,
            GunDistributionType.SIDES_ENDS_FD,
            GunDistributionType.SIDES_ENDS_AD,
        ):
            return 1.0
        return self._gun_position(fd_len, ad_len)

    def g2_gun_position(self, fd_len: float, ad_len: float) -> float:
        if self in (
            GunDistributionType.CENTERLINE_EVEN,
            GunDistributionType.CENTERLINE_ENDS_FD,
            GunDistributionType.CENTERLINE_ENDS_AD,
            GunDistributionType.SIDES_EVEN,
            GunDistributionType.SIDES_ENDS_FD,
            GunDistributionType.SIDES_ENDS_AD,
        ):
            return 0.0
        return self._gun_position(fd_len, ad_len)

    def super_factor_long(self) -> bool:
        return self not in (
            GunDistributionType.NONE,
            GunDistributionType.CENTERLINE_EVEN,
            GunDistributionType.CENTERLINE_ENDS_FD,
            GunDistributionType.SIDES_EVEN,
            GunDistributionType.SIDES_ENDS_FD,
            GunDistributionType.SIDES_ENDS_AD,
        ) or self in (GunDistributionType.CENTERLINE_ENDS_AD,)


class GunLayoutType(Enum):
    SINGLE = "Single"
    TWIN_2ROW = "Twin2Row"
    QUAD_4ROW = "Quad4Row"
    TWIN = "Twin"
    TWO_GUN = "TwoGun"
    QUAD_2ROW = "Quad2Row"
    TRIPLE = "Triple"
    THREE_GUN = "ThreeGun"
    SEX_2ROW = "Sex2Row"
    QUAD = "Quad"
    FOUR_GUN = "FourGun"
    OCT_2ROW = "Oct2Row"
    QUINT = "Quint"
    FIVE_GUN = "FiveGun"
    DEC_2ROW = "Dec2Row"

    @classmethod
    def default(cls) -> "GunLayoutType":
        return cls.SINGLE

    def label(self) -> str:
        return {
            GunLayoutType.SINGLE: "Single mount",
            GunLayoutType.TWIN_2ROW: "2 row twin mount",
            GunLayoutType.QUAD_4ROW: "4 row quad mount",
            GunLayoutType.TWIN: "Twin mount",
            GunLayoutType.TWO_GUN: "2-gun mount",
            GunLayoutType.QUAD_2ROW: "2 row quad mount",
            GunLayoutType.TRIPLE: "Triple mount",
            GunLayoutType.THREE_GUN: "3-gun mount",
            GunLayoutType.SEX_2ROW: "2 row sextuple mount",
            GunLayoutType.QUAD: "Quad mount",
            GunLayoutType.FOUR_GUN: "4-gun mount",
            GunLayoutType.OCT_2ROW: "2 row octuple mount",
            GunLayoutType.QUINT: "Quintuple mount",
            GunLayoutType.FIVE_GUN: "5-gun mount",
            GunLayoutType.DEC_2ROW: "2 row decuple mount",
        }[self]

    def __str__(self) -> str:
        return {
            GunLayoutType.SINGLE: "Single",
            GunLayoutType.TWIN_2ROW: "2 row, twin",
            GunLayoutType.QUAD_4ROW: "4 row, quad",
            GunLayoutType.TWIN: "Twin",
            GunLayoutType.TWO_GUN: "2-gun",
            GunLayoutType.QUAD_2ROW: "2 row, quad",
            GunLayoutType.TRIPLE: "Triple",
            GunLayoutType.THREE_GUN: "3-gun",
            GunLayoutType.SEX_2ROW: "2 row, sextuple",
            GunLayoutType.QUAD: "quad",
            GunLayoutType.FOUR_GUN: "4-gun",
            GunLayoutType.OCT_2ROW: "2 row, octuple",
            GunLayoutType.QUINT: "quintuple",
            GunLayoutType.FIVE_GUN: "5-gun",
            GunLayoutType.DEC_2ROW: "2 row, decuple",
        }[self]

    def index(self) -> int:
        return GunLayoutType.ALL().index(self)

    @classmethod
    def ALL(cls) -> list["GunLayoutType"]:
        return [
            cls.SINGLE,
            cls.TWIN_2ROW,
            cls.QUAD_4ROW,
            cls.TWIN,
            cls.TWO_GUN,
            cls.QUAD_2ROW,
            cls.TRIPLE,
            cls.THREE_GUN,
            cls.SEX_2ROW,
            cls.QUAD,
            cls.FOUR_GUN,
            cls.OCT_2ROW,
            cls.QUINT,
            cls.FIVE_GUN,
            cls.DEC_2ROW,
        ]

    @classmethod
    def all_labels(cls) -> list[str]:
        return [v.label() for v in cls.ALL()]

    @classmethod
    def from_index(cls, index: int) -> "GunLayoutType":
        all_v = cls.ALL()
        return all_v[index] if 0 <= index < len(all_v) else cls.default()

    @classmethod
    def from_str(cls, index: str) -> "GunLayoutType":
        try:
            return cls.from_index(int(str(index).strip()))
        except (ValueError, AttributeError):
            return cls.default()

    @classmethod
    def from_name(cls, name: str) -> "GunLayoutType":
        from .utils import enum_from_name

        return enum_from_name(cls, name, cls.default())

    def guns_per(self) -> int:
        return {
            GunLayoutType.SINGLE: 1,
            GunLayoutType.TWIN_2ROW: 2,
            GunLayoutType.TWIN: 2,
            GunLayoutType.TWO_GUN: 2,
            GunLayoutType.TRIPLE: 3,
            GunLayoutType.THREE_GUN: 3,
            GunLayoutType.QUAD_2ROW: 4,
            GunLayoutType.QUAD_4ROW: 4,
            GunLayoutType.QUAD: 4,
            GunLayoutType.FOUR_GUN: 4,
            GunLayoutType.QUINT: 5,
            GunLayoutType.FIVE_GUN: 5,
            GunLayoutType.SEX_2ROW: 6,
            GunLayoutType.OCT_2ROW: 8,
            GunLayoutType.DEC_2ROW: 10,
        }[self]

    def diameter_calc_nums(self) -> tuple[float, float]:
        return {
            GunLayoutType.SINGLE: (1.44, 0.609725),
            GunLayoutType.TWIN_2ROW: (1.44, 0.609725),
            GunLayoutType.QUAD_4ROW: (1.44, 0.609725),
            GunLayoutType.TWIN: (1.52, 0.4205),
            GunLayoutType.TWO_GUN: (1.52, 0.4205),
            GunLayoutType.QUAD_2ROW: (1.52, 0.4205),
            GunLayoutType.TRIPLE: (1.64, 0.29),
            GunLayoutType.THREE_GUN: (1.64, 0.29),
            GunLayoutType.SEX_2ROW: (1.64, 0.29),
            GunLayoutType.QUAD: (1.8, 0.2),
            GunLayoutType.FOUR_GUN: (1.8, 0.2),
            GunLayoutType.OCT_2ROW: (1.8, 0.2),
            GunLayoutType.QUINT: (2.0, 0.14),
            GunLayoutType.FIVE_GUN: (2.0, 0.14),
            GunLayoutType.DEC_2ROW: (2.0, 0.14),
        }[self]

    def wgt_adj(self) -> float:
        return {
            GunLayoutType.SINGLE: 1.0,
            GunLayoutType.TWIN_2ROW: 1.0,
            GunLayoutType.QUAD_4ROW: 1.0,
            GunLayoutType.TWIN: 0.75,
            GunLayoutType.TWO_GUN: 1.0,
            GunLayoutType.QUAD_2ROW: 1.0,
            GunLayoutType.TRIPLE: 0.75,
            GunLayoutType.THREE_GUN: 1.0,
            GunLayoutType.SEX_2ROW: 1.0,
            GunLayoutType.QUAD: 0.75,
            GunLayoutType.FOUR_GUN: 1.0,
            GunLayoutType.OCT_2ROW: 1.0,
            GunLayoutType.QUINT: 0.75,
            GunLayoutType.FIVE_GUN: 1.0,
            GunLayoutType.DEC_2ROW: 1.0,
        }[self]


@dataclass
class SubBattery:
    layout: GunLayoutType = GunLayoutType.SINGLE
    distribution: GunDistributionType = GunDistributionType.NONE
    above: int = 0
    on: int = 0
    below: int = 0
    two_mounts_up: bool = False
    lower_deck: bool = False

    def super_(self) -> int:
        above = self.above * (2 if self.two_mounts_up else 1)
        below = self.below * (2 if self.lower_deck else 1)
        return (above - below) * self.layout.guns_per()

    def num_mounts(self) -> int:
        return self.above + self.on + self.below

    def diameter_calc(self, diam: float) -> float:
        if diam == 0.0:
            return 0.0
        factor, power = self.layout.diameter_calc_nums()
        calc = factor * diam * (1.0 + (1.0 / diam) ** power)
        if diam < 12.0:
            calc += 12.0 / diam
        if diam > 1.0 and self.layout.wgt_adj() < 1.0:
            calc *= 0.9
        return calc

    def wgt_adj(self) -> float:
        return self.layout.wgt_adj() * float(self.num_mounts())

    def free(self, hull) -> float:
        return self.distribution.free(self.num_mounts(), hull) * float(self.num_mounts())

    @classmethod
    def from_dict(cls, data: dict) -> "SubBattery":
        """Parse a .ship battery group object."""
        return cls(
            layout=GunLayoutType.from_name(data.get("layout", "Single")),
            distribution=GunDistributionType.from_name(data.get("distribution", "None")),
            above=int(data.get("above", 0)),
            on=int(data.get("on", 0)),
            below=int(data.get("below", 0)),
            two_mounts_up=bool(data.get("two_mounts_up", False)),
            lower_deck=bool(data.get("lower_deck", False)),
        )


@dataclass
class Battery:
    units: Units = Units.IMPERIAL
    num: int = 0
    diam: Measurement = field(default_factory=lambda: _ms(0.0))
    len: float = 45.0
    year: int = 0
    shells: int = 0
    shell_wgt: Measurement | None = None
    kind: GunType = GunType.BREECH_LOADING
    mount_num: int = 0
    mount_kind: MountType = MountType.DECK
    armor_face: Measurement = field(default_factory=lambda: _ms(0.0))
    armor_back: Measurement = field(default_factory=lambda: _ms(0.0))
    armor_barb: Measurement = field(default_factory=lambda: _ms(0.0))
    groups: list[SubBattery] = field(default_factory=lambda: [SubBattery(), SubBattery()])

    CORDITE_FACTOR: float = 0.2444444

    def broad_and_below(self) -> bool:
        if self.mount_kind == MountType.BROADSIDE:
            for g in self.groups:
                if g.below != 0:
                    return True
        return False

    def concentration(self, wgt_broad: float) -> float:
        if self.mount_num == 0 or wgt_broad == 0.0:
            return 0.0
        return (self.shell_wgt_value().imp() * float(self.num) / wgt_broad) * (
            (4.0 / float(self.mount_num)) ** 0.25 - 1.0
            if self.mount_kind.wgt_adj() > 0.6
            else -0.1
        )

    def super_(self, hull) -> float:
        if self.num == 0:
            return 0.0
        s = sum(g.super_() for g in self.groups)
        free = self.free(hull)
        if free == 0.0:
            return 0.0
        return ((float(s) / float(self.num)) * rmax(self.diam.imp() * 0.6, 7.5) + free) / free

    def free(self, hull) -> float:
        if self.mount_num == 0:
            return 0.0
        return sum(g.free(hull) for g in self.groups) / float(self.mount_num)

    def armor_face_wgt(self) -> float:
        wgt = self.mount_kind.armor_face_wgt(self.armor_back.imp())
        diameter_calc = sum(g.diameter_calc(self.diam.imp()) * float(g.num_mounts()) for g in self.groups)
        return wgt * diameter_calc * self._house_hgt() * self.armor_face.imp() * Armor.INCH * self.kind.armor_face_wgt(
            self.armor_back.imp()
        )

    def _house_hgt(self) -> float:
        return rmax(7.5, 0.625 * self.diam.imp() * self.mount_kind.gunhouse_hgt_factor())

    def armor_back_wgt(self) -> float:
        shell_k, base_k = self.mount_kind.armor_back_wgt()
        shell = sum(g.diameter_calc(self.diam.imp()) * float(g.num_mounts()) for g in self.groups)
        shell *= self._house_hgt() * shell_k
        base = sum((g.diameter_calc(self.diam.imp()) / 2.0) ** 2.0 * float(g.num_mounts()) for g in self.groups)
        base *= _PI * base_k
        return (shell + base) * self.armor_back.imp() * Armor.INCH

    def armor_barb_wgt(self, hull) -> float:
        guns = sum(g.layout.guns_per() * g.num_mounts() for g in self.groups)
        if self.mount_num == 0:
            return 0.0
        if self.mount_kind.wgt_adj() > 0.5:
            a = min(4, guns // self.mount_num)
        else:
            a = guns // self.mount_num
        b = self.mount_kind.armor_barb_wgt()
        if self.free(hull) <= 0.0:
            return 0.0
        return (
            (1.0 - (float(a) - 2.0) / 6.0)
            * self.armor_barb.imp()
            * float(self.num)
            * self.diam.imp() ** 1.2
            * b
            * self.free(hull)
            / 16.0
            * self.super_(hull)
            * b
            * 2.0
            * math.sqrt(self._date_factor())
        )

    def armor_wgt(self, hull) -> float:
        return self.armor_face_wgt() + self.armor_back_wgt() + self.armor_barb_wgt(hull)

    def wgt_adj(self) -> float:
        if self.mount_num == 0:
            return 0.0
        return sum(b.wgt_adj() for b in self.groups) / float(self.mount_num)

    def _date_factor(self) -> float:
        return math.sqrt(year_adj(self.year))

    def set_shell_wgt(self, wgt: float, units: Units) -> float:
        self.shell_wgt = Measurement(wgt, UnitType.WEIGHT, units)
        return wgt

    def clear_shell_wgt(self) -> None:
        self.shell_wgt = None

    def shell_wgt_set(self) -> bool:
        return self.shell_wgt is not None

    def shell_wgt_value(self) -> Measurement:
        if self.shell_wgt is not None:
            return self.shell_wgt
        return Measurement(self.shell_wgt_est(), UnitType.WEIGHT, Units.IMPERIAL)

    def shell_wgt_est(self) -> float:
        return (
            self.diam.imp() ** 3.0
            / 1.9830943211886
            * self._date_factor()
            * (1.0 + (1.0 if self.len >= 45.0 else -1.0) * abs(45.0 - self.len) ** 0.5 / 45.0)
        )

    def gun_wgt(self) -> float:
        if self.diam.imp() == 0.0:
            return 0.0
        return (
            self.shell_wgt_est()
            * (self.len / 812.389434917877 * (1.0 + (1.0 / self.diam.imp()) ** 2.3297949327695))
            * float(self.num)
        )

    def mount_wgt(self) -> float:
        if self.diam.imp() == 0.0:
            return 0.0
        wgt = self.mount_kind.wgt() * (
            self.kind.wgt_sm() if self.mount_kind.wgt_adj() < 0.6 else self.kind.wgt_lg()
        )
        wgt = (wgt + 1.0 / self.diam.imp() ** 0.313068808543972) * self.gun_wgt()
        if self.diam.imp() > 10.0:
            wgt *= 1.0 - 2.1623769 * self.diam.imp() / 100.0
        elif self.diam.imp() <= 1.0:
            wgt = self.gun_wgt()
        return wgt * self.wgt_adj()

    def broadside_wgt(self) -> float:
        return float(self.num) * self.shell_wgt_value().imp()

    def mag_wgt(self) -> float:
        return float(self.num * self.shells) * self.shell_wgt_value().imp() / POUND2TON * (
            1.0 + self.CORDITE_FACTOR
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Battery":
        """Parse a .ship battery object."""
        from .units import Units as _Units

        ms = UnitType.LENGTH_SMALL
        shell_wgt = data.get("shell_wgt")
        return cls(
            units=_Units.from_name(data.get("units", "")),
            num=int(data.get("num", 0)),
            diam=Measurement.from_dict(data.get("diam") or {"v": 0.0}, ms),
            len=float(data.get("len", 45.0)),
            year=int(data.get("year", 0)),
            shells=int(data.get("shells", 0)),
            shell_wgt=(
                Measurement.from_dict(shell_wgt, UnitType.WEIGHT) if shell_wgt else None
            ),
            kind=GunType.from_name(data.get("kind", "BreechLoading")),
            mount_num=int(data.get("mount_num", 0)),
            mount_kind=MountType.from_name(data.get("mount_kind", "Deck")),
            armor_face=Measurement.from_dict(data.get("armor_face") or {"v": 0.0}, ms),
            armor_back=Measurement.from_dict(data.get("armor_back") or {"v": 0.0}, ms),
            armor_barb=Measurement.from_dict(data.get("armor_barb") or {"v": 0.0}, ms),
            groups=[SubBattery.from_dict(g) for g in data.get("groups", []) or []],
        )

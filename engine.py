"""Port of calc/engine.rs — Engine, FuelType, BoilerType, DriveType."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntFlag

from .utils import YEAR_MAX, rpow


class FuelType(IntFlag):
    NONE = 0
    COAL = 1 << 0
    OIL = 1 << 1
    DIESEL = 1 << 2
    GASOLINE = 1 << 3
    BATTERY = 1 << 4

    @classmethod
    def default(cls) -> "FuelType":
        return cls.OIL

    def is_steam(self) -> bool:
        return bool(self & (FuelType.COAL | FuelType.OIL))

    @classmethod
    def from_name(cls, text: str) -> "FuelType":
        """Parse bitflags serde string from .ship files ("Coal | Oil")."""
        from .utils import flags_from_str

        return flags_from_str(
            cls,
            text,
            {
                "Coal": cls.COAL,
                "Oil": cls.OIL,
                "Diesel": cls.DIESEL,
                "Gasoline": cls.GASOLINE,
                "Battery": cls.BATTERY,
            },
        )

    def __str__(self) -> str:
        s = self
        if s == FuelType.COAL:
            return "Coal fired boilers"
        if s == FuelType.OIL:
            return "Oil fired boilers"
        if s == (FuelType.COAL | FuelType.OIL):
            return "Coal and oil fired boilers"
        if s == (FuelType.COAL | FuelType.DIESEL):
            return "Coal fired boilers plus diesel motors"
        if s == (FuelType.OIL | FuelType.DIESEL):
            return "Oil fired boilers plus diesel motors"
        if s == (FuelType.COAL | FuelType.OIL | FuelType.DIESEL):
            return "Coal and oil fired boilers plus diesel motors"
        if s == FuelType.DIESEL:
            return "Diesel internal combustion motors"
        if s == (FuelType.DIESEL | FuelType.BATTERY):
            return "Diesel internal combustion engines plus batteries"
        if s == FuelType.GASOLINE:
            return "Gasoline internal combustion motors"
        if s == (FuelType.GASOLINE | FuelType.BATTERY):
            return "Gasoline internal combustion motors plus batteries"
        if s == FuelType.BATTERY:
            return "Battery powered"
        return "ERROR: Revise fuels"


class BoilerType(IntFlag):
    NONE = 0
    SIMPLE = 1 << 0
    COMPLEX = 1 << 1
    TURBINE = 1 << 2

    @classmethod
    def default(cls) -> "BoilerType":
        return cls.TURBINE

    @classmethod
    def from_name(cls, text: str) -> "BoilerType":
        """Parse bitflags serde string from .ship files ("Simple | Turbine")."""
        from .utils import flags_from_str

        return flags_from_str(
            cls, text, {"Simple": cls.SIMPLE, "Complex": cls.COMPLEX, "Turbine": cls.TURBINE}
        )

    def __str__(self) -> str:
        s = self
        if s == BoilerType.SIMPLE:
            return "simple reciprocating steam engines"
        if s == BoilerType.COMPLEX:
            return "complex reciprocating steam engines"
        if s == BoilerType.TURBINE:
            return "steam turbines"
        if s == (BoilerType.SIMPLE | BoilerType.COMPLEX):
            return "reciprocating steam engines"
        if s == (BoilerType.SIMPLE | BoilerType.TURBINE):
            return "reciprocating cruising steam engines and steam turbines"
        if s == (BoilerType.SIMPLE | BoilerType.COMPLEX | BoilerType.TURBINE):
            return "ERROR: Too many types of steam engines"
        return "ERROR: No steam engines"

    def hp_type(self) -> str:
        return "ihp" if self.is_reciprocating() else "shp"

    def num_engines(self) -> int:
        return bin(int(self)).count("1")

    def is_simple(self) -> bool:
        return bool(self & BoilerType.SIMPLE)

    def is_complex(self) -> bool:
        return bool(self & BoilerType.COMPLEX)

    def is_reciprocating(self) -> bool:
        return self.is_simple() or self.is_complex()

    def is_turbine(self) -> bool:
        return bool(self & BoilerType.TURBINE)

    def d_engine_factor(self, year: int, fuel: FuelType) -> float:
        if year < 1860:
            return 0.0
        if self.is_simple():
            if year <= 1884:
                a = 1.2 + (year - 1860) * 0.05
            elif year <= 1949:
                a = 2.45 + (year - 1885) * 0.025
            else:
                a = 4.075
        else:
            a = 0.0
        if self.is_complex():
            if year <= 1905:
                b = 1.2 + (year - 1860) * 0.05
            elif year <= 1910:
                b = 3.5 + (year - 1906)
            elif year <= 1949:
                b = 7.5 + (year - 1910) * 0.025
            else:
                b = 8.5
        else:
            b = 0.0
        if self.is_turbine() or not fuel.is_steam():
            if year <= 1897:
                c = 1.2 + (year - 1860) * 0.05
            elif year <= 1902:
                c = 1.0 + (year - 1898) * 0.5
            elif year <= 1909:
                c = 4.0 + (year - 1903)
            elif year <= 1949:
                c = 11.0 + (year - 1910) * 0.2
            else:
                c = 19.0
        else:
            c = 0.0
        return a + b + c

    def bunker_factor(self, year: int) -> float:
        y = float(year)
        if self.is_reciprocating() or y < 1898.0:
            return 1.0 - (1910.0 - y) / 70.0
        if y < 1920.0:
            return 1.0 + (y - 1910.0) / 20.0
        if y < float(YEAR_MAX):
            return 1.5 + (y - 1920.0) / 60.0
        return 2.0


class DriveType(IntFlag):
    NONE = 0
    DIRECT = 1 << 0
    GEARED = 1 << 1
    ELECTRIC = 1 << 2
    HYDRAULIC = 1 << 3

    @classmethod
    def default(cls) -> "DriveType":
        return cls.GEARED

    @classmethod
    def from_name(cls, text: str) -> "DriveType":
        """Parse bitflags serde string from .ship files ("Geared")."""
        from .utils import flags_from_str

        return flags_from_str(
            cls,
            text,
            {
                "Direct": cls.DIRECT,
                "Geared": cls.GEARED,
                "Electric": cls.ELECTRIC,
                "Hydraulic": cls.HYDRAULIC,
            },
        )

    def __str__(self) -> str:
        s = self
        if s == DriveType.DIRECT:
            return "Direct drive"
        if s == DriveType.GEARED:
            return "Geared drive"
        if s == DriveType.ELECTRIC:
            return "Electric motors"
        if s == DriveType.HYDRAULIC:
            return "Hydraulic drive"
        if s == (DriveType.GEARED | DriveType.ELECTRIC):
            return "Electric cruising motors plus geared drives"
        if s == DriveType.NONE:
            return "ERROR: No drive to shaft"
        return "ERROR: Revise drives"


@dataclass
class Engine:
    year: int = YEAR_MAX
    fuel: FuelType = field(default_factory=FuelType.default)
    boiler: BoilerType = field(default_factory=BoilerType.default)
    drive: DriveType = field(default_factory=DriveType.default)
    factor: int = 0
    vmax: float = 0.0
    vcruise: float = 0.0
    range: int = 0
    shafts: int = 0
    pct_coal: float = 0.0

    RANGE: float = 7000.0

    def set_shafts(self, shafts: int, hull) -> int:
        hull.set_shafts(shafts)
        self.shafts = shafts
        return shafts

    def hp(self, v: float, d: float, lwl: float, leff: float, cs: float, ws: float) -> float:
        if v <= 15.0:
            len_hp = lwl - (leff - lwl)
        elif v >= 25.0:
            len_hp = leff
        else:
            len_hp = (leff - lwl) * ((v - 20.0) / 5.0) + lwl
        if len_hp == 0.0:
            return 0.0
        hp = (rpow(d, 2.0 / 3.0) / len_hp * cs * v**4.0 + 0.01 * ws * v**1.83) * v / 184.1666667
        if self.year < 1890:
            hp *= 1.0 + (1890 - self.year) / 100.0
        return hp

    def hp_max(self, d: float, lwl: float, leff: float, cs: float, ws: float) -> float:
        return self.hp(self.vmax, d, lwl, leff, cs, ws)

    def hp_cruise(self, d: float, lwl: float, leff: float, cs: float, ws: float) -> float:
        return self.hp(min(self.vcruise, self.vmax), d, lwl, leff, cs, ws)

    @staticmethod
    def _rf(v: float, ws: float) -> float:
        return 0.01 * ws * v**1.83

    def rf_max(self, ws: float) -> float:
        return self._rf(self.vmax, ws)

    def rf_cruise(self, ws: float) -> float:
        return self._rf(self.vcruise, ws)

    @staticmethod
    def _rw(v: float, d: float, lwl: float, cs: float) -> float:
        if lwl == 0.0:
            return 0.0
        return rpow(d, 2.0 / 3.0) / lwl * cs * v**4.0

    def rw_max(self, d: float, lwl: float, cs: float) -> float:
        return self._rw(self.vmax, d, lwl, cs)

    def rw_cruise(self, d: float, lwl: float, cs: float) -> float:
        return self._rw(self.vcruise, d, lwl, cs)

    @staticmethod
    def _pw(rw: float, rf: float) -> float:
        if rw + rf == 0.0:
            return 0.0
        return rw / (rw + rf)

    def pw_max(self, d: float, lwl: float, cs: float, ws: float) -> float:
        return self._pw(self.rw_max(d, lwl, cs), self.rf_max(ws))

    def pw_cruise(self, d: float, lwl: float, cs: float, ws: float) -> float:
        return self._pw(self.rw_cruise(d, lwl, cs), self.rf_cruise(ws))

    def bunker(self, d: float, lwl: float, leff: float, cs: float, ws: float) -> float:
        return self.bunker_for_range(float(self.range), d, lwl, leff, cs, ws)

    def bunker_for_range(self, rng: float, d: float, lwl: float, leff: float, cs: float, ws: float) -> float:
        if self.vcruise == 0.0:
            return 0.0
        if self.boiler.bunker_factor(self.year) == 0.0:
            return 0.0
        if self.hp_cruise(d, lwl, leff, cs, ws) == 0.0:
            return 0.0
        bunker = rng / (1.0 + 0.4 * (1.0 - self.pct_coal))
        bunker = bunker / self.boiler.bunker_factor(self.year)
        return bunker / (1.8 / self.hp_cruise(d, lwl, leff, cs, ws) * self.RANGE * self.vcruise * 0.1) + d * 0.005

    def bunker_max(self, d: float, lwl: float, leff: float, cs: float, ws: float) -> float:
        return self.bunker(d, lwl, leff, cs, ws) * 1.8

    def num_engines(self) -> int:
        return self.boiler.num_engines()

    def d_engine(self, d: float, lwl: float, leff: float, cs: float, ws: float) -> float:
        factor = self.boiler.d_engine_factor(self.year, self.fuel)
        if self.year <= 1889:
            early = 1.0 + (1890 - self.year) / 100.0
        else:
            early = 1.0
        if early == 0.0:
            return 0.0
        return (self.hp_max(d, lwl, leff, cs, ws) / (factor / self.num_engines() * (1.1 - self.pct_coal / 10.0))) / early

    @classmethod
    def from_dict(cls, data: dict) -> "Engine":
        """Parse a .ship engine object."""
        return cls(
            year=int(data.get("year", 0)),
            fuel=FuelType.from_name(data.get("fuel", "")),
            boiler=BoilerType.from_name(data.get("boiler", "")),
            drive=DriveType.from_name(data.get("drive", "")),
            factor=int(data.get("factor", 0)),
            vmax=float(data.get("vmax", 0.0)),
            vcruise=float(data.get("vcruise", 0.0)),
            range=int(data.get("range", 0)),
            shafts=int(data.get("shafts", 0)),
            pct_coal=float(data.get("pct_coal", 0.0)),
        )

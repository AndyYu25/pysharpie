"""Port of calc/ship.rs — Ship numeric core (calc only).

Out of scope (not ported): convert/load/save, report, ship_type,
seakeeping_desc/type_sea and warning helpers, internals output.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .armor import Armor, BulkheadType
from .asw import ASW
from .battery import Battery, GunDistributionType
from .engine import Engine
from .hull import Hull
from .mines import Mines
from .torpedoes import Torpedoes
from .units import Measurement, Units, UnitType
from .utils import POUND2TON, YEAR_MAX, rmax, rmin, rpow, rsqrt, year_adj
from .weights import MiscWgts


@dataclass
class Ship:
    name: str = ""
    country: str = ""
    kind: str = ""
    year: int = YEAR_MAX
    trim: int = 50
    hull: Hull = field(default_factory=Hull)
    armor: Armor = field(default_factory=Armor)
    engine: Engine = field(default_factory=Engine)
    batteries: list[Battery] = field(default_factory=lambda: [Battery() for _ in range(5)])
    torps: list[Torpedoes] = field(default_factory=lambda: [Torpedoes(), Torpedoes()])
    mines: Mines = field(default_factory=Mines)
    asw: list[ASW] = field(default_factory=lambda: [ASW(), ASW()])
    wgts: MiscWgts = field(default_factory=MiscWgts)
    notes: list[str] = field(default_factory=list)
    _cached_wgt_engine: float | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        # Mirror Ship::default(): propagate ship year to sub-parts.
        # (Only applies to freshly defaulted ships; harmless otherwise
        # when callers overwrite years afterwards.)
        pass

    @classmethod
    def default(cls) -> "Ship":
        ship = cls(
            name="",
            country="",
            kind="",
            year=YEAR_MAX,
            trim=50,
            hull=Hull(),
            armor=Armor(),
            engine=Engine(),
            batteries=[Battery() for _ in range(5)],
            torps=[Torpedoes(), Torpedoes()],
            mines=Mines(),
            asw=[ASW(), ASW()],
            wgts=MiscWgts(),
            notes=[],
        )
        ship.engine.year = ship.year
        ship.mines.year = ship.year
        for b in ship.batteries:
            b.year = ship.year
        for a in ship.asw:
            a.year = ship.year
        for t in ship.torps:
            t.year = ship.year
        return ship

    @staticmethod
    def year_adj(year: int) -> float:
        return year_adj(year)

    # -- space -----------------------------------------------------------
    def deck_space(self) -> float:
        if self.hull.wp().imp() == 0.0:
            return 0.0
        space = sum(w.deck_space(self.hull.b.imp()) for w in self.torps)
        return space / self.hull.wp().imp()

    def hull_space(self) -> float:
        if self.hull.d() == 0.0:
            return 0.0
        space = sum(w.hull_space() for w in self.torps)
        return space / (self.hull.d() * Hull.FT3_PER_TON_SEA)

    # -- displacements ----------------------------------------------------
    def wgt_bunker(self) -> float:
        return self.engine.bunker(
            self.hull.d(), self.hull.lwl().imp(), self.hull.leff(), self.hull.cs(), self.hull.ws()
        )

    def wgt_load(self) -> float:
        return self.hull.d() * 0.02 + self.wgt_bunker() + self.wgt_mag()

    def d_lite(self) -> float:
        return self.hull.d() - self.wgt_load()

    def d_std(self) -> float:
        return self.hull.d() - self.wgt_bunker()

    def d_max(self) -> float:
        return self.hull.d() + 0.8 * self.wgt_bunker()

    def t_max(self) -> Measurement:
        return Measurement(self.hull.t_calc(self.d_max()), UnitType.LENGTH_LONG, Units.IMPERIAL)

    def cb_max(self) -> float:
        return self.hull.cb_calc(self.d_max(), self.t_max().imp())

    def crew_max(self) -> int:
        return int(rpow(self.hull.d(), 0.75) * 0.65)

    def crew_min(self) -> int:
        return int(float(self.crew_max()) * 0.7692)

    def vitalspace(self) -> float:
        return (1.0 - 0.65 * self.hull_room()) * 50.0 - 0.01

    def vitalspace_length(self) -> float:
        return self.hull.lwl().imp() * 0.65 * self.hull_room() + 0.01

    def _room(self) -> float:
        divisor = 1.0 - self.hull_space()
        if divisor == 0.0:
            return 0.0
        return (
            self.wgt_mag()
            + self.hull.d() * 0.02
            + self._wgt_borne() * 6.4
            + self.wgt_engine() * 3.0
            + float(self.wgts.vital)
            + float(self.wgts.hull)
        ) / (self.hull.d() * 0.94) / divisor

    def hull_room(self) -> float:
        if self.armor.bh_beam.imp() == 0.0:
            return 0.0
        factor = 1.0
        if self.armor.bulkhead.wgt(self.hull.lwl().imp(), self.hull.cwp(), self.hull.b.imp()) > 0.1:
            factor = self.hull.b.imp() / self.armor.bh_beam.imp()
        return self._room() * factor

    def deck_room(self) -> float:
        if self.crew_min() == 0:
            return 0.0
        return (
            self.hull.wp().imp()
            / Hull.FT3_PER_TON_SEA
            / 15.0
            * (1.0 - self.deck_space())
            / float(self.crew_min())
            * self.hull.freeboard.distributed()
        )

    def deck_room_quality(self) -> str:
        sp = self.deck_room()
        if sp > 1.2:
            return "Excellent"
        if sp > 0.9:
            return "Adequate"
        if sp >= 0.5:
            return "Cramped"
        return "Poor"

    def hull_room_quality(self) -> str:
        sp = self.hull_room()
        if sp < 5.0 / 6.0:
            return "Excellent"
        if sp < 1.1111112:
            return "Adequate"
        if sp <= 2.0:
            return "Cramped"
        return "Extremely poor"

    # -- cost --------------------------------------------------------------
    def cost_dollar(self) -> float:
        base = (
            (self.hull.d() - self.wgt_load()) * 0.00014
            + self.wgt_engine() * 0.00056
            + (self._wgt_borne() * 8.0) * 0.00042
        )
        if float(self.year) + 2.0 > 1914.0:
            return base * (1.0 + (float(self.year) + 1.5 - 1914.0) / 5.5)
        return base

    def cost_lb(self) -> float:
        return self.cost_dollar() / 4.0

    # -- stability / seakeeping --------------------------------------------
    def recoil(self) -> float:
        if self.hull.bb.imp() == 0.0:
            return 0.0
        denom = (
            self.stability_adj() * ((50.0 - self.steadiness()) / 150.0 + 1.0)
            if self.stability_adj() > 0.0
            else 1.0
        )
        return (
            (self.wgt_broad().imp() / self.hull.d() * self.hull.freeboard.distributed()
             * self._gun_super_factor() / self.hull.bb.imp())
            * (rpow(self.hull.d(), 1.0 / 3.0) / self.hull.bb.imp() * 3.0) ** 2.0
            * 7.0
        ) / denom

    def metacenter(self) -> Measurement:
        return Measurement(
            self.hull.b.imp() ** 1.5 * (self.stability_adj() - 0.5) / 0.5 / 200.0,
            UnitType.LENGTH_LONG,
            Units.IMPERIAL,
        )

    def _seaboat(self) -> float:
        if (
            self.hull.d() == 0.0
            or self.hull.bb.imp() == 0.0
            or self.hull.lwl().imp() == 0.0
            or self.rf_max() + self.rw_max() == 0.0
        ):
            return 0.0
        a = (
            rsqrt(self.hull.free_cap(self.cap_calc_broadside()) / (2.4 * rpow(self.hull.d(), 0.2)))
            * (
                rpow(self._stability() * 5.0 * (self.hull.bb.imp() / self.hull.lwl().imp()), 0.2)
                * rsqrt(self.hull.free_cap(self.cap_calc_broadside()) / self.hull.lwl().imp() * 20.0)
                * (
                    self.hull.d()
                    / (
                        self.hull.d()
                        + self.armor.end.wgt(self.hull.lwl().imp(), self.hull.cwp(), self.hull.b.imp()) * 3.0
                        + self._wgt_hull_plus() / 3.0
                        + (self._wgt_borne() + self.wgt_gun_armor()) * self.super_factor_long()
                    )
                )
            )
            * 8.0
        )
        if (self.hull.t.imp() / self.hull.bb.imp()) < 0.3:
            b = a * rsqrt(self.hull.t.imp() / self.hull.bb.imp() / 0.3)
        else:
            b = a
        if (self.rf_max() / (self.rf_max() + self.rw_max())) < 0.55 and self.engine.vmax > 0.0:
            c = b * (self.rf_max() / (self.rf_max() + self.rw_max())) ** 2.0
        else:
            c = b * 0.3025
        return rmin(c, 2.0)

    def seakeeping(self) -> float:
        return self._seaboat() * rmin(self.steadiness(), 50.0) / 50.0

    def roll_period(self) -> float:
        if self.metacenter().imp() == 0.0:
            return 0.0
        return 0.42 * self.hull.bb.imp() / rsqrt(self.metacenter().imp())

    def steadiness(self) -> float:
        return rmin(float(self.trim) * self._seaboat(), 100.0)

    def _stability(self) -> float:
        if self.hull.t.imp() == 0.0 or self.hull.len2beam() == 0.0:
            return 0.0
        a = (
            (self.armor.ct_fwd.wgt(self.hull.d()) + self.armor.ct_aft.wgt(self.hull.d())) * 5.0
            + (self._wgt_borne() + self.wgt_gun_armor()) * (2.0 * self._gun_super_factor() - 1.0) * 4.0
            + float(self.wgts.hull) * 2.0
            + float(self.wgts.on) * 3.0
            + float(self.wgts.above) * 4.0
            + self.armor.upper.wgt(self.hull.d(), self.hull.cwp(), self.hull.b.imp()) * 2.0
            + self.armor.main.wgt(self.hull.d(), self.hull.cwp(), self.hull.b.imp())
            + self.armor.end.wgt(self.hull.d(), self.hull.cwp(), self.hull.b.imp())
            + self.deck_wgt()
            + (self._wgt_hull_plus() + self.wgt_guns() + self._wgt_gun_mounts() - self._wgt_borne())
            * 1.5
            * self.hull.freeboard.average().imp()
            / self.hull.t.imp()
        )
        if self.deck_room() < 1.0:
            b = a + (self.wgt_engine() + float(self.wgts.vital) + float(self.wgts.void)) * (
                1.0 - self.deck_room() ** 2.0
            )
        else:
            b = a
        if b > 0.0:
            return (
                rsqrt((self.hull.d() * (self.hull.bb.imp() / self.hull.t.imp()) / b) * 0.5)
                * rpow(8.76755 / self.hull.len2beam(), 0.25)
            )
        return b

    def stability_adj(self) -> float:
        return self._stability() * ((50.0 - float(self.trim)) / 150.0 + 1.0)

    def d_factor(self) -> float:
        divisor = (
            self.engine.d_engine(
                self.hull.d(), self.hull.lwl().imp(), self.hull.leff(), self.hull.cs(), self.hull.ws()
            )
            + 8.0 * self._wgt_borne()
            + self.wgt_armor()
            + float(self.wgts.wgt())
        )
        if divisor == 0.0:
            return 0.0
        return rmin(self.hull.d() / divisor, 10.0)

    def cap_calc_broadside(self) -> bool:
        return any(b.broad_and_below() for b in self.batteries)

    # -- survivability / strength -------------------------------------------
    def flotation(self) -> Measurement:
        if self._room() == 0.0:
            return Measurement(0.0, UnitType.WEIGHT, Units.IMPERIAL)
        if self.cap_calc_broadside():
            a = self.hull.free_cap(self.cap_calc_broadside())
        else:
            a = self.hull.freeboard.distributed()
        b = (a * self.hull.wp().imp() / Hull.FT3_PER_TON_SEA + self.hull.d()) / 2.0
        sa = self.stability_adj()
        c = b * (rsqrt(sa) if sa > 1.0 else sa**4.0)
        d = c * (self.str_comp() if self.str_comp() < 1.0 else 1.0)
        e = d / self._room() ** (2.0 if self._room() > 1.0 else 1.0)
        return Measurement(rmax(e * self.year_adj(self.year), 0.0), UnitType.WEIGHT, Units.IMPERIAL)

    def str_cross(self) -> float:
        concentration = 1.0
        if self.wgt_broad().imp() > 0.0:
            concentration = 1.0 + self._gun_concentration()
        a = rsqrt(self.hull.bb.imp() * (self.hull.t.imp() + self.hull.freeboard.distributed()))
        b = (
            self.hull.d()
            + (
                (
                    self.wgt_broad().imp()
                    + self._wgt_borne()
                    + self.wgt_gun_armor()
                    + self.armor.ct_fwd.wgt(self.hull.d())
                    + self.armor.ct_aft.wgt(self.hull.d())
                )
                * (concentration * self._gun_super_factor())
                + rmax(self.hp_max().imp(), 0.0) / 100.0
            )
        ) / self.hull.d()
        if a == 0.0 or b == 0.0:
            return 0.0
        s = self.wgt_struct().imp() / a / b * 0.6
        if self.year < 1900:
            s *= 1.0 - (1900.0 - float(self.year)) / 100.0
        return s

    def str_long(self) -> float:
        divisor = self.hull.t.imp() + self.hull.free_cap(self.cap_calc_broadside())
        if divisor == 0.0:
            return 0.0
        a = (self.hull.lwl().imp() / divisor) ** 2.0 * (
            self.hull.d()
            + self.armor.end.wgt(self.hull.lwl().imp(), self.hull.cwp(), self.hull.b.imp()) * 3.0
            + (self._wgt_borne() + self.wgt_gun_armor()) * self.super_factor_long() * 2.0
        )
        if a == 0.0:
            return 0.0
        if self.armor.bh_kind is BulkheadType.ADDITIONAL:
            top = self._wgt_hull_plus() + self.armor.bulkhead.wgt(
                self.hull.lwl().imp(), self.hull.cwp(), self.hull.b.imp()
            )
        else:
            top = self._wgt_hull_plus()
        # NOTE: Rust uses u32 integer division here: 1 - (1900 - year) / 100.
        pre1900 = 1 - (1900 - self.year) // 100 if self.year < 1900 else 1
        return top / a * 850.0 * float(pre1900)

    def str_comp(self) -> float:
        if self.str_long() == 0.0 or self.str_cross() == 0.0:
            return 0.0
        if self.str_cross() > self.str_long():
            return self.str_long() * (self.str_cross() / self.str_long()) ** 0.25
        return self.str_cross() * (self.str_long() / self.str_cross()) ** 0.1

    def _gun_concentration(self) -> float:
        return sum(b.concentration(self.wgt_broad().imp()) for b in self.batteries)

    def damage_shell_size(self) -> Measurement:
        if self.batteries[0].diam.imp() > 0.0:
            return self.batteries[0].diam
        return Measurement(6.0, UnitType.LENGTH_SMALL, Units.IMPERIAL)

    def damage_shell_num(self) -> float:
        if self.year_adj(self.year) == 0.0:
            return 0.0
        return self.flotation().imp() / (
            self.damage_shell_size().imp() ** 3.0 / 2.0 * self.year_adj(self.year)
        )

    def damage_torp_size(self) -> Measurement:
        size = self.torps[0].diam.imp() if self.torps[0].wgt_weaps() > 0.0 else 20.0
        return Measurement(size, UnitType.LENGTH_SMALL, Units.IMPERIAL)

    def damage_torp_num(self) -> float:
        if (
            self.hull.lwl().imp() == 0.0
            or self.hull.t.imp() == 0.0
            or (self.hull.t.imp() + self.hull.t.imp()) == 0.0
            or self._room() == 0.0
            or self.torps[0].num == 0
            or self.torps[0].wgt_weaps() == 0.0
        ):
            return 0.0
        inner = (
            rpow(self.flotation().imp() / 10_000.0, 1.0 / 3.0)
            + (self.hull.bb.imp() / 75.0) ** 2.0
            + rpow(
                (self.armor.bulkhead.thick.imp() / 2.0 * self.armor.bulkhead.len.imp() / self.hull.lwl().imp())
                / 0.65
                * self.armor.bulkhead.hgt.imp()
                / self.hull.t.imp(),
                1.0 / 3.0,
            )
            * self.flotation().imp()
            / 35_000.0
            * self.hull.bb.imp()
            / 50.0
        ) / self._room() * self.hull.lwl().imp() / (self.hull.lwl().imp() + self.hull.bb.imp())
        if self.stability_adj() < 1.0:
            inner *= self.stability_adj() ** 4.0
        inner *= 1.0 - self.hull_space()
        if self.torps[0].wgt_weaps() > 0.0:
            inner *= 1.313 / (self.torps[0].wgt_weaps() / float(self.torps[0].num))
        return inner

    # -- weights -------------------------------------------------------------
    def wgt_engine(self) -> float:
        if self._cached_wgt_engine is not None:
            return self._cached_wgt_engine
        TOLERANCE = 0.05
        MAX_ITER = 50
        prev = 0.0
        for _ in range(MAX_ITER):
            self._cached_wgt_engine = prev
            if 600.0 <= self.hull.d() < 5000.0 and self.d_factor() < 1.0:
                p = 1.0 - self.hull.d() / 5000.0
            elif self.hull.d() < 600.0 and self.d_factor() < 1.0:
                p = 0.88
            else:
                p = 0.0
            new = (
                self.engine.d_engine(
                    self.hull.d(),
                    self.hull.lwl().imp(),
                    self.hull.leff(),
                    self.hull.cs(),
                    self.hull.ws(),
                )
                / 2.0
            ) * self.d_factor() ** p
            if abs(new - prev) < TOLERANCE:
                self._cached_wgt_engine = prev
                return new
            prev = new
        self._cached_wgt_engine = prev
        return prev

    def wgt_struct(self) -> Measurement:
        divisor = (
            self.hull.ws()
            + 2.0 * self.hull.lwl().imp() * self.hull.free_cap(self.cap_calc_broadside())
            + self.hull.wp().imp()
        )
        if divisor == 0.0:
            return Measurement(0.0, UnitType.WEIGHT_PER_AREA, Units.IMPERIAL)
        if self.armor.bh_kind is BulkheadType.ADDITIONAL:
            extra = self.armor.bulkhead.wgt(self.hull.lwl().imp(), self.hull.cwp(), self.hull.b.imp())
        else:
            extra = 0.0
        return Measurement(
            (self._wgt_hull_plus() + extra) * POUND2TON / divisor,
            UnitType.WEIGHT_PER_AREA,
            Units.IMPERIAL,
        )

    def wgt_hull(self) -> float:
        return (
            self.hull.d()
            - self.wgt_guns()
            - self._wgt_gun_mounts()
            - self._wgt_weaps()
            - self.wgt_armor()
            - self.wgt_engine()
            - self.wgt_load()
            - float(self.wgts.wgt())
        )

    def _wgt_hull_plus(self) -> float:
        return self.wgt_hull() + self.wgt_guns() + self._wgt_gun_mounts() - self._wgt_borne()

    def _wgt_borne(self) -> float:
        return sum(b.gun_wgt() * b.mount_kind.wgt_adj() for b in self.batteries) * 2.0

    def _wgt_weaps(self) -> float:
        wgt = sum(w.wgt() for w in self.torps)
        wgt += sum(w.wgt_all() for w in self.asw)
        wgt += self.mines.wgt_all()
        return wgt

    def wgt_guns(self) -> float:
        return sum(b.gun_wgt() for b in self.batteries)

    def _wgt_gun_mounts(self) -> float:
        return sum(b.mount_wgt() for b in self.batteries)

    def wgt_gun_armor(self) -> float:
        return sum(b.armor_wgt(self.hull) for b in self.batteries)

    def wgt_mag(self) -> float:
        return sum(b.mag_wgt() for b in self.batteries)

    def wgt_broad(self) -> Measurement:
        return Measurement(
            sum(b.broadside_wgt() for b in self.batteries), UnitType.WEIGHT, Units.IMPERIAL
        )

    def wgt_armor(self) -> float:
        return self.armor.wgt(self.hull, self.wgt_mag(), self.wgt_engine()) + self.wgt_gun_armor()

    def _gun_wtf(self) -> float:
        wtf = 0.0
        for b in self.batteries:
            if b.diam.imp() == 0.0:
                continue
            wtf += (b.gun_wgt() + b.mount_wgt() + b.armor_wgt(self.hull)) * b.super_(
                self.hull
            ) * b.mount_kind.wgt_adj()
        return wtf

    def _gun_super_factor(self) -> float:
        if self.wgt_gun_armor() + self.wgt_guns() + self._wgt_gun_mounts() == 0.0:
            return 0.0
        return self._gun_wtf() / (self.wgt_gun_armor() + self.wgt_guns() + self._wgt_gun_mounts())

    def super_factor_long(self) -> float:
        b0 = self.batteries[0]
        if (
            b0.groups[0].distribution in (GunDistributionType.CENTERLINE_EVEN, GunDistributionType.SIDES_EVEN)
            or b0.groups[1].distribution
            in (GunDistributionType.CENTERLINE_EVEN, GunDistributionType.SIDES_EVEN)
        ) and (b0.mount_num == 3 or b0.mount_num == 4):
            a = self.hull_room() * self._gun_super_factor()
        else:
            a = self.hull_room() * 1.0
        g0, g1 = b0.groups[0], b0.groups[1]
        if (
            (g0.num_mounts() > 0 and g1.num_mounts() == 0 and g0.distribution.super_factor_long())
            or (g1.num_mounts() > 0 and g0.num_mounts() == 0 and g1.distribution.super_factor_long())
            or (
                g0.num_mounts() > 0
                and g1.num_mounts() > 0
                and abs(
                    g0.distribution.g1_gun_position(
                        self.hull.freeboard.fd_len, self.hull.freeboard.ad_len()
                    )
                    - g1.distribution.g2_gun_position(
                        self.hull.freeboard.fd_len, self.hull.freeboard.ad_len()
                    )
                )
                < 0.2
            )
        ):
            return a * (0.8 * self._gun_super_factor())
        return a * (2.0 * self._gun_super_factor() - 1.0)

    # -- engine/hull convenience wrappers --------------------------------------
    def deck_wgt(self) -> float:
        return self.armor.deck.wgt(self.hull, self.wgt_mag(), self.wgt_engine())

    def hp_max(self) -> Measurement:
        return Measurement(
            self.engine.hp_max(
                self.hull.d(), self.hull.lwl().imp(), self.hull.leff(), self.hull.cs(), self.hull.ws()
            ),
            UnitType.POWER,
            Units.IMPERIAL,
        )

    def hp_cruise(self) -> float:
        return self.engine.hp_cruise(
            self.hull.d(), self.hull.lwl().imp(), self.hull.leff(), self.hull.cs(), self.hull.ws()
        )

    def rf_max(self) -> float:
        return self.engine.rf_max(self.hull.ws())

    def rf_cruise(self) -> float:
        return self.engine.rf_cruise(self.hull.ws())

    def rw_max(self) -> float:
        return self.engine.rw_max(self.hull.d(), self.hull.lwl().imp(), self.hull.cs())

    def rw_cruise(self) -> float:
        return self.engine.rw_cruise(self.hull.d(), self.hull.lwl().imp(), self.hull.cs())

    def pw_max(self) -> float:
        return self.engine.pw_max(self.hull.d(), self.hull.lwl().imp(), self.hull.cs(), self.hull.ws())

    def pw_cruise(self) -> float:
        return self.engine.pw_cruise(
            self.hull.d(), self.hull.lwl().imp(), self.hull.cs(), self.hull.ws()
        )

    def d_engine(self) -> float:
        return self.engine.d_engine(
            self.hull.d(), self.hull.lwl().imp(), self.hull.leff(), self.hull.cs(), self.hull.ws()
        )

    def bunker_max(self) -> float:
        return self.engine.bunker_max(
            self.hull.d(), self.hull.lwl().imp(), self.hull.leff(), self.hull.cs(), self.hull.ws()
        )

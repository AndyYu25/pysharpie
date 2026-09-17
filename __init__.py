"""Python port of the Rust `calc` module — numeric core only.

Mirrors calc/mod.rs re-exports (minus report/IO/SVG which are out of scope):
YEAR_MIN/YEAR_MAX, units, weights, freeboard, hull, engine, armor,
battery, torpedoes, mines, asw, ship, utils.
"""
from .armor import Armor, Belt, BeltType, BulkheadType, CT, Deck, DeckType
from .asw import ASW, ASWType
from .battery import (
    Battery,
    GunDistributionType,
    GunLayoutType,
    GunType,
    MountType,
    SubBattery,
)
from .engine import BoilerType, DriveType, Engine, FuelType
from .freeboard import Freeboard
from .hull import BowType, Displacement, Hull, Length, SternType
from .mines import Mines, MineType
from .ship import Ship
from .torpedoes import TorpedoMountType, Torpedoes
from .units import Measurement, Units, UnitType
from .utils import POUND2TON, YEAR_MAX, YEAR_MIN, num, pct, plural, rmax, rmin, rpow, rsqrt, to_place, year_adj
from .weights import MiscWgts

__all__ = [
    "Armor",
    "Belt",
    "BeltType",
    "BulkheadType",
    "CT",
    "Deck",
    "DeckType",
    "ASW",
    "ASWType",
    "Battery",
    "GunDistributionType",
    "GunLayoutType",
    "GunType",
    "MountType",
    "SubBattery",
    "BoilerType",
    "DriveType",
    "Engine",
    "FuelType",
    "Freeboard",
    "BowType",
    "Displacement",
    "Hull",
    "Length",
    "SternType",
    "Mines",
    "MineType",
    "Ship",
    "TorpedoMountType",
    "Torpedoes",
    "Measurement",
    "Units",
    "UnitType",
    "MiscWgts",
    "POUND2TON",
    "YEAR_MAX",
    "YEAR_MIN",
    "num",
    "pct",
    "plural",
    "rmin",
    "rmax",
    "rpow",
    "rsqrt",
    "to_place",
    "year_adj",
]


def test_ship() -> Ship:
    """Mirror of calc/mod.rs test_support::test_ship()."""
    from .hull import Hull as _Hull

    hull = _Hull()
    hull.set_lwl(100.0, Units.IMPERIAL)
    hull.set_d(1000.0)
    hull.b = Measurement(50.0, UnitType.LENGTH_LONG, Units.IMPERIAL)
    hull.bb = Measurement(hull.b.imp(), UnitType.LENGTH_LONG, Units.IMPERIAL)
    hull.t = Measurement(10.0, UnitType.LENGTH_LONG, Units.IMPERIAL)
    hull.freeboard.fc_len = 0.2
    hull.freeboard.fc_fwd = Measurement(10.0, UnitType.LENGTH_LONG, Units.IMPERIAL)
    hull.freeboard.fc_aft = hull.freeboard.fc_fwd
    hull.freeboard.fd_len = 0.3
    hull.freeboard.fd_fwd = hull.freeboard.fc_fwd
    hull.freeboard.fd_aft = hull.freeboard.fc_fwd
    hull.freeboard.ad_fwd = hull.freeboard.fc_fwd
    hull.freeboard.ad_aft = hull.freeboard.fc_fwd
    hull.freeboard.qd_len = 0.15
    hull.freeboard.qd_fwd = hull.freeboard.fc_fwd
    hull.freeboard.qd_aft = hull.freeboard.fc_fwd

    engine = Engine()
    engine.set_shafts(2, hull)
    engine.year = 1920
    engine.fuel = FuelType.OIL
    engine.boiler = BoilerType.TURBINE
    engine.drive = DriveType.GEARED
    engine.vmax = 30.0
    engine.vcruise = 20.0
    engine.range = 10000

    ship = Ship.default()
    ship.hull = hull
    ship.engine = engine
    return ship

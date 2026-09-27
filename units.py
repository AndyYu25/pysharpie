"""Port of calc/units.rs — Units, UnitType, Measurement (calc core only)."""
from __future__ import annotations

from enum import Enum


class Units(Enum):
    IMPERIAL = 0
    METRIC = 1

    @classmethod
    def default(cls) -> "Units":
        return cls.IMPERIAL

    @classmethod
    def from_str(cls, index: str) -> "Units":
        # Rust: "1" => Metric, everything else ("0", unknown) => Imperial
        return cls.METRIC if index == "1" else cls.IMPERIAL

    @classmethod
    def from_int(cls, index: int) -> "Units":
        return cls.from_str(str(index))

    def to_int(self) -> int:
        return self.value

    @classmethod
    def from_name(cls, name: str) -> "Units":
        """Parse serde variant name from .ship files ("Imperial"/"Metric")."""
        return cls.METRIC if str(name).strip() == "Metric" else cls.IMPERIAL


class UnitType(Enum):
    LENGTH_SMALL = "LengthSmall"
    LENGTH_LONG = "LengthLong"
    AREA = "Area"
    WEIGHT = "Weight"
    POWER = "Power"
    WEIGHT_PER_AREA = "WeightPerArea"

    INCH2MM = 25.4
    FEET2METERS = 0.3048
    SQFEET2SQMETERS = 0.09290304
    POUND2KG = 0.45359237
    HP2KW = 0.74569987

    def imperial_to_metric(self) -> float:
        if self is UnitType.LENGTH_SMALL:
            return 25.4
        if self is UnitType.LENGTH_LONG:
            return 0.3048
        if self is UnitType.AREA:
            return 0.09290304
        if self is UnitType.WEIGHT:
            return 0.45359237
        if self is UnitType.POWER:
            return 0.74569987
        if self is UnitType.WEIGHT_PER_AREA:
            return 0.45359237 / 0.09290304
        raise ValueError(f"unknown UnitType {self}")

    def _labels(self) -> tuple[str, ...]:
        return {
            UnitType.LENGTH_SMALL: ("in", "mm"),
            UnitType.LENGTH_LONG: ("ft", "m"),
            UnitType.AREA: ("sq ft", "sq m"),
            UnitType.WEIGHT: ("lbs", "kg"),
            UnitType.POWER: ("hp", "kW"),
            UnitType.WEIGHT_PER_AREA: ("lbs/sq ft", "kg/sq m"),
        }[self]

    def all_labels(self) -> list[str]:
        return list(self._labels())

    def from_index(self, index: int) -> str:
        labels = self._labels()
        if 0 <= index < len(labels):
            return labels[index]
        return labels[0]


class Measurement:
    """Dual imperial/metric value. Port of calc/units.rs Measurement."""

    __slots__ = ("imp_v", "metric_v", "units", "factor")

    def __init__(self, v: float, unit_type: UnitType, units: Units):
        factor = unit_type.imperial_to_metric()
        if units is Units.IMPERIAL:
            imp_v, metric_v = float(v), float(v) * factor
        else:
            imp_v, metric_v = float(v) / factor, float(v)
        self.imp_v = imp_v
        self.metric_v = metric_v
        self.units = units
        self.factor = factor

    @classmethod
    def _raw(cls, imp_v: float, metric_v: float, units: Units, factor: float) -> "Measurement":
        obj = cls.__new__(cls)
        obj.imp_v = imp_v
        obj.metric_v = metric_v
        obj.units = units
        obj.factor = factor
        return obj

    def metric(self) -> float:
        return self.metric_v

    def imp(self) -> float:
        return self.imp_v

    def set_units(self, u: Units) -> None:
        self.units = u

    @classmethod
    def from_dict(cls, data: dict, unit_type: UnitType) -> "Measurement":
        """Parse a .ship measure `{"v": ..., "units": ..., "factor": ...}`.

        `v` is in the stated units for the given unit type; the stored
        factor is ignored and recomputed (mirrors Measurement::new).
        """
        return cls(float(data.get("v", 0.0)), unit_type, Units.from_name(data.get("units", "")))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Measurement):
            return NotImplemented
        return (
            self.imp_v == other.imp_v
            and self.metric_v == other.metric_v
            and self.units == other.units
            and self.factor == other.factor
        )

    def __repr__(self) -> str:
        return f"Measurement(imp={self.imp_v!r}, metric={self.metric_v!r}, units={self.units})"

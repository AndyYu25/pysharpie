"""Port of calc/freeboard.rs — Freeboard."""
from __future__ import annotations

from dataclasses import dataclass

from .units import Measurement, Units, UnitType


@dataclass
class Freeboard:
    fc_len: float = 0.2
    fc_fwd: Measurement = None  # type: ignore[assignment]
    fc_aft: Measurement = None  # type: ignore[assignment]
    fd_len: float = 0.3
    fd_fwd: Measurement = None  # type: ignore[assignment]
    fd_aft: Measurement = None  # type: ignore[assignment]
    ad_fwd: Measurement = None  # type: ignore[assignment]
    ad_aft: Measurement = None  # type: ignore[assignment]
    qd_len: float = 0.15
    qd_fwd: Measurement = None  # type: ignore[assignment]
    qd_aft: Measurement = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        def _m(v: Measurement | None) -> Measurement:
            return v if v is not None else Measurement(0.0, UnitType.LENGTH_LONG, Units.IMPERIAL)

        self.fc_fwd = _m(self.fc_fwd)
        self.fc_aft = _m(self.fc_aft)
        self.fd_fwd = _m(self.fd_fwd)
        self.fd_aft = _m(self.fd_aft)
        self.ad_fwd = _m(self.ad_fwd)
        self.ad_aft = _m(self.ad_aft)
        self.qd_fwd = _m(self.qd_fwd)
        self.qd_aft = _m(self.qd_aft)

    def ad_len(self) -> float:
        return 1.0 - self.fc_len - self.fd_len - self.qd_len

    def fc(self) -> float:
        return self.fc_aft.imp() + (self.fc_fwd.imp() - self.fc_aft.imp()) * 0.4

    def fd(self) -> float:
        return self.fd_fwd.imp() + (self.fd_aft.imp() - self.fd_fwd.imp()) * 0.5

    def ad(self) -> float:
        return self.ad_fwd.imp() + (self.ad_aft.imp() - self.ad_fwd.imp()) * 0.5

    def qd(self) -> float:
        return self.qd_fwd.imp() + (self.qd_aft.imp() - self.qd_fwd.imp()) * 0.5

    def average(self) -> Measurement:
        return Measurement(
            self.fc() * self.fc_len
            + self.fd() * self.fd_len
            + self.ad() * self.ad_len()
            + self.qd() * self.qd_len,
            UnitType.LENGTH_LONG,
            Units.IMPERIAL,
        )

    def distributed(self) -> float:
        denom = self.fd_len + self.ad_len()
        if denom == 0.0:
            return 0.0
        return (self.fd() * self.fd_len + self.ad() * self.ad_len()) / denom

    @classmethod
    def from_dict(cls, data: dict) -> "Freeboard":
        """Parse flat .ship hull fields (freeboard is inlined in the file)."""
        ml = UnitType.LENGTH_LONG

        def get(key: str) -> Measurement:
            return Measurement.from_dict(data.get(key) or {"v": 0.0}, ml)

        return cls(
            fc_len=float(data.get("fc_len", 0.0)),
            fc_fwd=get("fc_fwd"),
            fc_aft=get("fc_aft"),
            fd_len=float(data.get("fd_len", 0.0)),
            fd_fwd=get("fd_fwd"),
            fd_aft=get("fd_aft"),
            ad_fwd=get("ad_fwd"),
            ad_aft=get("ad_aft"),
            qd_len=float(data.get("qd_len", 0.0)),
            qd_fwd=get("qd_fwd"),
            qd_aft=get("qd_aft"),
        )

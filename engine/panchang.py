"""Panchang calculations scaffolding.

Will compute:
- Tithi (Krishna/Shukla, Trayodashi/Chaturdashi/Ashtami)
- Paksha
- Yoga
- Karana
- Lunar month and Magha Shukla Ashtami

NOTE: Current repo has only nakshatra/yoga/dignity/yogas.
This module is added to support chronology search.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PanchangResult:
    tithi: str
    paksha: str
    yoga: str
    karana: str
    lunar_month: str
    details: Dict[str, Any]


def compute_panchang(*, jd: float, sun_sidereal_lon: float, moon_sidereal_lon: float) -> PanchangResult:
    """Compute Panchang elements from sidereal longitudes.

    This is scaffolding; real algorithm must be implemented.
    """
    # TODO: implement tithi based on Moon-Sun elongation and paksha boundaries.
    # TODO: implement yoga based on (Sun+Moon) sidereal sum.
    # TODO: implement karana from half-tithi.
    # TODO: implement month from Sun sign and identify Magha Shukla Ashtami.
    raise NotImplementedError("Panchang computation not implemented yet")


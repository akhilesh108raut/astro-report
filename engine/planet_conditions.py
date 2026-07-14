"""Planetary condition helpers for exact nakshatra/pada and anchor distances."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def angular_distance_arcmin(lon1_deg: float, lat1_deg: float, lon2_deg: float, lat2_deg: float) -> float:
    """Angular distance between two points on the sky in arcminutes.

    Placeholder.
    """
    raise NotImplementedError


def is_lon_in_nakshatra_exact(
    *,
    planet_sidereal_lon: float,
    target_nakshatra: str,
    target_pada: int,
    nakshatra_exact_tolerance_arcmin: float,
) -> bool:
    """Return True if planet longitude lies within tolerance of the target nakshatra/pada region."""
    raise NotImplementedError


def is_planet_in_exact_nakshatra_and_pada(*, planet: str, planet_lon: float, **kwargs: Any) -> bool:
    """Convenience wrapper."""
    return is_lon_in_nakshatra_exact(planet_sidereal_lon=planet_lon, **kwargs)


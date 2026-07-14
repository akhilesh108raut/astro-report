"""Ephemeris backend interface.

Goal: provide Swiss Ephemeris / JPL DE440/DE431 accuracy for chronology.

Current repo uses `ephem` in engine/ephemeris.py. This module adds optional
backends while keeping `ephem` as fallback.

Scaffolding only: actual integrations come after deps are installed/validated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional


class EphemerisBackend:
    name: str = "base"

    def planet_sidereal_longitudes(self, jd: float, lat: float, lon: float) -> Dict[str, float]:
        """Return sidereal longitudes (0-360) for Sun..Saturn and Rahu/Ketu."""
        raise NotImplementedError

    def retrograde_flags(self, jd: float, lat: float, lon: float) -> Dict[str, bool]:
        """Return retrograde flags for the 7 classical planets (and optionally nodes)."""
        raise NotImplementedError

    def eclipse_search(self, jd_start: float, jd_end: float) -> list[dict]:
        """Return raw eclipse candidates/events."""
        raise NotImplementedError


class EphemBackend(EphemerisBackend):
    name = "ephem"

    def __init__(self, ephem_module=None):
        import ephem as _ephem
        self._ephem = ephem_module or _ephem

    def planet_sidereal_longitudes(self, jd: float, lat: float, lon: float) -> Dict[str, float]:
        # TODO: call existing engine/ephemeris functions. For now, not wired.
        raise NotImplementedError

    def retrograde_flags(self, jd: float, lat: float, lon: float) -> Dict[str, bool]:
        raise NotImplementedError

    def eclipse_search(self, jd_start: float, jd_end: float) -> list[dict]:
        raise NotImplementedError


def get_backend(preferred: str = "swiss") -> EphemerisBackend:
    """Select backend.

    preferred: "swiss" | "jpl" | "ephem"
    """
    # TODO: implement Swiss/JPL detection.
    return EphemBackend()


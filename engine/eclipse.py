"""Eclipse detection scaffolding.

Will detect:
- solar eclipses
- lunar eclipses
- pairs separated by 13/14/15 days

NOTE: requires accurate new/full moon (syzygy) computations and eclipse
conditions (node alignment). This module is added as a scaffold.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class EclipseEvent:
    jd: float
    kind: str  # "solar" | "lunar"
    details: Dict[str, Any]


def find_eclipses_in_window(*, jd_start: float, jd_end: float) -> List[EclipseEvent]:
    """Find eclipses within [jd_start, jd_end]."""
    raise NotImplementedError


def has_eclipse_pair_separated_by(*, eclipse_events: List[EclipseEvent], days: int, tolerance_days: float = 0.75) -> bool:
    """Check if any pair of eclipse events are separated by `days` (± tolerance)."""
    raise NotImplementedError


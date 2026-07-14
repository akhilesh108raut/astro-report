"""Star proper-motion ordering utilities.

Target checks:
- Arundhati precedes Vasistha
- RA(Alcor) > RA(Mizar)
- EclipticLongitude(Alcor) > EclipticLongitude(Mizar)

This requires:
- mapping of Arundhati and Vasistha to actual star IDs
- proper motion propagation from catalog epoch to candidate epochs

Scaffolding only; concrete star mapping + constants are TODO.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple


@dataclass
class Star:
    name: str
    ra0_deg: float
    dec0_deg: float
    pm_ra_mas_per_yr: float
    pm_dec_mas_per_yr: float
    ref_epoch_jd: float


def propagate_star(*, star: Star, jd: float) -> Tuple[float, float]:
    """Propagate a star's RA/Dec by proper motion (scaffolding).

    Returns (ra_deg, dec_deg).
    """
    raise NotImplementedError


def arundhati_precedes_vasistha(*, jd: float) -> bool:
    """Check Arundhati precedes Vasistha using propagated positions.

    Precedes is defined by your objective; currently left as TODO.
    """
    raise NotImplementedError


def alcor_mizar_ordering(*, jd: float) -> Dict[str, Any]:
    """Return RA and ecliptic longitude ordering checks for Alcor/Mizar."""
    raise NotImplementedError


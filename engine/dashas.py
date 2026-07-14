"""
Vimshottari Dasha calculation.
Based on Moon's nakshatra at birth.
"""

from datetime import datetime, timedelta
from .constants import (
    NAKSHATRAS, NAKSHATRA_DASHA_LORD, DASHA_LORDS, DASHA_YEARS, DASHA_CYCLE
)


def get_dasha_balance(moon_lon: float, birth_date: datetime, query_date: datetime = None) -> dict:
    """
    Calculates mahadasha, antardasha, and remaining balance at query_date.
    If query_date is None, uses birth_date (for showing dasha at birth).
    If query_date is provided, shows current dasha (for readings at any point in time).
    Returns active dashas at query_date and next 5 mahadashas.
    """
    if query_date is None:
        query_date = birth_date

    nak_span = 360 / 27  # 13.3333°
    nak_index = int(moon_lon // nak_span) % 27
    fraction_elapsed = (moon_lon % nak_span) / nak_span

    # Starting dasha lord
    start_lord = NAKSHATRA_DASHA_LORD[nak_index]
    lord_index = DASHA_LORDS.index(start_lord)

    # Years elapsed in first dasha at birth
    total_years = DASHA_YEARS[start_lord]
    elapsed_years = total_years * fraction_elapsed

    # Build timeline of dashas from birth (backward to cycle start, then forward)
    dashas = []
    cycle_start = birth_date - timedelta(days=elapsed_years * 365.25)

    # Build 15 mahadashas to ensure we cover any reasonable query date (450 years)
    for i in range(15):
        lord = DASHA_LORDS[(lord_index + i) % 9]
        years = DASHA_YEARS[lord] if i > 0 else total_years
        start = cycle_start if i == 0 else dashas[-1]["end"]
        end = start + timedelta(days=years * 365.25)
        dashas.append({"lord": lord, "years": years, "start": start, "end": end})

    # Find active mahadasha at query_date
    active_maha = next(
        (d for d in dashas if d["start"] <= query_date <= d["end"]),
        dashas[0]  # fallback to first if somehow outside range
    )

    # Build antardasha within active mahadasha
    maha_lord = active_maha["lord"]
    maha_lord_idx = DASHA_LORDS.index(maha_lord)
    maha_total_years = DASHA_YEARS[maha_lord]
    maha_start = active_maha["start"]

    antardashas = []
    for j in range(9):
        antar_lord = DASHA_LORDS[(maha_lord_idx + j) % 9]
        antar_fraction = DASHA_YEARS[antar_lord] / DASHA_CYCLE
        antar_years = maha_total_years * antar_fraction
        a_start = maha_start if j == 0 else antardashas[-1]["end"]
        a_end = a_start + timedelta(days=antar_years * 365.25)
        antardashas.append({"lord": antar_lord, "start": a_start, "end": a_end})

    active_antar = next(
        (a for a in antardashas if a["start"] <= query_date <= a["end"]),
        antardashas[0]
    )

    return {
        "mahadasha": maha_lord,
        "mahadasha_end": active_maha["end"].strftime("%Y-%m-%d"),
        "antardasha": active_antar["lord"],
        "antardasha_end": active_antar["end"].strftime("%Y-%m-%d"),
        "upcoming_dashas": [
            {"lord": d["lord"], "start": d["start"].strftime("%Y-%m-%d"),
             "end": d["end"].strftime("%Y-%m-%d")}
            for d in dashas[dashas.index(active_maha):dashas.index(active_maha)+5]
        ]
    }

"""
Vedic chart calculations: signs, houses, nakshatras, dignity.
"""

from .constants import (
    SIGNS, SIGN_LORDS, NAKSHATRAS, EXALTATION, DEBILITATION, OWN_SIGNS,
    PLANET_NAMES
)


def longitude_to_sign(lon: float) -> tuple[str, float]:
    """Returns (sign_name, degree_within_sign) for a sidereal longitude."""
    sign_index = int(lon // 30)
    degree_in_sign = lon % 30
    return SIGNS[sign_index], round(degree_in_sign, 4)


def longitude_to_nakshatra(lon: float) -> tuple[str, int, float]:
    """
    Returns (nakshatra_name, pada, degree_within_nakshatra).
    Each nakshatra = 13°20' = 13.3333°. Each pada = 3°20' = 3.3333°.
    """
    nakshatra_span = 360 / 27  # 13.3333°
    pada_span = nakshatra_span / 4  # 3.3333°

    nak_index = int(lon // nakshatra_span) % 27
    degree_in_nak = lon % nakshatra_span
    pada = int(degree_in_nak // pada_span) + 1

    return NAKSHATRAS[nak_index], pada, round(degree_in_nak, 4)


def get_house(planet_lon: float, asc_lon: float) -> int:
    """
    Whole Sign house system: lagna sign = house 1.
    Returns house number 1-12.
    """
    lagna_sign_index = int(asc_lon // 30)
    planet_sign_index = int(planet_lon // 30)
    house = (planet_sign_index - lagna_sign_index) % 12 + 1
    return house


def get_dignity(planet: str, sign: str, lon: float) -> str:
    """Returns planetary dignity: exalted, debilitated, own, or neutral."""
    sign_index = SIGNS.index(sign)
    degree = lon % 30

    if planet in EXALTATION:
        ex_sign, ex_deg = EXALTATION[planet]
        if sign_index == ex_sign:
            return "exalted"

    if planet in DEBILITATION:
        deb_sign, deb_deg = DEBILITATION[planet]
        if sign_index == deb_sign:
            return "debilitated"

    if planet in OWN_SIGNS and sign in OWN_SIGNS[planet]:
        return "own"

    return "neutral"


def get_aspects(planet: str, house: int) -> list[int]:
    """
    Returns houses aspected by a planet (Vedic full aspects).
    All planets aspect 7th from themselves.
    Mars also aspects 4th and 8th.
    Jupiter also aspects 5th and 9th.
    Saturn also aspects 3rd and 10th.
    Rahu/Ketu aspect 5th and 9th (like Jupiter).
    """
    aspected = [(house + 6) % 12 or 12]  # 7th aspect

    extra = {
        "Mars": [3, 7],       # 4th and 8th from itself (offsets)
        "Jupiter": [4, 8],    # 5th and 9th
        "Saturn": [2, 9],     # 3rd and 10th
        "Rahu": [4, 8],
        "Ketu": [4, 8],
    }

    for offset in extra.get(planet, []):
        aspected.append((house + offset - 1) % 12 + 1)

    return sorted(set(aspected))


def build_planet_data(positions: dict, asc_lon: float) -> dict:
    """
    Builds structured planet info from raw longitudes.
    Returns dict keyed by planet name.
    """
    result = {}
    for planet, lon in positions.items():
        sign, deg_in_sign = longitude_to_sign(lon)
        nak, pada, deg_in_nak = longitude_to_nakshatra(lon)
        house = get_house(lon, asc_lon)
        dignity = get_dignity(planet, sign, lon)
        aspects = get_aspects(planet, house)

        result[planet] = {
            "longitude": lon,
            "sign": sign,
            "sign_lord": SIGN_LORDS[sign],
            "degree": deg_in_sign,
            "house": house,
            "nakshatra": nak,
            "nakshatra_pada": pada,
            "dignity": dignity,
            "aspects_houses": aspects,
        }

    return result


def get_house_lords(asc_lon: float) -> dict:
    """Returns {house_number: lord_planet} for all 12 houses."""
    lagna_sign_index = int(asc_lon // 30)
    lords = {}
    for i in range(12):
        sign = SIGNS[(lagna_sign_index + i) % 12]
        lords[i + 1] = SIGN_LORDS[sign]
    return lords

"""
Planetary position calculator using ephem (Brandon Rhodes).
Returns sidereal (Vedic/Lahiri) longitudes.
"""

import ephem
import math
from datetime import datetime


def lahiri_ayanamsha(jd: float) -> float:
    # Reference: Lahiri ayanamsha on Jan 1 1900 = 22°27'54" = 22.4650°
    # Annual precession ~50.3"/yr = 0.013972°/yr
    years_from_1900 = (jd - 2415020.5) / 365.25
    return 22.4650 + years_from_1900 * 0.013972


def _ecliptic_longitude(body, observer) -> float:
    """
    Geocentric tropical ecliptic longitude using ephem.Ecliptic.
    ephem.Ecliptic converts a body's apparent geocentric RA/Dec to ecliptic
    coordinates — giving the TRUE geocentric longitude, not heliocentric.
    Using body.hlong was wrong: it returns heliocentric longitude, which
    puts the Sun 180° off and other planets off by parallax.
    """
    body.compute(observer)
    ecl = ephem.Ecliptic(body, epoch=observer.date)
    return math.degrees(ecl.lon) % 360


def _ephem_body(name: str):
    return {
        "Sun":     ephem.Sun(),
        "Moon":    ephem.Moon(),
        "Mars":    ephem.Mars(),
        "Mercury": ephem.Mercury(),
        "Jupiter": ephem.Jupiter(),
        "Venus":   ephem.Venus(),
        "Saturn":  ephem.Saturn(),
    }.get(name)


def get_planet_positions(dt: datetime, lat: float, lon: float) -> dict:
    """
    Returns sidereal longitudes (0-360°) for all 9 Vedic planets.
    Rahu/Ketu from the IAU mean lunar node formula.
    """
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = dt.strftime("%Y/%m/%d %H:%M:%S")
    observer.pressure = 0

    jd = ephem.julian_date(observer.date)
    ayanamsha = lahiri_ayanamsha(jd)

    positions = {}
    for name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        body = _ephem_body(name)
        tropical = _ecliptic_longitude(body, observer)
        positions[name] = round((tropical - ayanamsha) % 360, 4)

    # Rahu (mean ascending node) — IAU formula, Julian centuries from J2000.0
    T = (jd - 2451545.0) / 36525.0
    rahu_tropical = (125.04455501
                     - 1934.13626197 * T
                     + 0.00207765 * T * T
                     + 0.00000215 * T * T * T) % 360
    if rahu_tropical < 0:
        rahu_tropical += 360
    rahu_sid = (rahu_tropical - ayanamsha) % 360
    positions["Rahu"] = round(rahu_sid, 4)
    positions["Ketu"] = round((rahu_sid + 180) % 360, 4)

    return positions


def _obliquity(jd: float) -> float:
    T = (jd - 2451545.0) / 36525.0
    return 23.439291111 - 0.013004167 * T - 0.000000164 * T ** 2 + 0.000000504 * T ** 3


def get_ascendant(dt: datetime, lat: float, lon: float) -> float:
    """
    Returns sidereal ascendant longitude (0-360°).

    Formula:  tan(E) = -cos(RAMC) / (sin(ε)·tan(φ) + cos(ε)·sin(RAMC))
    Quadrant: if denominator < 0  →  E += 180°   (standard spherical-astronomy rule)
    The earlier code used `if 90 < RAMC <= 270` which is WRONG — it flips the
    ascendant to the descendant for many evening birth times.
    """
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = dt.strftime("%Y/%m/%d %H:%M:%S")
    observer.pressure = 0

    jd = ephem.julian_date(observer.date)
    ayanamsha = lahiri_ayanamsha(jd)

    ramc = math.degrees(observer.sidereal_time()) % 360
    eps  = math.radians(_obliquity(jd))
    lat_rad  = math.radians(lat)
    ramc_rad = math.radians(ramc)

    num = -math.cos(ramc_rad)
    den =  math.sin(eps) * math.tan(lat_rad) + math.cos(eps) * math.sin(ramc_rad)

    asc_tropical = math.degrees(math.atan2(num, den)) % 360

    # Quadrant correction: denominator sign, NOT RAMC range
    if den < 0:
        asc_tropical = (asc_tropical + 180) % 360

    return round((asc_tropical - ayanamsha) % 360, 4)

"""
Divisional Charts (Vargas): D9 Navamsa, D10 Dasamsa, D7 Saptamsa, D60 Shastiamsa.
Each divides the zodiac to show specific life areas.
"""

from typing import Any
from .constants import SIGNS


def get_divisional_chart(lagna_lon: float, chart_type: str) -> dict:
    """
    Calculate divisional chart longitude for a given varga type.

    D1: Rashi (whole zodiac, 30° per sign)
    D9: Navamsa (9 divisions, 3°20' per sign) - marriage, karmic bonds
    D10: Dasamsa (10 divisions, 3° per sign) - career, public life
    D7: Saptamsa (7 divisions, 4°17' per sign) - children, health
    D60: Shastiamsa (60 divisions, 30 min per sign) - subtle karma
    """

    varga_divisor = {
        "D9": 9,
        "D10": 10,
        "D7": 7,
        "D60": 60,
    }.get(chart_type, 1)

    if varga_divisor == 1:
        return {"sign": get_sign(lagna_lon), "degree": lagna_lon % 30}

    # Calculate varga position
    varga_lon = (lagna_lon * varga_divisor) % 360

    return {
        "sign": get_sign(varga_lon),
        "degree": varga_lon % 30,
        "varga": chart_type,
        "divisor": varga_divisor,
    }


def get_sign(longitude: float) -> str:
    """Get sign for a longitude (0-360)."""
    sign_index = int(longitude // 30)
    return SIGNS[sign_index % 12]


def build_all_divisional_charts(chart: dict) -> dict:
    """Build D1, D9, D10, D7, D60 for lagna and key planets."""
    lagna_lon = chart["lagna"]["degree"] + (SIGNS.index(chart["lagna"]["sign"]) * 30)
    planets = chart["planets"]

    divisional_charts = {}

    # D9 Navamsa (marriage, spouse, relationships)
    d9 = {
        "type": "D9 Navamsa",
        "focus": "Marriage, Karmic Bonds, Spouse Qualities",
        "lagna": get_divisional_chart(lagna_lon, "D9"),
        "planets": {},
    }
    for planet, data in planets.items():
        p_lon = data.get("longitude", 0)
        d9["planets"][planet] = get_divisional_chart(p_lon, "D9")
    divisional_charts["D9"] = d9

    # D10 Dasamsa (career, public life, authority)
    d10 = {
        "type": "D10 Dasamsa",
        "focus": "Career, Public Image, Authority, Profession",
        "lagna": get_divisional_chart(lagna_lon, "D10"),
        "planets": {},
    }
    for planet, data in planets.items():
        p_lon = data.get("longitude", 0)
        d10["planets"][planet] = get_divisional_chart(p_lon, "D10")
    divisional_charts["D10"] = d10

    # D7 Saptamsa (children, health, dharma of family)
    d7 = {
        "type": "D7 Saptamsa",
        "focus": "Children, Health, Family Dharma",
        "lagna": get_divisional_chart(lagna_lon, "D7"),
        "planets": {},
    }
    for planet, data in planets.items():
        p_lon = data.get("longitude", 0)
        d7["planets"][planet] = get_divisional_chart(p_lon, "D7")
    divisional_charts["D7"] = d7

    # D60 Shastiamsa (subtle karma, hidden patterns)
    d60 = {
        "type": "D60 Shastiamsa",
        "focus": "Subtle Karma, Hidden Talents, Karmic Threads",
        "lagna": get_divisional_chart(lagna_lon, "D60"),
        "planets": {},
    }
    for planet, data in planets.items():
        p_lon = data.get("longitude", 0)
        d60["planets"][planet] = get_divisional_chart(p_lon, "D60")
    divisional_charts["D60"] = d60

    return divisional_charts


def analyze_divisional_strength(chart: dict) -> dict:
    """
    Compare D1 and D10 for career, D1 and D9 for marriage, etc.
    Returns coherence scores.
    """
    divisional = build_all_divisional_charts(chart)
    analysis = {}

    # D1 vs D10 (Career coherence)
    d1_sign = chart["lagna"]["sign"]
    d10_sign = divisional["D10"]["lagna"]["sign"]
    career_coherence = 100 if d1_sign == d10_sign else 70 if SIGNS.index(d1_sign) % 3 == SIGNS.index(d10_sign) % 3 else 50
    analysis["career_coherence"] = {
        "d1_lagna": d1_sign,
        "d10_lagna": d10_sign,
        "coherence_score": career_coherence,
        "interpretation": "Strong" if career_coherence > 80 else "Medium" if career_coherence > 60 else "Weak"
    }

    # D1 vs D9 (Marriage coherence)
    d9_sign = divisional["D9"]["lagna"]["sign"]
    marriage_coherence = 100 if d1_sign == d9_sign else 70 if SIGNS.index(d1_sign) % 2 == SIGNS.index(d9_sign) % 2 else 50
    analysis["marriage_coherence"] = {
        "d1_lagna": d1_sign,
        "d9_lagna": d9_sign,
        "coherence_score": marriage_coherence,
        "interpretation": "Strong" if marriage_coherence > 80 else "Medium" if marriage_coherence > 60 else "Weak"
    }

    # D1 vs D7 (Children/Health coherence)
    d7_sign = divisional["D7"]["lagna"]["sign"]
    children_coherence = 100 if d1_sign == d7_sign else 70 if SIGNS.index(d1_sign) % 3 == SIGNS.index(d7_sign) % 3 else 50
    analysis["children_coherence"] = {
        "d1_lagna": d1_sign,
        "d7_lagna": d7_sign,
        "coherence_score": children_coherence,
        "interpretation": "Strong" if children_coherence > 80 else "Medium" if children_coherence > 60 else "Weak"
    }

    return {
        "divisional_charts": divisional,
        "coherence_analysis": analysis,
    }

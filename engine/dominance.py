"""
Dominant Factors Engine: Compute chart influence hierarchy and mechanisms.
Ranks planets, yogas, and dasha by actual strength, not just positions.
"""

from typing import Any
from .constants import KENDRA_HOUSES, TRIKONA_HOUSES, TRIK_HOUSES


def _sign_strength(dignity: str) -> float:
    """Sign strength (exaltation, own, debilitation) 0-100."""
    strength_map = {
        "exalted": 95,
        "own": 80,
        "neutral": 50,
        "debilitated": 25,
    }
    return strength_map.get(dignity, 50)


def _house_strength(house: int) -> float:
    """House strength: kendra > trikona > trik > others."""
    if house in KENDRA_HOUSES:
        return 90  # Kendra (1,4,7,10) strongest
    elif house in TRIKONA_HOUSES:
        return 85  # Trikona (1,5,9)
    elif house in TRIK_HOUSES:
        return 45  # Trik (6,8,12) weak naturally, but some yogas here
    else:
        return 60  # Neutral


def _dasha_strength(planet: str, active_maha: str, active_antar: str) -> float:
    """Dasha activation: +40 if mahadasha, +20 if antardasha, else 0."""
    if planet == active_maha:
        return 40
    elif planet == active_antar:
        return 20
    else:
        return 0


def _aspect_strength(planet: str, chart: dict) -> float:
    """Strength from receiving auspicious aspects."""
    planets = chart.get("planets", {})
    p_data = planets.get(planet)
    if not p_data:
        return 0

    score = 0
    p_house = p_data["house"]
    aspected_by = p_data.get("aspects", [])

    # Which planets aspect this one
    for other_p, other_data in planets.items():
        if other_p == planet:
            continue
        if p_house in other_data.get("aspects", []):
            # Benefic aspects help, malefic hinder
            if other_p in ("Jupiter", "Venus", "Mercury"):
                score += 15
            elif other_p in ("Sun", "Moon"):
                score += 10
            elif other_p in ("Mars", "Saturn"):
                score -= 8
            elif other_p in ("Rahu", "Ketu"):
                score -= 5

    return min(100, max(0, 50 + score))


def _combustion_penalty(planet: str, sun_lon: float, planet_lon: float) -> float:
    """Penalty if planet is too close to Sun (combusted)."""
    if planet in ("Sun", "Moon"):
        return 0  # Sun/Moon can't combust
    diff = abs(sun_lon - planet_lon)
    if diff > 180:
        diff = 360 - diff
    if diff < 8:  # Combusted
        return -30
    elif diff < 15:  # Partially afflicted
        return -15
    return 0


def compute_planet_strength(chart: dict) -> dict:
    """
    Computes strength score for each planet.
    Returns {planet: {strength, components, rank}}.
    """
    planets = chart.get("planets", {})
    dasha = chart.get("dasha", {})
    sun_lon = chart.get("planets", {}).get("Sun", {}).get("longitude", 0)

    active_maha = dasha.get("mahadasha", "")
    active_antar = dasha.get("antardasha", "")

    scores = {}

    for planet, data in planets.items():
        lon = data.get("longitude", 0)
        sign_str = _sign_strength(data.get("dignity", "neutral"))
        house_str = _house_strength(data.get("house", 6))
        dasha_str = _dasha_strength(planet, active_maha, active_antar)
        aspect_str = _aspect_strength(planet, chart)
        combust = _combustion_penalty(planet, sun_lon, lon)

        total = (sign_str * 0.25 + house_str * 0.25 + dasha_str * 0.20 +
                 aspect_str * 0.20 + combust * 0.10)
        total = max(0, min(100, total))

        scores[planet] = {
            "strength": round(total, 1),
            "components": {
                "sign_strength": round(sign_str, 1),
                "house_strength": round(house_str, 1),
                "dasha_activation": round(dasha_str, 1),
                "aspect_support": round(aspect_str, 1),
                "combustion_penalty": round(combust, 1),
            },
        }

    # Rank by strength
    ranked = sorted(scores.items(), key=lambda x: x[1]["strength"], reverse=True)
    for rank, (planet, data) in enumerate(ranked, 1):
        data["rank"] = rank

    return dict(ranked)


def identify_dominant_mechanisms(chart: dict, top_k: int = 5) -> list[dict]:
    """
    Returns top N mechanisms (planet placements, yogas, dasha activations)
    that most strongly influence the chart.
    """
    mechanisms = []
    planet_strength = compute_planet_strength(chart)
    yogas = chart.get("yogas", [])
    dasha = chart.get("dasha", {})

    # Top planet placements
    for planet, data in list(planet_strength.items())[:5]:
        p_chart = chart["planets"][planet]
        mechanisms.append({
            "type": "planet",
            "name": f"{planet} in {p_chart['sign']} H{p_chart['house']}",
            "strength": data["strength"],
            "reasoning": f"{planet} strength {data['strength']:.0f}: "
                        f"Sign:{data['components']['sign_strength']:.0f}, "
                        f"House:{data['components']['house_strength']:.0f}, "
                        f"Dasha:{data['components']['dasha_activation']:.0f}",
        })

    # Yogas (high impact)
    for yoga in yogas:
        yoga_strength = 85 if "Raja" in yoga["name"] else 75
        mechanisms.append({
            "type": "yoga",
            "name": yoga["name"],
            "strength": yoga_strength,
            "reasoning": f"{yoga['rule']} => {yoga['effect']}",
        })

    # Current dasha (context)
    if dasha.get("mahadasha"):
        mechanisms.append({
            "type": "dasha",
            "name": f"{dasha['mahadasha']} Mahadasha (active now)",
            "strength": 80,
            "reasoning": f"Active until {dasha['mahadasha_end']}, "
                        f"with {dasha['antardasha']} Antardasha until {dasha['antardasha_end']}",
        })

    # Sort and return top K
    mechanisms.sort(key=lambda x: x["strength"], reverse=True)
    return mechanisms[:top_k]


def find_contradictions(chart: dict) -> dict:
    """
    Identifies conflicting indicators and how they resolve.
    Returns {contradiction_type: [positive_factors, negative_factors, resolution]}.
    """
    planets = chart.get("planets", {})
    yogas = [y["name"] for y in chart.get("yogas", [])]
    dasha = chart.get("dasha", {})

    contradictions = {}

    # ── Career contradiction ──
    career_positive = []
    career_negative = []

    # Sun/Mars in 10th is strong
    if planets.get("Sun", {}).get("house") == 10:
        career_positive.append("Sun in 10th (authority, visibility)")
    if planets.get("Mars", {}).get("house") == 10:
        career_positive.append("Mars in 10th (leadership, drive)")

    # Raja Yoga helps
    if any("Raja" in y for y in yogas):
        career_positive.append("Raja Yoga active (success yoga)")

    # Rahu mahadasha = uncertainty
    if dasha.get("mahadasha") == "Rahu":
        career_negative.append("Rahu Mahadasha (unconventional, unstable pathways)")

    # Jupiter in 8th = delay/hidden success
    if planets.get("Jupiter", {}).get("house") == 8:
        career_negative.append("Jupiter in 8th (results come through transformation, not direct path)")

    if career_positive and career_negative:
        contradictions["career"] = {
            "positive": career_positive,
            "negative": career_negative,
            "resolution": "Strong career potential exists, but Rahu period may create "
                         "unconventional challenges before stabilization. Success comes "
                         "through learning and adaptation rather than direct achievement.",
        }

    # ── Marriage contradiction ──
    marriage_positive = []
    marriage_negative = []

    # Venus strength helps
    if planets.get("Venus", {}).get("dignity") in ("exalted", "own"):
        marriage_positive.append("Venus strong (harmony, partnership)")

    # Sun/Saturn in 7th afflicts
    if planets.get("Sun", {}).get("house") == 7:
        marriage_negative.append("Sun in 7th (ego in relationships)")
    if planets.get("Saturn", {}).get("house") == 7:
        marriage_negative.append("Saturn in 7th (delays, coldness)")

    if marriage_positive and marriage_negative:
        contradictions["marriage"] = {
            "positive": marriage_positive,
            "negative": marriage_negative,
            "resolution": "Partnership is possible but requires maturity and patience. "
                         "Early relationships may be turbulent; later ones more stable.",
        }

    # ── Spirituality contradiction ──
    spiritual_positive = []
    spiritual_negative = []

    if planets.get("Jupiter", {}).get("house") in (8, 9, 12):
        spiritual_positive.append("Jupiter in moksha house (spirituality)")

    if dasha.get("mahadasha") == "Rahu":
        spiritual_negative.append("Rahu MD (material focus, worldly chaos)")

    if spiritual_positive and spiritual_negative:
        contradictions["spirituality"] = {
            "positive": spiritual_positive,
            "negative": spiritual_negative,
            "resolution": "Spiritual inclination exists but is dormant during Rahu period. "
                         "Will activate strongly in later dashas (Jupiter, Saturn).",
        }

    return contradictions


def generate_chart_summary(chart: dict) -> dict:
    """
    High-level chart summary for SLM prompt.
    Returns the key mechanisms, contradictions, and themes.
    """
    mechanisms = identify_dominant_mechanisms(chart, top_k=5)
    contradictions = find_contradictions(chart)
    planet_strength = compute_planet_strength(chart)

    # Top 3 planets by strength
    top_planets = [p for p, data in list(planet_strength.items())[:3]]

    lagna = chart.get("lagna", {})
    dasha = chart.get("dasha", {})

    return {
        "lagna": {
            "sign": lagna.get("sign"),
            "degree": lagna.get("degree"),
            "lord": lagna.get("lord"),
        },
        "moon_nakshatra": f"{chart.get('moon', {}).get('nakshatra')} "
                         f"P{chart.get('moon', {}).get('nakshatra_pada')}",
        "dominant_mechanisms": mechanisms,
        "planet_strength_ranking": {
            planet: {
                "strength": data["strength"],
                "rank": data["rank"],
            }
            for planet, data in planet_strength.items()
        },
        "contradictions": contradictions,
        "current_dasha": {
            "mahadasha": dasha.get("mahadasha"),
            "antardasha": dasha.get("antardasha"),
            "mahadasha_end": dasha.get("mahadasha_end"),
        },
        "top_planets_by_influence": top_planets,
        "interpretation_themes": {
            "primary_axis": _identify_primary_axis(chart, contradictions),
            "dominant_planet": top_planets[0] if top_planets else None,
            "shadow_theme": _identify_shadow_theme(chart),
        },
    }


def _identify_primary_axis(chart: dict, contradictions: dict) -> str:
    """Identify the main life axis from chart placements."""
    if "career" in contradictions:
        return "Career ↔ Dharma"
    elif "marriage" in contradictions:
        return "Partnership ↔ Independence"
    elif "spirituality" in contradictions:
        return "Worldly ↔ Spiritual"
    planets = chart.get("planets", {})
    if planets.get("Sun", {}).get("house") in (9, 10):
        return "Dharma ↔ Public Life"
    if planets.get("Venus", {}).get("house") in (7, 11):
        return "Relationships ↔ Social Influence"
    return "Growth ↔ Stability"


def _identify_shadow_theme(chart: dict) -> str:
    """What challenges or growth areas the chart highlights."""
    dasha = chart.get("dasha", {})
    if dasha.get("mahadasha") == "Rahu":
        return "Rahu-driven transformation and experimentation"
    if dasha.get("mahadasha") == "Saturn":
        return "Saturn testing and building through discipline"
    planets = chart.get("planets", {})
    if planets.get("Saturn", {}).get("house") == 1:
        return "Early karmic testing, later wisdom"
    return "Finding authenticity through self-discovery"

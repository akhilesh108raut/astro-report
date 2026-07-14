"""
Main chart builder. Given birth data, produces a fully structured chart JSON
ready for SLM reasoning.
"""

from datetime import datetime
from .ephemeris import get_planet_positions, get_ascendant
from .vedic import build_planet_data, get_house_lords, longitude_to_sign, longitude_to_nakshatra
from .dashas import get_dasha_balance
from .yogas import detect_yogas
from .dominance import generate_chart_summary
from .graph import build_graph_visualization
from .timeline import generate_life_timeline
from .confidence import score_life_areas
from .divisional import analyze_divisional_strength
from .chart_dna import extract_chart_dna
from .multi_agent import run_multi_agent_analysis
from .predictions import generate_predictions
from .advanced_predictions import generate_advanced_predictions
from .constants import SIGNS, SIGN_LORDS


def build_chart(
    year: int, month: int, day: int,
    hour: int, minute: int,
    lat: float, lon: float,
    timezone_offset: float = 5.5,  # IST default
    # Backward-compat: older callers (and tests) pass `timezone` instead of `timezone_offset`
    timezone: float | None = None,
    name: str = ""
) -> dict:
    """
    Returns a fully structured Vedic birth chart as a dict.

    Args:
        year/month/day/hour/minute: Local birth time
        lat/lon: Birth place coordinates
        timezone_offset: Hours offset from UTC (e.g. 5.5 for IST)
        name: Optional name for reference
    """
    # Backward-compat: if `timezone` provided, it overrides `timezone_offset`.
    if timezone is not None:
        timezone_offset = timezone

    # Ensure timezone_offset is numeric (timedelta(hours=...) is strict)
    try:
        timezone_offset = float(timezone_offset)
    except (TypeError, ValueError) as e:
        raise TypeError(f"Invalid timezone_offset: {timezone_offset!r}") from e

    # Convert to UTC
    from datetime import timedelta
    local_dt = datetime(year, month, day, hour, minute)
    utc_dt = local_dt - timedelta(hours=timezone_offset)

    # Core calculations
    positions = get_planet_positions(utc_dt, lat, lon)
    asc_lon = get_ascendant(utc_dt, lat, lon)

    # Structured planet data
    planet_data = build_planet_data(positions, asc_lon)
    house_lords = get_house_lords(asc_lon)

    # Lagna info
    lagna_sign, lagna_deg = longitude_to_sign(asc_lon)
    lagna_lord = SIGN_LORDS[lagna_sign]

    # Moon info
    moon_lon = positions["Moon"]
    moon_sign, moon_deg = longitude_to_sign(moon_lon)
    moon_nak, moon_pada, _ = longitude_to_nakshatra(moon_lon)

    # Sun info
    sun_lon = positions["Sun"]
    sun_sign, _ = longitude_to_sign(sun_lon)

    # Dashas — show current dasha (today's date), not dasha at birth
    from datetime import datetime as _dt
    today = _dt.now()
    dasha_info = get_dasha_balance(moon_lon, local_dt, query_date=today)

    # Yogas
    yogas = detect_yogas(planet_data, house_lords)

    # Build planetary summary (compact for SLM input)
    planets_compact = {}
    for planet, data in planet_data.items():
        planets_compact[planet] = {
            "sign": data["sign"],
            "house": data["house"],
            "nakshatra": data["nakshatra"],
            "nakshatra_pada": data["nakshatra_pada"],
            "dignity": data["dignity"],
            "aspects": data["aspects_houses"],
            # Keep legacy fields expected by tests/client.
            # Some downstream code expects either `longitude` or `lon`.
            "longitude": data.get("longitude", data.get("lon")),
            "lon": data.get("lon", data.get("longitude")),

            "retrograde": False,   # updated by server after chart build
        }


    # House lord placements
    house_lord_placements = {}
    for house_num, lord in house_lords.items():
        lord_house = planet_data.get(lord, {}).get("house", "?")
        house_lord_placements[f"house_{house_num}_lord"] = {
            "planet": lord,
            "placed_in_house": lord_house
        }

    chart = {
        "meta": {
            "name": name,
            "birth_date": f"{year:04d}-{month:02d}-{day:02d}",
            "birth_time": f"{hour:02d}:{minute:02d}",
            "latitude": lat,
            "longitude": lon,
            "timezone_offset": timezone_offset,
        },
        "lagna": {
            "sign": lagna_sign,
            "degree": round(lagna_deg, 2),
            "lord": lagna_lord,
        },
        "moon": {
            "sign": moon_sign,
            "nakshatra": moon_nak,
            "nakshatra_pada": moon_pada,
        },
        "sun_sign": sun_sign,
        "planets": planets_compact,
        "house_lords": house_lord_placements,
        "yogas": yogas,
        "dasha": dasha_info,
    }

    # Add dominant factors analysis
    chart["analysis"] = generate_chart_summary(chart)

    # Phase 2: Add graph, timeline, and confidence
    chart["graph"] = build_graph_visualization(chart)
    chart["timeline"] = generate_life_timeline(chart)
    chart["confidence_scores"] = score_life_areas(chart)

    # Phase 3: Add divisional charts, chart DNA, and multi-agent reasoning
    divisional = analyze_divisional_strength(chart)
    chart["divisional"] = divisional["divisional_charts"]
    chart["divisional_coherence"] = divisional["coherence_analysis"]

    chart["chart_dna"] = extract_chart_dna(chart)

    chart["multi_agent_analysis"] = run_multi_agent_analysis(chart)

    # Add predictions for next 10 years
    from datetime import datetime as _dt
    current_year = _dt.now().year
    chart["predictions"] = generate_predictions(chart, current_year, years_ahead=10)

    # Add advanced predictions (karma, dharma, detailed life areas)
    chart["advanced_predictions"] = generate_advanced_predictions(chart)

    return chart


def chart_to_reasoning_prompt(chart: dict) -> str:
    """
    Converts structured chart to a reasoning-chain prompt for SLM training.
    NOW includes dominant factors analysis at the top.
    """
    lagna = chart["lagna"]
    moon = chart["moon"]
    dasha = chart["dasha"]
    planets = chart["planets"]
    yogas = chart["yogas"]
    analysis = chart.get("analysis", {})

    # ── Dominant mechanisms (highest impact) ──
    mechanisms = analysis.get("dominant_mechanisms", [])
    mechanism_str = ""
    if mechanisms:
        mechanism_str = "=== TOP 5 DOMINANT MECHANISMS ===\n"
        for i, mech in enumerate(mechanisms, 1):
            mechanism_str += f"{i}. {mech['name']} (strength: {mech['strength']:.0f}%)\n"
            mechanism_str += f"   {mech['reasoning']}\n"
        mechanism_str += "\n"

    # ── Planet strength ranking ──
    ranking = analysis.get("planet_strength_ranking", {})
    rank_str = ""
    if ranking:
        rank_str = "=== PLANET INFLUENCE RANKING ===\n"
        ranked = sorted(ranking.items(), key=lambda x: x[1]['strength'], reverse=True)
        for planet, data in ranked:
            rank_str += f"  {planet}: {data['strength']:.0f} (rank #{data['rank']})\n"
        rank_str += "\n"

    # ── Contradictions ──
    contradictions = analysis.get("contradictions", {})
    contradiction_str = ""
    if contradictions:
        contradiction_str = "=== CONFLICTING INDICATORS & RESOLUTION ===\n"
        for theme, info in contradictions.items():
            contradiction_str += f"{theme.upper()}:\n"
            contradiction_str += f"  Positive: {', '.join(info['positive'])}\n"
            contradiction_str += f"  Negative: {', '.join(info['negative'])}\n"
            contradiction_str += f"  Resolution: {info['resolution']}\n\n"

    # ── Themes ──
    themes = analysis.get("interpretation_themes", {})
    theme_str = ""
    if themes:
        theme_str = "=== CHART THEMES ===\n"
        if themes.get("primary_axis"):
            theme_str += f"  Primary Life Axis: {themes['primary_axis']}\n"
        if themes.get("dominant_planet"):
            theme_str += f"  Dominant Planet: {themes['dominant_planet']}\n"
        if themes.get("shadow_theme"):
            theme_str += f"  Shadow Theme: {themes['shadow_theme']}\n"
        theme_str += "\n"

    yoga_rules = "\n".join(f"  - {y['name']}: {y['rule']} => {y['effect']}" for y in yogas)

    prompt = f"""{mechanism_str}{rank_str}{contradiction_str}{theme_str}=== BIRTH CHART DETAILS ===
Lagna (Ascendant): {lagna['sign']} at {lagna['degree']}° — Lord: {lagna['lord']}
Moon: {moon['sign']}, Nakshatra: {moon['nakshatra']} Pada {moon['nakshatra_pada']}
Sun: {chart['sun_sign']}

=== ACTIVE YOGAS ===
{yoga_rules if yogas else 'None'}

=== CURRENT DASHA ===
Mahadasha: {dasha['mahadasha']} (ends {dasha['mahadasha_end']})
Antardasha: {dasha['antardasha']} (ends {dasha['antardasha_end']})

=== REASONING TASK ===
Based on the dominant mechanisms above, synthesize a coherent interpretation:
1. What are the 3-5 strongest mechanisms governing this chart?
2. How do the positive and negative factors resolve?
3. What is the net effect on the person's life trajectory?
4. How does the current dasha activate or inhibit these mechanisms?
5. Provide a final one-sentence archetype for this chart.

=== INTERPRETATION ==="""

    return prompt

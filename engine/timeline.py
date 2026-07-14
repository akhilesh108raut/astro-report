"""
Timeline Generator: When things happen based on dasha periods.
Shows activation periods, transits, and major turning points.
"""

from datetime import datetime, timedelta
from typing import Any


def generate_life_timeline(chart: dict, current_year: int = 2026, num_years: int = 50) -> dict:
    """
    Generates a life timeline showing dasha periods and major life themes.
    """
    birth_date_str = chart["meta"]["birth_date"]
    birth_year = int(birth_date_str[:4])
    dasha_info = chart["dasha"]
    planets = chart["planets"]
    analysis = chart.get("analysis", {})

    timeline = {
        "birth": birth_year,
        "current": current_year,
        "age_now": current_year - birth_year,
        "periods": [],
        "milestones": [],
    }

    # Extract upcoming dashas
    upcoming = dasha_info.get("upcoming_dashas", [])
    if not upcoming:
        return timeline

    # Build period entries
    for dasha_entry in upcoming:
        lord = dasha_entry["lord"]
        start_str = dasha_entry["start"]
        end_str = dasha_entry["end"]

        try:
            start = datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.strptime(end_str, "%Y-%m-%d")
        except:
            continue

        start_year = start.year
        end_year = end.year
        duration = (end - start).days // 365

        # Determine what this dasha activates
        planet_data = planets.get(lord, {})
        houses_occupied = [planet_data.get("house")]
        themes = _get_dasha_themes(lord, planet_data, chart)

        period = {
            "dasha_lord": lord,
            "start_year": start_year,
            "end_year": end_year,
            "duration_years": duration,
            "age_start": start_year - birth_year,
            "age_end": end_year - birth_year,
            "houses_activated": houses_occupied,
            "themes": themes,
            "quality": _rate_dasha_period(lord, chart),
        }

        if start_year >= current_year - 5 and end_year <= current_year + 30:
            timeline["periods"].append(period)

    # Generate milestones (major turning points)
    timeline["milestones"] = _identify_milestones(chart, timeline["periods"], birth_year)

    return timeline


def _get_dasha_themes(dasha_lord: str, planet_data: dict, chart: dict) -> list[str]:
    """Extract life themes for a dasha period."""
    themes = []
    house = planet_data.get("house")
    sign = planet_data.get("sign")
    nakshatra = planet_data.get("nakshatra")

    # House themes
    house_themes = {
        1: ["Identity", "Self-Expression", "Physical Health"],
        2: ["Wealth", "Family", "Values"],
        3: ["Communication", "Siblings", "Short Travel"],
        4: ["Home", "Mother", "Real Estate"],
        5: ["Creativity", "Children", "Romance"],
        6: ["Enemies", "Health Issues", "Service Work"],
        7: ["Marriage", "Partnerships", "Public Relations"],
        8: ["Transformation", "Inheritance", "Occult"],
        9: ["Fortune", "Spirituality", "Higher Learning"],
        10: ["Career", "Authority", "Public Image"],
        11: ["Gains", "Social Network", "Fulfillment"],
        12: ["Spirituality", "Isolation", "Foreign Lands"],
    }
    themes.extend(house_themes.get(house, []))

    # Planet-specific themes
    planet_themes = {
        "Sun": ["Leadership", "Authority", "Vitality"],
        "Moon": ["Emotions", "Nurturing", "Mental Peace"],
        "Mars": ["Action", "Conflict Resolution", "Physical Challenges"],
        "Mercury": ["Communication", "Business", "Learning"],
        "Jupiter": ["Expansion", "Wisdom", "Abundance"],
        "Venus": ["Relationships", "Luxury", "Creativity"],
        "Saturn": ["Discipline", "Hard Work", "Maturity"],
        "Rahu": ["Ambition", "Unconventional Paths", "Experimentation"],
        "Ketu": ["Spirituality", "Release", "Karmic Lessons"],
    }
    themes.extend(planet_themes.get(dasha_lord, []))

    return list(set(themes))[:5]  # Top 5 unique themes


def _rate_dasha_period(dasha_lord: str, chart: dict) -> str:
    """Rate whether a dasha period is favorable or challenging."""
    analysis = chart.get("analysis", {})
    contradictions = analysis.get("contradictions", {})

    # Check if this dasha is mentioned in contradictions
    for theme, info in contradictions.items():
        if dasha_lord in str(info.get("negative", "")):
            return "challenging"

    # Benefic vs malefic
    if dasha_lord in ("Jupiter", "Venus", "Mercury"):
        return "favorable"
    elif dasha_lord in ("Saturn", "Mars"):
        return "challenging"
    elif dasha_lord == "Rahu":
        return "transformative"
    else:
        return "neutral"


def _identify_milestones(chart: dict, periods: list, birth_year: int) -> list[dict]:
    """Identify major life turning points."""
    milestones = []

    for period in periods:
        dasha_lord = period["dasha_lord"]
        start_year = period["start_year"]
        quality = period["quality"]

        age = start_year - birth_year

        # Age milestones (Vedic tradition)
        if age in [18, 21, 25, 30, 36, 42, 48, 54]:
            milestone_type = "Vedic Age Gate"
            if age == 30:
                milestone_type = "Saturn Return (maturity test)"
            elif age == 42:
                milestone_type = "Mid-Life Activation"
            elif age == 54:
                milestone_type = "Saturn Maturity Complete"

            milestones.append({
                "year": start_year,
                "age": age,
                "type": milestone_type,
                "dasha": dasha_lord,
                "description": f"{dasha_lord} Mahadasha begins at age {age}. "
                              f"{quality.capitalize()} period for inner transformation.",
            })

        # Dasha change milestones (major transitions)
        if quality == "transformative":
            milestones.append({
                "year": start_year,
                "age": age,
                "type": "Dasha Activation (Unconventional)",
                "dasha": dasha_lord,
                "description": f"{dasha_lord} activation at age {age}. "
                              f"Unconventional paths, experimentation, major life shifts.",
            })
        elif quality == "challenging":
            milestones.append({
                "year": start_year,
                "age": age,
                "type": "Testing Period",
                "dasha": dasha_lord,
                "description": f"{dasha_lord} Mahadasha begins at age {age}. "
                              f"Requires discipline and resilience. Growth through adversity.",
            })

    return milestones[:15]  # Top 15 milestones


def format_timeline_for_display(timeline: dict) -> str:
    """Format timeline as readable text."""
    output = []
    output.append(f"LIFE TIMELINE (Age {timeline['age_now']} in {timeline['current']})\n")
    output.append("=" * 60)

    for period in timeline["periods"]:
        output.append(
            f"\n{period['dasha_lord'].upper()} Mahadasha: "
            f"Age {period['age_start']}-{period['age_end']} ({period['start_year']}-{period['end_year']})"
        )
        output.append(f"  Duration: {period['duration_years']} years | Quality: {period['quality']}")
        output.append(f"  Themes: {', '.join(period['themes'][:3])}")

    if timeline["milestones"]:
        output.append("\n\nMAJOR MILESTONES")
        output.append("=" * 60)
        for m in timeline["milestones"]:
            output.append(
                f"\nAge {m['age']} ({m['year']}) — {m['type']}"
            )
            output.append(f"  {m['description']}")

    return "\n".join(output)

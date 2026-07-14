"""
Chart DNA: Extract the core archetypal pattern of a chart.
One sentence that captures the entire chart's essence.
"""

from typing import Any


def extract_chart_dna(chart: dict) -> dict:
    """
    Distill a chart into its core archetype and life story.
    Returns one-liner + detailed archetype profile.
    """
    analysis = chart.get("analysis", {})
    planets = chart.get("planets", {})
    yogas = chart.get("yogas", [])
    dasha = chart.get("dasha", {})

    # Identify core archetypal pattern
    primary_axis = analysis.get("interpretation_themes", {}).get("primary_axis", "Unknown")
    dominant_planet = analysis.get("interpretation_themes", {}).get("dominant_planet", "Unknown")
    shadow_theme = analysis.get("interpretation_themes", {}).get("shadow_theme", "Unknown")

    mechanisms = analysis.get("dominant_mechanisms", [])
    contradictions = analysis.get("contradictions", {})

    # Build archetype name
    archetype = _determine_archetype(
        dominant_planet, mechanisms, contradictions, yogas, primary_axis
    )

    # One-liner
    one_liner = _generate_one_liner(archetype, primary_axis, shadow_theme, dasha)

    # Detailed profile
    profile = {
        "archetype_name": archetype,
        "one_liner": one_liner,
        "primary_life_axis": primary_axis,
        "dominant_planet": dominant_planet,
        "shadow_theme": shadow_theme,
        "core_mechanism": mechanisms[0]["name"] if mechanisms else "Unknown",
        "life_challenge": _identify_challenge(contradictions),
        "life_gift": _identify_gift(mechanisms, yogas),
        "developmental_direction": _identify_direction(dasha, planets),
        "destiny_type": _identify_destiny_type(mechanisms, yogas),
    }

    return profile


def _determine_archetype(dominant_planet: str, mechanisms: list, contradictions: dict, yogas: list, axis: str) -> str:
    """Determine the core archetype."""
    # Check for specific yoga patterns
    yoga_names = [y["name"] for y in yogas]

    if "Raja Yoga" in yoga_names and len(yoga_names) >= 2:
        return "The Sovereign"
    elif dominant_planet == "Jupiter":
        return "The Sage" if "Spirituality" in axis else "The Benefactor"
    elif dominant_planet == "Saturn":
        return "The Builder" if "Career" in axis else "The Hermit"
    elif dominant_planet == "Venus":
        return "The Lover" if "Marriage" in contradictions else "The Artist"
    elif dominant_planet == "Mars":
        return "The Warrior"
    elif dominant_planet == "Mercury":
        return "The Scholar"
    elif dominant_planet == "Moon":
        return "The Nurturer"
    elif dominant_planet == "Sun":
        return "The Leader"
    elif dominant_planet == "Rahu":
        return "The Transformer"
    elif dominant_planet == "Ketu":
        return "The Mystic"
    else:
        return "The Seeker"


def _generate_one_liner(archetype: str, axis: str, shadow: str, dasha: dict) -> str:
    """Generate one-sentence description of the chart."""
    current_md = dasha.get("mahadasha", "Unknown")

    templates = {
        "The Sovereign": f"A natural leader navigating {axis.split('↔')[0]} through authority and vision.",
        "The Sage": f"A seeker of wisdom pursuing {axis.split('↔')[0]} with philosophical depth.",
        "The Benefactor": f"A generous soul spreading abundance while exploring {axis}.",
        "The Builder": f"A disciplined architect constructing {axis.split('↔')[0]} through sustained effort.",
        "The Hermit": f"An introspective sage building wisdom through solitude and {axis.split('↔')[1]}.",
        "The Lover": f"A relational being seeking harmony in {axis.split('↔')[0]} and human connection.",
        "The Artist": f"A creative soul expressing {axis.split('↔')[0]} through artistic vision.",
        "The Warrior": f"A courageous fighter conquering {axis.split('↔')[0]} through bold action.",
        "The Scholar": f"An intellectual explorer mastering {axis.split('↔')[0]} through learning.",
        "The Nurturer": f"A compassionate caregiver manifesting {axis.split('↔')[0]} through connection.",
        "The Leader": f"A luminous presence shining in {axis.split('↔')[0]} through authentic power.",
        "The Transformer": f"An evolutionary spirit embracing {shadow} to reach {axis.split('↔')[1]}.",
        "The Mystic": f"A transcendent being discovering ultimate truth beyond {axis}.",
        "The Seeker": f"An earnest explorer navigating {axis} with growth-oriented intention.",
    }

    return templates.get(archetype, f"A complex being navigating {axis}.")


def _identify_challenge(contradictions: dict) -> str:
    """What is the main life challenge."""
    if not contradictions:
        return "Learning to balance multiple competing interests."

    for theme, info in contradictions.items():
        return f"{theme.title()}: {info['resolution'][:50]}..."

    return "Integrating internal contradictions."


def _identify_gift(mechanisms: list, yogas: list) -> str:
    """What is the life gift/strength."""
    if mechanisms:
        top = mechanisms[0]
        return f"Strength in {top['name']}: {top['reasoning'][:50]}..."

    if yogas:
        top_yoga = yogas[0]
        return f"{top_yoga['name']}: {top_yoga['effect']}"

    return "Capacity for growth and learning."


def _identify_direction(dasha: dict, planets: dict) -> str:
    """What direction should development head."""
    current_md = dasha.get("mahadasha", "")

    if current_md == "Rahu":
        return "Embrace experimentation and unconventional paths; stabilize later with Saturn/Jupiter MD."
    elif current_md == "Saturn":
        return "Build discipline and lasting foundations; wisdom comes through patient effort."
    elif current_md == "Jupiter":
        return "Expand knowledge, spirituality, and generosity; share gifts with others."
    elif current_md == "Venus":
        return "Cultivate relationships and creative expression; seek harmony and beauty."
    elif current_md == "Mars":
        return "Channel courage into purposeful action; overcome obstacles with determination."
    else:
        return f"Continue {current_md} themes; prepare for next dasha transition."


def _identify_destiny_type(mechanisms: list, yogas: list) -> str:
    """What type of destiny does this chart show."""
    yoga_names = [y["name"] for y in yogas]
    mechanism_names = [m["name"] for m in mechanisms]

    if any("Raja" in name for name in yoga_names):
        return "Destiny of Power: Success through authority and leadership."
    elif any("Dhana" in name for name in yoga_names):
        return "Destiny of Wealth: Material abundance and financial success."
    elif "Viparita Raja Yoga" in yoga_names:
        return "Destiny of Transformation: Gain through adversity and hidden strength."
    elif any("Pancha Mahapurusha" in name for name in yoga_names):
        return "Destiny of Excellence: Outstanding achievement in specific field."
    elif "Rahu Mahadasha" in mechanism_names:
        return "Destiny of Evolution: Rapid growth through unconventional means."
    elif "Saturn" in mechanism_names:
        return "Destiny of Discipline: Enduring success through patient work."
    else:
        return "Destiny of Balance: Harmonious development across life areas."


def format_chart_dna(dna: dict) -> str:
    """Format DNA as readable text."""
    output = []
    output.append("=" * 70)
    output.append("CHART DNA - CORE ARCHETYPE")
    output.append("=" * 70)
    output.append("")
    output.append(f"ARCHETYPE: {dna['archetype_name']}")
    output.append("")
    output.append(f"ONE LINER:")
    output.append(f"  \"{dna['one_liner']}\"")
    output.append("")
    output.append(f"LIFE AXIS: {dna['primary_life_axis']}")
    output.append(f"DOMINANT PLANET: {dna['dominant_planet']}")
    output.append(f"SHADOW THEME: {dna['shadow_theme']}")
    output.append("")
    output.append(f"CORE MECHANISM: {dna['core_mechanism']}")
    output.append("")
    output.append(f"LIFE CHALLENGE:")
    output.append(f"  {dna['life_challenge']}")
    output.append("")
    output.append(f"LIFE GIFT:")
    output.append(f"  {dna['life_gift']}")
    output.append("")
    output.append(f"DEVELOPMENT DIRECTION:")
    output.append(f"  {dna['developmental_direction']}")
    output.append("")
    output.append(f"DESTINY TYPE:")
    output.append(f"  {dna['destiny_type']}")
    output.append("")
    output.append("=" * 70)

    return "\n".join(output)

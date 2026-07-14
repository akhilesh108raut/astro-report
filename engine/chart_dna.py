"""
Chart DNA: Extract the core archetypal pattern of a chart.
One sentence that captures the entire chart's essence.
"""

from typing import Any


def _truncate_at_word(text: str, limit: int = 90) -> str:
    """Truncate at a word boundary, never mid-word, and only append '...'
    when something was actually cut."""
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut + "..."


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
    """Generate the arrival-page hook — a destiny statement, not a personality
    label. Every version below is built only from real chart_dna inputs
    (archetype, axis, shadow theme, current dasha) but framed to promise
    what the report reveals, not just describe a trait."""
    left, right = (axis.split('↔') + [axis])[:2]
    current_md = dasha.get("mahadasha", "")
    now = f" Right now, your {current_md} Mahadasha is where that gift is being tested." if current_md else ""

    templates = {
        "The Sovereign": f"You weren't born to simply succeed — your chart points toward earning authority "
                         f"through {left.strip().lower()}, not demanding it.{now}",
        "The Sage": f"Every choice you've made has quietly circled back to one question: what is actually true. "
                    f"Your chart explains why {left.strip().lower()} keeps pulling at you, and what it's preparing you to understand.",
        "The Benefactor": f"Your chart suggests a life measured less by what you keep and more by what you make "
                           f"possible for others — built around {left.strip().lower()}.{now}",
        "The Builder": f"Some lives chase quick wins. Yours is built for what lasts — {left.strip().lower()}, "
                       f"assembled slowly enough to actually hold weight.{now}",
        "The Hermit": f"You've likely spent more of your life in solitude than most — not from avoidance, "
                      f"but because {right.strip().lower()} only reveals itself in quiet.",
        "The Lover": f"Your chart suggests connection isn't a side quest for you — {left.strip().lower()} "
                     f"is close to the center of what your life is actually about.",
        "The Artist": f"You don't just experience {left.strip().lower()} — your chart suggests you're built to "
                      f"turn it into something others can feel too.",
        "The Warrior": f"Your chart suggests a life shaped by confrontation, not avoidance of it — "
                       f"{left.strip().lower()} won through bold, direct action.{now}",
        "The Scholar": f"Understanding isn't optional for you — your chart suggests {left.strip().lower()} "
                       f"only becomes real once you've mastered it from the inside.",
        "The Nurturer": f"Your chart suggests your impact shows up less in what you achieve and more in who "
                        f"you help become steady — centered on {left.strip().lower()}.",
        "The Leader": f"People notice you before you try to be noticed. Your chart points toward "
                      f"{left.strip().lower()}, carried through presence rather than performance.{now}",
        "The Transformer": f"Your chart suggests your hardest chapters were never punishment — they were the "
                           f"path through {shadow.lower()} toward {right.strip().lower()}.",
        "The Mystic": f"Your chart suggests the ordinary explanation has never quite satisfied you — "
                      f"something in you has always been reaching past {axis.lower()}.",
        "The Seeker": f"Your chart suggests you're not lost — you're paced by growth itself, moving through "
                      f"{axis.lower()} on a timeline only your chart can explain.",
    }

    return templates.get(
        archetype,
        f"Your chart reveals a specific pattern behind {axis.lower()} — one this report explains in full."
    )


def _identify_challenge(contradictions: dict) -> str:
    """What is the main life challenge."""
    if not contradictions:
        return "Learning to balance multiple competing interests."

    for theme, info in contradictions.items():
        return f"{theme.title()}: {_truncate_at_word(info['resolution'])}"

    return "Integrating internal contradictions."


def _identify_gift(mechanisms: list, yogas: list) -> str:
    """What is the life gift/strength."""
    if mechanisms:
        top = mechanisms[0]
        return f"Strength in {top['name']}: {_truncate_at_word(top['reasoning'])}"

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

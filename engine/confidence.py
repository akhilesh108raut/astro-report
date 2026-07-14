"""
Confidence Scoring: How confident is the astrology engine about predictions?
Scores different life areas and explains the reasoning.
"""

from typing import Any


def score_life_areas(chart: dict) -> dict:
    """
    Score confidence in predictions for 8 major life areas.
    Returns {area: {score (0-100), confidence, reasoning}}.
    """
    planets = chart.get("planets", {})
    analysis = chart.get("analysis", {})
    dasha = chart.get("dasha", {})
    yogas = chart.get("yogas", [])

    scores = {}

    # ─── CAREER & AUTHORITY ───
    career_score = _score_career(planets, yogas, dasha, analysis)
    scores["Career & Authority"] = career_score

    # ─── MARRIAGE & PARTNERSHIPS ───
    marriage_score = _score_marriage(planets, yogas, dasha)
    scores["Marriage & Partnerships"] = marriage_score

    # ─── WEALTH & FINANCES ───
    wealth_score = _score_wealth(planets, yogas, dasha, analysis)
    scores["Wealth & Finances"] = wealth_score

    # ─── HEALTH & LONGEVITY ───
    health_score = _score_health(planets, dasha, analysis)
    scores["Health & Longevity"] = health_score

    # ─── CHILDREN & FAMILY ───
    children_score = _score_children(planets, yogas, dasha)
    scores["Children & Family"] = children_score

    # ─── SPIRITUALITY & GROWTH ───
    spirituality_score = _score_spirituality(planets, yogas, dasha)
    scores["Spirituality & Growth"] = spirituality_score

    # ─── INTELLIGENCE & LEARNING ───
    intelligence_score = _score_intelligence(planets, yogas, dasha)
    scores["Intelligence & Learning"] = intelligence_score

    # ─── FOREIGN & TRAVEL ───
    foreign_score = _score_foreign(planets, dasha)
    scores["Foreign & Travel"] = foreign_score

    return scores


def _score_career(planets, yogas, dasha, analysis) -> dict:
    """Score career potential (0-100)."""
    score = 50
    reasoning = []

    # Check 10th house (career)
    sun_h = planets.get("Sun", {}).get("house")
    mars_h = planets.get("Mars", {}).get("house")
    saturn_h = planets.get("Saturn", {}).get("house")

    if sun_h == 10:
        score += 15
        reasoning.append("Sun in 10th (strong career house)")
    if mars_h == 10:
        score += 12
        reasoning.append("Mars in 10th (leadership)")
    if saturn_h == 10:
        score += 10
        reasoning.append("Saturn in 10th (structured success)")

    # Check Raja Yogas
    if any("Raja" in y["name"] for y in yogas):
        score += 18
        reasoning.append("Raja Yoga present (success indicator)")

    # Check dasha
    if dasha.get("mahadasha") in ("Sun", "Mars", "Saturn", "Jupiter"):
        score += 12
        reasoning.append(f"{dasha.get('mahadasha')} MD active (career activation)")
    elif dasha.get("mahadasha") == "Rahu":
        score -= 10
        reasoning.append("Rahu MD (unconventional, unstable paths)")

    # Check for afflictions
    contradictions = analysis.get("contradictions", {})
    if "career" in contradictions:
        if contradictions["career"]["negative"]:
            score -= 8
            reasoning.append(f"Negative factors: {', '.join(contradictions['career']['negative'][:1])}")

    score = max(0, min(100, score))
    confidence = "High" if score > 75 else "Medium" if score > 50 else "Low"

    return {
        "score": round(score),
        "confidence": confidence,
        "reasoning": reasoning,
    }


def _score_marriage(planets, yogas, dasha) -> dict:
    """Score marriage potential (0-100)."""
    score = 50
    reasoning = []

    # 7th house (marriage)
    venus_h = planets.get("Venus", {}).get("house")
    venus_dign = planets.get("Venus", {}).get("dignity")

    if venus_dign == "exalted":
        score += 20
        reasoning.append("Venus exalted (strong relationships)")
    elif venus_dign == "own":
        score += 15
        reasoning.append("Venus in own sign (comfort in partnerships)")

    if venus_h == 7:
        score += 12
        reasoning.append("Venus in 7th (marriage house)")

    # Check afflictions in 7th
    sun_h = planets.get("Sun", {}).get("house")
    saturn_h = planets.get("Saturn", {}).get("house")

    if sun_h == 7:
        score -= 12
        reasoning.append("Sun in 7th (ego in relationships)")
    if saturn_h == 7:
        score -= 15
        reasoning.append("Saturn in 7th (delays, coldness)")

    # Dasha effects
    if dasha.get("mahadasha") == "Venus":
        score += 15
        reasoning.append("Venus MD (relationship activation)")
    elif dasha.get("mahadasha") == "Saturn":
        score -= 8
        reasoning.append("Saturn MD (relationship tests)")

    score = max(0, min(100, score))
    confidence = "High" if score > 70 else "Medium" if score > 45 else "Low"

    return {
        "score": round(score),
        "confidence": confidence,
        "reasoning": reasoning,
    }


def _score_wealth(planets, yogas, dasha, analysis) -> dict:
    """Score wealth potential (0-100)."""
    score = 50
    reasoning = []

    # 2nd house (wealth), 11th house (gains)
    venus_h = planets.get("Venus", {}).get("house")
    jupiter_h = planets.get("Jupiter", {}).get("house")
    moon_h = planets.get("Moon", {}).get("house")

    if venus_h == 2:
        score += 12
        reasoning.append("Venus in 2nd (luxury, wealth)")
    if moon_h == 2:
        score += 10
        reasoning.append("Moon in 2nd (family wealth)")

    # Check for Dhana Yoga
    if any("Dhana" in y["name"] for y in yogas):
        score += 16
        reasoning.append("Dhana Yoga (wealth accumulation yoga)")

    # Jupiter strength
    jupiter_str = analysis.get("planet_strength_ranking", {}).get("Jupiter", {}).get("strength", 50)
    if jupiter_str > 60:
        score += 10
        reasoning.append(f"Jupiter strong (abundance)")

    # Dasha effects
    if dasha.get("mahadasha") in ("Jupiter", "Venus"):
        score += 10
        reasoning.append(f"{dasha.get('mahadasha')} MD (wealth expansion)")

    score = max(0, min(100, score))
    confidence = "High" if score > 65 else "Medium" if score > 45 else "Low"

    return {
        "score": round(score),
        "confidence": confidence,
        "reasoning": reasoning,
    }


def _score_health(planets, dasha, analysis) -> dict:
    """Score health prospects (0-100)."""
    score = 65  # Assume reasonable health
    reasoning = []

    # Sun (health indicator)
    sun_dign = planets.get("Sun", {}).get("dignity")
    if sun_dign == "debilitated":
        score -= 15
        reasoning.append("Sun debilitated (weak constitution)")
    elif sun_dign == "exalted":
        score += 10
        reasoning.append("Sun exalted (strong vitality)")

    # Check 6th/8th/12th (health problems)
    for p, data in planets.items():
        if data.get("house") == 6:
            score -= 5
            reasoning.append(f"{p} in 6th (health issues)")
        elif data.get("house") == 8:
            score -= 3
            reasoning.append(f"{p} in 8th (chronic conditions)")

    # Dasha effects
    if dasha.get("mahadasha") == "Saturn":
        score -= 8
        reasoning.append("Saturn MD (health testing period)")

    score = max(0, min(100, score))
    confidence = "Medium"  # Health always somewhat uncertain

    return {
        "score": round(score),
        "confidence": confidence,
        "reasoning": reasoning,
    }


def _score_children(planets, yogas, dasha) -> dict:
    """Score children prospects (0-100)."""
    score = 50
    reasoning = []

    # 5th house (children)
    jupiter_h = planets.get("Jupiter", {}).get("house")
    if jupiter_h == 5:
        score += 20
        reasoning.append("Jupiter in 5th (blessed with children)")

    # Check 5th lord
    venus_h = planets.get("Venus", {}).get("house")
    sun_h = planets.get("Sun", {}).get("house")

    if venus_h in (5, 7):
        score += 10
        reasoning.append("5th/7th lord well-placed")

    # Afflictions
    if sun_h == 5 and sun_h == 5:
        score -= 10
        reasoning.append("Sun in 5th (few children, delays)")

    score = max(0, min(100, score))
    confidence = "Medium"

    return {
        "score": round(score),
        "confidence": confidence,
        "reasoning": reasoning,
    }


def _score_spirituality(planets, yogas, dasha) -> dict:
    """Score spiritual development potential (0-100)."""
    score = 50
    reasoning = []

    # 8th, 9th, 12th houses (spirituality)
    jupiter_h = planets.get("Jupiter", {}).get("house")
    moon_h = planets.get("Moon", {}).get("house")

    if jupiter_h in (8, 9, 12):
        score += 20
        reasoning.append(f"Jupiter in moksha house ({jupiter_h})")

    # Ketu (spirituality)
    ketu_h = planets.get("Ketu", {}).get("house")
    if ketu_h in (8, 9, 12):
        score += 15
        reasoning.append(f"Ketu in moksha house ({ketu_h})")

    # Future dasha
    if dasha.get("mahadasha") in ("Jupiter", "Saturn"):
        score += 10
        reasoning.append(f"{dasha.get('mahadasha')} MD (wisdom period ahead)")

    score = max(0, min(100, score))
    confidence = "Medium"

    return {
        "score": round(score),
        "confidence": confidence,
        "reasoning": reasoning,
    }


def _score_intelligence(planets, yogas, dasha) -> dict:
    """Score intellectual potential (0-100)."""
    score = 50
    reasoning = []

    # Mercury (intellect)
    mercury_str = planets.get("Mercury", {}).get("dignity")
    if mercury_str == "exalted":
        score += 18
        reasoning.append("Mercury exalted (exceptional intellect)")
    elif mercury_str == "own":
        score += 12
        reasoning.append("Mercury in own sign (good communication)")

    # Moon (mind)
    moon_str = planets.get("Moon", {}).get("dignity")
    if moon_str == "exalted":
        score += 10
        reasoning.append("Moon exalted (clear thinking)")

    score = max(0, min(100, score))
    confidence = "High"

    return {
        "score": round(score),
        "confidence": confidence,
        "reasoning": reasoning,
    }


def _score_foreign(planets, dasha) -> dict:
    """Score foreign/travel prospects (0-100)."""
    score = 50
    reasoning = []

    # 9th/12th (foreign)
    rahu_h = planets.get("Rahu", {}).get("house")
    if rahu_h in (9, 12):
        score += 20
        reasoning.append(f"Rahu in {rahu_h} (foreign settlement)")

    # Dasha
    if dasha.get("mahadasha") == "Rahu":
        score += 12
        reasoning.append("Rahu MD (foreign connections)")

    score = max(0, min(100, score))
    confidence = "Medium"

    return {
        "score": round(score),
        "confidence": confidence,
        "reasoning": reasoning,
    }

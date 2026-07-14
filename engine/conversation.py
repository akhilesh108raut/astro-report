"""
Conversational AI: Answer questions about a chart using structured reasoning.
Uses the chart's analysis layers to generate contextual answers.
"""

from typing import Any
import re


COMMON_QUESTIONS = {
    "career": [
        "What does my chart say about career?",
        "Will I be successful?",
        "What career path suits me?",
        "When will my career peak?",
    ],
    "marriage": [
        "When will I get married?",
        "What does my chart say about marriage?",
        "Will my marriage be happy?",
        "What type of partner suits me?",
    ],
    "wealth": [
        "Will I be wealthy?",
        "When will I accumulate wealth?",
        "Does my chart show financial success?",
    ],
    "health": [
        "What health issues should I watch for?",
        "Will I live long?",
        "What does my chart say about health?",
    ],
    "spirituality": [
        "Am I spiritual?",
        "Will I achieve spiritual awakening?",
        "When is my spiritual period?",
    ],
    "dasha": [
        "What does my current dasha mean?",
        "What's happening in my current period?",
        "When does this dasha end?",
        "What should I expect in the next dasha?",
    ],
    "strength": [
        "What are my strengths?",
        "What's my biggest advantage?",
        "What am I naturally good at?",
    ],
    "challenge": [
        "What are my challenges?",
        "What should I watch out for?",
        "What's my biggest test?",
    ],
}


def categorize_question(question: str) -> str:
    """Categorize a question into a life area."""
    q_lower = question.lower()

    categories = {
        "marriage": ["marri", "spouse", "partner", "relationship", "love", "romance", "wife", "husband"],  # marri* matches marry/marriage/married
        "career": ["career", "job", "profession", "success", "work", "business", "achievement", "authority"],
        "wealth": ["wealth", "money", "finance", "rich", "abundant", "income", "prosperous"],
        "health": ["health", "disease", "illness", "live long", "longevity", "wellbeing", "constitution"],
        "spirituality": ["spiritual", "enlightenment", "meditation", "guru", "moksha", "awakening"],
        "dasha": ["dasha", "period", "phase", "current", "next", "upcoming"],
        "strength": ["strength", "talent", "gift", "advantage", "good at", "excel"],
        "challenge": ["challenge", "problem", "struggle", "difficult", "test", "obstacle"],
    }

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in q_lower:
                return category

    return "general"


def answer_question(question: str, chart: dict) -> dict:
    """Generate an answer to a question about the chart."""
    category = categorize_question(question)
    analysis = chart.get("analysis", {})
    confidence = chart.get("confidence_scores", {})
    dna = chart.get("chart_dna", {})
    timeline = chart.get("timeline", {})
    dasha = chart.get("dasha", {})
    planets = chart.get("planets", {})

    # Build answer based on category
    if category == "career":
        return _answer_career(chart, analysis, confidence, dna)
    elif category == "marriage":
        return _answer_marriage(chart, analysis, confidence)
    elif category == "wealth":
        return _answer_wealth(chart, analysis, confidence)
    elif category == "health":
        return _answer_health(chart, analysis, confidence)
    elif category == "spirituality":
        return _answer_spirituality(chart, analysis, confidence, dna)
    elif category == "dasha":
        return _answer_dasha(chart, dasha, timeline)
    elif category == "strength":
        return _answer_strength(chart, analysis, dna)
    elif category == "challenge":
        return _answer_challenge(chart, analysis)
    else:
        return _answer_general(chart, dna, analysis)


def _answer_career(chart, analysis, confidence, dna) -> dict:
    """Answer career-related questions."""
    score = confidence.get("Career & Authority", {}).get("score", 50)
    mechanisms = analysis.get("dominant_mechanisms", [])
    contradictions = analysis.get("contradictions", {})
    dasha = chart.get("dasha", {})

    answer = f"Your chart shows a {score}/100 confidence for career success.\n\n"

    # Key mechanisms
    career_mechanisms = [m for m in mechanisms if "career" in m.get("reasoning", "").lower() or "authority" in m["name"]]
    if career_mechanisms:
        answer += f"**Key Strengths:**\n"
        for mech in career_mechanisms[:2]:
            answer += f"• {mech['name']} — {mech['reasoning'][:100]}...\n"
        answer += "\n"

    # Current dasha impact
    current_md = dasha.get("mahadasha", "")
    if current_md == "Rahu":
        answer += f"**Current Period ({current_md} Mahadasha):**\n"
        answer += "You're in a transformative career period. Expect unconventional opportunities and rapid change.\n"
        answer += "Success comes through adaptability rather than traditional paths.\n\n"
    elif current_md == "Saturn":
        answer += f"**Current Period ({current_md} Mahadasha):**\n"
        answer += "This is a building phase. Slow, steady progress through discipline and hard work.\n\n"
    elif current_md == "Jupiter":
        answer += f"**Current Period ({current_md} Mahadasha):**\n"
        answer += "Expansion period! Your career can grow significantly through learning and networking.\n\n"

    # Contradictions
    if "career" in contradictions:
        career_info = contradictions["career"]
        answer += f"**Important Note:**\n{career_info['resolution']}\n"

    answer += f"\n**Next Career Shift:** Check the timeline for dasha transitions."

    return {
        "answer": answer,
        "category": "career",
        "confidence": score,
        "sources": ["dominant_factors", "dasha", "contradictions"]
    }


def _answer_marriage(chart, analysis, confidence) -> dict:
    """Answer marriage-related questions."""
    score = confidence.get("Marriage & Partnerships", {}).get("score", 50)
    planets = chart.get("planets", {})
    contradictions = analysis.get("contradictions", {})

    answer = f"Your chart shows a {score}/100 confidence for marriage happiness.\n\n"

    venus = planets.get("Venus", {})
    sun = planets.get("Sun", {})

    answer += f"**Current Planetary Indicators:**\n"
    if venus.get("dignity") in ("exalted", "own"):
        answer += f"• Venus is {venus['dignity']} — Strong for relationships\n"
    if sun.get("house") == 7:
        answer += f"• Sun in 7th — Ego can be a factor in relationships. Work on compromise.\n"

    if "marriage" in contradictions:
        marriage_info = contradictions["marriage"]
        answer += f"\n**Relationship Dynamics:**\n{marriage_info['resolution']}\n"

    if score < 50:
        answer += f"\n**Guidance:** Focus on emotional maturity and clear communication.\n"
        answer += "Marriage is possible but requires patience and understanding.\n"
    else:
        answer += f"\n**Good News:** Your chart supports stable, happy partnerships.\n"

    return {
        "answer": answer,
        "category": "marriage",
        "confidence": score,
        "sources": ["planets", "contradictions"]
    }


def _answer_wealth(chart, analysis, confidence) -> dict:
    """Answer wealth-related questions."""
    score = confidence.get("Wealth & Finances", {}).get("score", 50)
    mechanisms = analysis.get("dominant_mechanisms", [])
    planets = chart.get("planets", {})

    answer = f"Your chart shows a {score}/100 confidence for wealth accumulation.\n\n"

    answer += f"**Wealth Indicators:**\n"
    if planets.get("Moon", {}).get("house") == 2:
        answer += "• Moon in 2nd — Family wealth and steady accumulation\n"
    if planets.get("Jupiter", {}).get("house") in (2, 11):
        answer += "• Jupiter in wealth houses — Benefic for prosperity\n"

    if score > 60:
        answer += f"\n**Outlook:** Solid financial stability. Build through consistent effort.\n"
    else:
        answer += f"\n**Path to Wealth:** Focus on financial education and strategic planning.\n"

    answer += f"**Timeline:** Major gains likely after current dasha transitions.\n"

    return {
        "answer": answer,
        "category": "wealth",
        "confidence": score,
        "sources": ["planets", "houses"]
    }


def _answer_health(chart, analysis, confidence) -> dict:
    """Answer health-related questions."""
    score = confidence.get("Health & Longevity", {}).get("score", 50)
    planets = chart.get("planets", {})

    answer = f"Your chart shows a {score}/100 health outlook.\n\n"

    answer += f"**Health Considerations:**\n"
    sun = planets.get("Sun", {})
    if sun.get("dignity") == "debilitated":
        answer += "• Sun debilitated — Watch for weak constitution. Build immunity through yoga/exercise.\n"

    if planets.get("Saturn", {}).get("house") == 1:
        answer += "• Saturn in lagna — Early health challenges, but strong longevity later.\n"

    answer += f"\n**Recommendation:** Regular health monitoring and preventive care.\n"
    answer += "Your constitution strengthens significantly after age 36 (Saturn maturity).\n"

    return {
        "answer": answer,
        "category": "health",
        "confidence": score,
        "sources": ["planets", "dignity"]
    }


def _answer_spirituality(chart, analysis, confidence, dna) -> dict:
    """Answer spirituality-related questions."""
    score = confidence.get("Spirituality & Growth", {}).get("score", 50)
    planets = chart.get("planets", {})

    answer = f"Your spiritual inclination score: {score}/100.\n\n"

    if planets.get("Jupiter", {}).get("house") in (8, 9, 12):
        answer += f"**Strong Spiritual Markers:**\n"
        answer += "Your chart indicates genuine spiritual potential.\n"
        answer += "Past-life merits have brought you philosophical interests.\n\n"

    answer += f"**Shadow Theme:** {dna.get('shadow_theme', 'Unknown')}\n"
    answer += "Work with this shadow theme — it's your greatest teacher.\n\n"

    answer += f"**Spiritual Path:** Meditation, study of classical texts, and service.\n"

    return {
        "answer": answer,
        "category": "spirituality",
        "confidence": score,
        "sources": ["planets", "dna"]
    }


def _answer_dasha(chart, dasha, timeline) -> dict:
    """Answer dasha-related questions."""
    current_md = dasha.get("mahadasha", "Unknown")
    current_ad = dasha.get("antardasha", "Unknown")
    md_end = dasha.get("mahadasha_end", "Unknown")

    answer = f"**Current Dasha Period:**\n"
    answer += f"Mahadasha: {current_md} (ends {md_end})\n"
    answer += f"Antardasha: {current_ad}\n\n"

    dasha_meanings = {
        "Rahu": "Unconventional growth, rapid change, experimentation. Expect the unexpected.",
        "Saturn": "Building phase. Slow, steady progress through discipline. Tests your resilience.",
        "Jupiter": "Expansion, wisdom, generosity. This is your growth period.",
        "Venus": "Relationships, creativity, luxury. Focus on what brings joy.",
        "Mars": "Action, courage, competition. Peak energy for physical/career pursuits.",
        "Mercury": "Communication, learning, business. Intellectual growth phase.",
        "Sun": "Leadership, authority, ego. Your presence becomes more visible.",
        "Moon": "Emotions, nurturing, introspection. Focus on inner peace.",
        "Ketu": "Spirituality, letting go, past-life lessons. Mystical period.",
    }

    meaning = dasha_meanings.get(current_md, "Complex transformation period.")
    answer += f"**What This Means:**\n{meaning}\n\n"

    answer += f"**Next Major Shift:** {dasha.get('upcoming_dashas', [{}])[1].get('lord', 'Unknown')} "
    answer += f"Mahadasha starts in {dasha.get('upcoming_dashas', [{}])[1].get('start', 'Unknown')}\n"

    return {
        "answer": answer,
        "category": "dasha",
        "confidence": 90,
        "sources": ["dasha"]
    }


def _answer_strength(chart, analysis, dna) -> dict:
    """Answer questions about strengths."""
    mechanisms = analysis.get("dominant_mechanisms", [])
    dominant_planet = dna.get("dominant_planet", "Unknown")

    answer = f"**Your Greatest Strengths:**\n\n"

    answer += f"**Dominant Planet: {dominant_planet}**\n"
    answer += f"This is your core strength. You naturally excel in {dominant_planet} qualities.\n\n"

    answer += f"**Top Mechanisms:**\n"
    for i, mech in enumerate(mechanisms[:3], 1):
        answer += f"{i}. {mech['name']} — Strength: {mech['strength']:.0f}%\n"

    answer += f"\n**Archetype:** {dna.get('archetype_name', 'Unknown')}\n"
    answer += f"Your natural role: {dna.get('one_liner', '')}\n"

    return {
        "answer": answer,
        "category": "strength",
        "confidence": 85,
        "sources": ["analysis", "dna"]
    }


def _answer_challenge(chart, analysis) -> dict:
    """Answer questions about challenges."""
    contradictions = analysis.get("contradictions", {})
    mechanisms = analysis.get("dominant_mechanisms", [])

    answer = f"**Your Life Challenges:**\n\n"

    if contradictions:
        answer += f"**Internal Contradictions to Resolve:**\n"
        for theme, info in contradictions.items():
            answer += f"• {theme.title()}: {info['negative'][:100]}...\n"
        answer += "\n"

    answer += f"**How to Work With Them:**\n"
    answer += "1. **Awareness** — You now know the exact pattern.\n"
    answer += "2. **Timing** — Dasha periods activate different mechanisms.\n"
    answer += "3. **Growth** — Each challenge is a teacher.\n\n"

    answer += f"**The Good News:** These aren't weaknesses. They're your evolution points.\n"

    return {
        "answer": answer,
        "category": "challenge",
        "confidence": 80,
        "sources": ["contradictions"]
    }


def _answer_general(chart, dna, analysis) -> dict:
    """Comprehensive general chart reading — covers all life areas."""
    lagna   = chart.get("lagna", {})
    moon    = chart.get("moon", {})
    dasha   = chart.get("dasha", {})
    planets = chart.get("planets", {})
    yogas   = chart.get("yogas", [])
    adv     = chart.get("advanced_predictions", {})
    det     = adv.get("detailed_predictions", {})
    conf    = chart.get("confidence_scores", {}).get("scores", {})

    venus   = planets.get("Venus", {})
    jupiter = planets.get("Jupiter", {})
    saturn  = planets.get("Saturn", {})
    sun     = planets.get("Sun", {})
    mars    = planets.get("Mars", {})

    yoga_str = ", ".join([y["name"] for y in yogas[:4]]) or "no major yogas"

    career  = det.get("career", {})
    love    = det.get("marriage_love", {})
    wealth  = det.get("wealth", {})
    health  = det.get("health", {})
    dharma  = adv.get("dharma", {})
    past    = adv.get("past_lives", {})
    karma   = adv.get("karma_debts", {})

    answer  = f"BIRTH CHART READING\n\n"

    answer += f"CORE IDENTITY\n"
    answer += f"Your {lagna.get('sign')} Ascendant (Lord: {lagna.get('lord')}) at {lagna.get('degree',0):.1f}° "
    answer += f"shapes your outer personality. Moon in {moon.get('sign')} "
    answer += f"({moon.get('nakshatra')} Pada {moon.get('nakshatra_pada')}) is your emotional core. "
    answer += f"Sun in {chart.get('sun_sign')} defines your soul's purpose. "
    answer += f"Archetype: {dna.get('archetype', 'The Seeker')} — {dna.get('one_liner', '')}\n\n"

    answer += f"CAREER (House 10 | Saturn | Sun)\n"
    answer += f"Saturn in {saturn.get('sign','?')} House {saturn.get('house','?')} ({saturn.get('dignity','?')}). "
    answer += f"Sun in {sun.get('sign','?')} House {sun.get('house','?')} ({sun.get('dignity','?')}). "
    answer += f"{career.get('career_potential','Moderate')} potential. "
    answer += f"Ideal careers: {', '.join(career.get('ideal_careers',[])[:3]) or 'leadership, analysis, teaching'}. "
    answer += f"Peak periods: {', '.join(career.get('peak_career_periods',[])[:2]) or 'Age 30-42'}. "
    answer += f"Advancement timing: {career.get('advancement_timing','Post-Saturn Return')}.\n\n"

    answer += f"MARRIAGE & RELATIONSHIPS (House 7 | Venus | Jupiter)\n"
    answer += f"Venus in {venus.get('sign','?')} House {venus.get('house','?')} ({venus.get('dignity','?')}). "
    answer += f"Jupiter in {jupiter.get('sign','?')} House {jupiter.get('house','?')} ({jupiter.get('dignity','?')}). "
    answer += f"{love.get('relationship_potential','Moderate')} relationship potential. "
    answer += f"Marriage timing: {love.get('marriage_timing','Age 25-35')}. "
    answer += f"Partner traits: {', '.join(love.get('partner_traits',[])[:3]) or 'caring, stable, compatible'}. "
    answer += f"Longevity: {love.get('longevity_of_marriage','stable with effort')}.\n\n"

    answer += f"WEALTH & FINANCES (House 2 & 11 | Jupiter)\n"
    answer += f"Jupiter in {jupiter.get('sign','?')} House {jupiter.get('house','?')} — primary wealth significator. "
    answer += f"{wealth.get('wealth_potential','Moderate')} potential. "
    answer += f"Path: {wealth.get('accumulation_path','steady and diversified')}. "
    answer += f"Peaks: {', '.join(wealth.get('wealth_peaks',[])[:2]) or 'Age 36-48'}. "
    answer += f"Best investments: {', '.join(wealth.get('investment_areas',[])[:2]) or 'real estate, equity'}.\n\n"

    answer += f"HEALTH & LONGEVITY (House 1 & 6 | Sun | Saturn)\n"
    answer += f"{health.get('overall_health','Good')} constitution. "
    answer += (f"Watch for: {', '.join(health.get('vulnerabilities',[]))}. "
               if health.get('vulnerabilities') else "No major vulnerabilities indicated. ")
    answer += f"Strengthens after age {health.get('strengthening_age',36)}. "
    answer += f"Outlook: {health.get('longevity_outlook','Good with care')}.\n\n"

    answer += f"KARMA & DHARMA (Rahu/Ketu Axis)\n"
    answer += f"Past life mastery: {past.get('past_life_focus','spiritual knowledge')}. "
    answer += f"Skills: {', '.join(past.get('karmic_skills',[])[:3]) or 'wisdom, intuition'}. "
    answer += f"This life's dharma: {dharma.get('life_purpose','growth and contribution')}. "
    answer += f"Mission: {dharma.get('core_mission','evolve and serve')}. "
    answer += f"Karma path: {karma.get('karma_resolution_timeline','gradual transformation')}.\n\n"

    answer += f"CURRENT DASHA PERIOD\n"
    answer += f"Mahadasha: {dasha.get('mahadasha')} (ends {dasha.get('mahadasha_end')}). "
    answer += f"Antardasha: {dasha.get('antardasha')} (ends {dasha.get('antardasha_end')}). "
    answer += f"Active yogas: {yoga_str}. "
    answer += f"Shadow theme to integrate: {dna.get('shadow_theme','self-discovery')}.\n\n"

    answer += f"KEY TIMING (Next 10 Years)\n"
    pred   = chart.get("predictions", {}).get("predictions", {})
    events = pred.get("major_events", [])
    if events:
        for ev in events[:3]:
            answer += f"• {ev.get('event','Event')}: {ev.get('date','')} — {ev.get('description','')[:80]}\n"
    else:
        answer += f"• Saturn Return (age 29-30): Major life maturity milestone\n"
        answer += f"• Next dasha shift: {dasha.get('upcoming_dashas',[{}])[1].get('lord','Unknown')} Mahadasha\n"

    return {
        "answer": answer,
        "category": "general",
        "confidence": 80,
        "sources": ["lagna", "planets", "dasha", "predictions", "advanced_predictions"],
    }

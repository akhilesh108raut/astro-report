"""
Prediction System: Forecast major life events based on dasha, transits, and chart analysis.
Provides year-by-year predictions and event timing.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import math


class LifeEvent:
    """A predicted life event with timing and confidence."""

    def __init__(
        self,
        event_type: str,
        description: str,
        start_date: datetime,
        end_date: datetime = None,
        confidence: int = 50,
        severity: str = "moderate",
        life_area: str = "general",
        reasoning: str = "",
    ):
        self.event_type = event_type  # "opportunity", "challenge", "milestone", etc.
        self.description = description
        self.start_date = start_date
        self.end_date = end_date or start_date
        self.confidence = confidence  # 0-100
        self.severity = severity  # "minor", "moderate", "major"
        self.life_area = life_area  # career, marriage, wealth, health, etc.
        self.reasoning = reasoning

    def to_dict(self):
        return {
            "event_type": self.event_type,
            "description": self.description,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "confidence": self.confidence,
            "severity": self.severity,
            "life_area": self.life_area,
            "reasoning": self.reasoning,
        }


class PredictionEngine:
    """Generate predictions based on Vedic astrological principles."""

    # Dasha characteristics and their meanings
    DASHA_CHARACTERISTICS = {
        "Sun": {
            "themes": ["authority", "leadership", "visibility", "ego"],
            "challenges": ["arrogance", "burnout", "health issues"],
            "opportunities": ["promotions", "recognition", "leadership roles"],
            "life_areas": ["career", "health", "intelligence"],
        },
        "Moon": {
            "themes": ["emotions", "family", "nurturing", "introspection"],
            "challenges": ["mood swings", "family conflicts", "lethargy"],
            "opportunities": ["family harmony", "emotional healing", "home"],
            "life_areas": ["marriage", "family", "health"],
        },
        "Mars": {
            "themes": ["action", "courage", "competition", "passion"],
            "challenges": ["aggression", "accidents", "conflicts"],
            "opportunities": ["success in competition", "physical achievements"],
            "life_areas": ["career", "health", "marriage"],
        },
        "Mercury": {
            "themes": ["communication", "learning", "business", "intellect"],
            "challenges": ["confusion", "speech issues", "nervous disorders"],
            "opportunities": ["business success", "intellectual growth", "travel"],
            "life_areas": ["career", "intelligence", "foreign"],
        },
        "Jupiter": {
            "themes": ["expansion", "wisdom", "prosperity", "growth"],
            "challenges": ["excess", "overconfidence", "delays"],
            "opportunities": ["major gains", "education", "spiritual growth"],
            "life_areas": ["wealth", "spirituality", "intelligence"],
        },
        "Venus": {
            "themes": ["relationships", "creativity", "luxury", "pleasure"],
            "challenges": ["indulgence", "relationship issues", "excess"],
            "opportunities": ["marriage", "creativity", "financial gains"],
            "life_areas": ["marriage", "wealth", "creativity"],
        },
        "Saturn": {
            "themes": ["discipline", "hard work", "restrictions", "maturity"],
            "challenges": ["delays", "hardship", "isolation"],
            "opportunities": ["lasting success", "maturity", "spiritual growth"],
            "life_areas": ["career", "spirituality", "health"],
        },
        "Rahu": {
            "themes": ["innovation", "unconventional", "sudden change", "obsession"],
            "challenges": ["deception", "confusion", "sudden losses"],
            "opportunities": ["innovation", "sudden gains", "unique experiences"],
            "life_areas": ["career", "wealth", "foreign"],
        },
        "Ketu": {
            "themes": ["spirituality", "endings", "mysticism", "detachment"],
            "challenges": ["losses", "confusion", "isolation"],
            "opportunities": ["spiritual awakening", "enlightenment", "detachment"],
            "life_areas": ["spirituality", "health"],
        },
    }

    def __init__(self, chart: dict, current_year: int = 2026):
        self.chart = chart
        self.current_year = current_year
        self.current_date = datetime.now()

    def generate_predictions(self, years_ahead: int = 10) -> Dict[str, Any]:
        """
        Generate comprehensive predictions for the next N years.

        Returns:
            Dict with yearly predictions, major events, and life area forecasts
        """

        predictions = {
            "generated_at": self.current_date.isoformat(),
            "years_ahead": years_ahead,
            "yearly_forecasts": [],
            "major_events": [],
            "life_area_outlook": {},
            "next_major_transitions": [],
        }

        # Get dasha information
        dasha_info = self.chart.get("dasha", {})
        current_md = dasha_info.get("mahadasha", "Unknown")
        upcoming_dashas = dasha_info.get("upcoming_dashas", [])

        # Generate yearly forecasts
        for year_offset in range(years_ahead):
            forecast_year = self.current_year + year_offset
            forecast = self._forecast_year(forecast_year, current_md)
            predictions["yearly_forecasts"].append(forecast)

        # Major events
        predictions["major_events"] = self._predict_major_events(
            years_ahead, upcoming_dashas
        )

        # Life area outlook
        predictions["life_area_outlook"] = self._forecast_life_areas(
            years_ahead, current_md
        )

        # Next transitions
        predictions["next_major_transitions"] = self._identify_transitions(
            upcoming_dashas, years_ahead
        )

        return predictions

    def _forecast_year(self, year: int, active_md: str) -> Dict[str, Any]:
        """Forecast for a specific year."""

        days_in_year = 365 if year % 4 != 0 else 366
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31)

        # Dasha characteristics
        dasha_chars = self.DASHA_CHARACTERISTICS.get(active_md, {})

        # Overall theme for the year
        themes = dasha_chars.get("themes", [])
        opportunities = dasha_chars.get("opportunities", [])
        challenges = dasha_chars.get("challenges", [])

        # Confidence decreases with years ahead
        years_ahead = year - self.current_year
        base_confidence = max(50 - years_ahead * 3, 30)

        forecast = {
            "year": year,
            "theme": f"{active_md} Mahadasha - {', '.join(themes[:2])}",
            "opportunities": opportunities,
            "challenges": challenges,
            "key_months": self._identify_key_months(year, active_md),
            "confidence": base_confidence,
            "life_areas_affected": dasha_chars.get("life_areas", []),
            "guidance": self._generate_yearly_guidance(active_md, year),
        }

        return forecast

    def _identify_key_months(self, year: int, mahadasha: str) -> List[Dict]:
        """Identify key months in the year based on antardasha transitions."""

        # Simplified: assume each antardasha lasts ~12/9 = 1.33 months
        key_months = []

        for month in [3, 6, 9, 12]:  # Key months for review
            key_months.append(
                {
                    "month": month,
                    "event": f"Potential shift in {mahadasha} activation",
                    "type": "transition",
                }
            )

        return key_months

    def _predict_major_events(self, years_ahead: int, upcoming_dashas: List) -> List:
        """Predict major life events."""

        events = []

        # Saturn Return (age 29-30)
        birth_date = self._parse_birth_date()
        if birth_date:
            saturn_return = birth_date + timedelta(days=365 * 29)
            if saturn_return.year <= self.current_year + years_ahead:
                events.append(
                    {
                        "event": "Saturn Return",
                        "date": saturn_return.isoformat(),
                        "type": "milestone",
                        "description": "Major life transition and maturity phase. Important for career and personal growth.",
                        "confidence": 90,
                        "severity": "major",
                    }
                )

        # Dasha transitions
        for dasha in upcoming_dashas:
            start_year = dasha.get("start", "").split("-")[0]
            if start_year and self.current_year < int(start_year) <= self.current_year + years_ahead:
                events.append(
                    {
                        "event": f"{dasha.get('lord')} Mahadasha begins",
                        "date": dasha.get("start"),
                        "type": "transition",
                        "description": f"Major shift in life theme and opportunities. {dasha.get('lord')} becomes dominant.",
                        "confidence": 95,
                        "severity": "major",
                    }
                )

        return sorted(events, key=lambda x: x.get("date", ""))

    def _forecast_life_areas(self, years_ahead: int, current_md: str) -> Dict:
        """Forecast for each major life area."""

        life_areas = {
            "career": {"outlook": "Neutral", "key_timing": "Q2-Q3", "confidence": 60},
            "marriage": {"outlook": "Neutral", "key_timing": "Q3-Q4", "confidence": 55},
            "wealth": {"outlook": "Positive", "key_timing": "Q1-Q2", "confidence": 65},
            "health": {"outlook": "Good", "key_timing": "Throughout", "confidence": 70},
            "spirituality": {"outlook": "Neutral", "key_timing": "Q4", "confidence": 50},
        }

        # Adjust based on current dasha
        dasha_chars = self.DASHA_CHARACTERISTICS.get(current_md, {})
        affected_areas = dasha_chars.get("life_areas", [])

        for area in affected_areas:
            if area in life_areas:
                life_areas[area]["outlook"] = "Positive"
                life_areas[area]["confidence"] = min(85, life_areas[area]["confidence"] + 15)

        return life_areas

    def _identify_transitions(self, upcoming_dashas: List, years_ahead: int) -> List:
        """Identify major life transitions."""

        transitions = []

        for i, dasha in enumerate(upcoming_dashas):
            if i >= years_ahead:
                break

            start_date = dasha.get("start", "")
            lord = dasha.get("lord", "Unknown")

            if start_date:
                chars = self.DASHA_CHARACTERISTICS.get(lord, {})
                transitions.append(
                    {
                        "date": start_date,
                        "period": f"{lord} Mahadasha",
                        "duration_years": dasha.get("duration", 0),
                        "themes": chars.get("themes", []),
                        "key_focus": f"Focus on {', '.join(chars.get('themes', [])[:2])}",
                        "preparation": self._transition_preparation(lord),
                    }
                )

        return transitions

    def _transition_preparation(self, mahadasha: str) -> str:
        """Suggest preparation for upcoming dasha."""

        prep_hints = {
            "Sun": "Focus on leadership skills and health management",
            "Moon": "Prioritize emotional stability and family relationships",
            "Mars": "Channel aggressive energy into sports or competition",
            "Mercury": "Develop communication and business skills",
            "Jupiter": "Embrace learning and spiritual growth",
            "Venus": "Nurture relationships and creative pursuits",
            "Saturn": "Build discipline and long-term strategies",
            "Rahu": "Stay grounded and manage obsessions",
            "Ketu": "Practice meditation and spiritual work",
        }

        return prep_hints.get(mahadasha, "Adapt to changing circumstances")

    def _generate_yearly_guidance(self, mahadasha: str, year: int) -> str:
        """Generate guidance for the year."""

        base_guidance = {
            "Sun": "Take leadership initiatives. Focus on health and visibility.",
            "Moon": "Nurture family bonds. Work on emotional balance.",
            "Mars": "Channel energy into physical projects. Assert yourself wisely.",
            "Mercury": "Learn new skills. Communicate clearly. Travel if possible.",
            "Jupiter": "Expand knowledge. Be generous. Growth is available.",
            "Venus": "Enjoy relationships. Pursue creative projects. Invest in beauty.",
            "Saturn": "Work hard. Build lasting foundations. Patience is key.",
            "Rahu": "Embrace change. Stay ethical. Avoid obsessions.",
            "Ketu": "Meditate. Let go. Focus on spirituality.",
        }

        return base_guidance.get(mahadasha, "Adapt to circumstances and trust the process.")

    def _parse_birth_date(self) -> datetime:
        """Parse birth date from chart."""
        try:
            meta = self.chart.get("meta", {})
            birth_date = meta.get("birth_date", "")
            if birth_date:
                parts = birth_date.split("-")
                if len(parts) == 3:
                    return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        except:
            pass
        return None


def generate_predictions(chart: dict, current_year: int = 2026, years_ahead: int = 10) -> Dict:
    """
    Main function to generate predictions for a chart.

    Args:
        chart: Complete birth chart dict
        current_year: Current year for predictions
        years_ahead: How many years to predict

    Returns:
        Dict with complete predictions
    """

    engine = PredictionEngine(chart, current_year)
    predictions = engine.generate_predictions(years_ahead)

    return {
        "predictions": predictions,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "native": chart.get("meta", {}).get("name", "Unknown"),
            "current_dasha": chart.get("dasha", {}).get("mahadasha", "Unknown"),
        },
    }


def format_predictions_for_display(predictions_data: Dict) -> str:
    """Format predictions into readable text."""

    text = []
    preds = predictions_data.get("predictions", {})

    # Title
    text.append("=" * 70)
    text.append("VEDIC ASTROLOGY PREDICTIONS")
    text.append("=" * 70)

    # Major events
    major_events = preds.get("major_events", [])
    if major_events:
        text.append("\nMAJOR LIFE EVENTS")
        text.append("-" * 70)
        for event in major_events:
            text.append(f"\n{event['event']}")
            text.append(f"  Date: {event['date']}")
            text.append(f"  Type: {event['type']}")
            text.append(f"  {event['description']}")

    # Yearly forecasts (next 3 years only for display)
    text.append("\n\nYEARLY FORECASTS")
    text.append("-" * 70)
    for forecast in preds.get("yearly_forecasts", [])[:3]:
        year = forecast["year"]
        theme = forecast["theme"]
        text.append(f"\n{year}: {theme}")
        text.append(f"  Opportunities: {', '.join(forecast.get('opportunities', [])[:2])}")
        text.append(f"  Guidance: {forecast['guidance']}")

    # Life area outlook
    text.append("\n\nLIFE AREA OUTLOOK")
    text.append("-" * 70)
    for area, outlook in preds.get("life_area_outlook", {}).items():
        conf = outlook.get("confidence", 0)
        text.append(f"{area.title()}: {outlook.get('outlook')} (Confidence: {conf}%)")

    return "\n".join(text)

"""
Advanced Predictions: Past lives, karma, dharma, and detailed life area forecasts.
Integrates with the base prediction system.
"""

from datetime import datetime
from typing import Dict, List, Any


class KarmaAnalyzer:
    """Analyze past karma and karmic debts."""

    def __init__(self, chart: dict):
        self.chart = chart
        self.planets = chart.get("planets", {})
        self.lagna = chart.get("lagna", {})
        self.dasha = chart.get("dasha", {})

    def analyze_past_lives(self) -> Dict[str, Any]:
        """Analyze past life patterns from chart."""

        ketu_pos = self.planets.get("Ketu", {})
        house = ketu_pos.get("house", 1)
        sign = ketu_pos.get("sign", "Unknown")

        past_life_themes = {
            1: "Self-awareness, spiritual development",
            2: "Wealth accumulation, material mastery",
            3: "Communication, writing, travel",
            4: "Property, family, emotional roots",
            5: "Creativity, children, romance",
            6: "Service, healing, work",
            7: "Relationships, partnerships, harmony",
            8: "Transformation, occult, hidden wisdom",
            9: "Higher learning, spirituality, travel",
            10: "Career, public life, authority",
            11: "Friendships, networks, humanitarian work",
            12: "Spirituality, solitude, liberation",
        }

        return {
            "past_life_focus": past_life_themes.get(house, "Spiritual evolution"),
            "ketu_house": house,
            "ketu_sign": sign,
            "karmic_skills": self._extract_karmic_skills(house),
            "past_mastery": self._describe_past_mastery(house),
            "abandonment_needed": self._abandonment_areas(house),
        }

    def analyze_karma_debts(self) -> Dict[str, Any]:
        """Analyze pending karma and karmic debts."""

        rahu_pos = self.planets.get("Rahu", {})
        eighth_house = self.planets.get("Mars", {}).get("house") == 8

        karmic_debts = []

        # Saturn positions indicate karmic tests
        saturn = self.planets.get("Saturn", {})
        if saturn.get("dignity") == "debilitated":
            karmic_debts.append({
                "area": "Discipline & Responsibility",
                "debt": "Learning through restriction and effort",
                "resolution": "Accept limitations, work hard, build slowly",
                "timeline": "Saturn periods especially",
            })

        # Rahu/Ketu axis shows karmic evolution
        rahu_house = rahu_pos.get("house", 1)
        karmic_debts.append({
            "area": self._rahu_karmic_area(rahu_house),
            "debt": f"Development in house {rahu_house} area",
            "resolution": f"Embrace growth, avoid obsession",
            "timeline": "Rahu mahadasha period",
        })

        # 8th house karma
        if eighth_house:
            karmic_debts.append({
                "area": "Transformation & Healing",
                "debt": "Deep psychological and spiritual work",
                "resolution": "Embrace change, study occult/psychology",
                "timeline": "Throughout life",
            })

        return {
            "pending_karmic_debts": karmic_debts,
            "karma_resolution_timeline": self._karma_timeline(),
            "karmic_lessons_active": self._active_karmic_lessons(),
        }

    def analyze_dharma_purpose(self) -> Dict[str, Any]:
        """Analyze dharma (life purpose) from chart."""

        rahu_pos = self.planets.get("Rahu", {})
        rahu_house = rahu_pos.get("house", 1)
        lagna_lord = self.lagna.get("lord", "Unknown")

        dharma_themes = {
            1: "Self-realization, spiritual development",
            2: "Share knowledge, teach, communicate",
            3: "Build networks, connect communities",
            4: "Nourish family, create home",
            5: "Create art, guide others, inspire",
            6: "Serve humanity, heal, improve",
            7: "Create partnerships, bring harmony",
            8: "Transform consciousness, heal trauma",
            9: "Share wisdom, guide spiritually",
            10: "Lead, build institutions, inspire",
            11: "Network communities, humanitarian work",
            12: "Spiritual liberation, transcendence",
        }

        dharma_description = dharma_themes.get(
            rahu_house, "Spiritual evolution and growth"
        )

        return {
            "life_purpose": dharma_description,
            "dharma_house": rahu_house,
            "core_mission": self._core_mission(rahu_house),
            "dharma_activation_age": self._dharma_activation_age(),
            "soul_growth_areas": self._soul_growth_areas(rahu_house),
            "contribution_to_world": self._world_contribution(rahu_house),
        }

    def _extract_karmic_skills(self, ketu_house: int) -> List[str]:
        """Extract skills from past life (Ketu house)."""
        skills = {
            1: ["Self-awareness", "Spirituality", "Leadership"],
            2: ["Finance", "Materialism mastery", "Speaking"],
            3: ["Writing", "Communication", "Travel"],
            4: ["Property management", "Emotional depth", "Family"],
            5: ["Creativity", "Performance", "Teaching"],
            6: ["Service", "Healing", "Problem-solving"],
            7: ["Relationships", "Diplomacy", "Art"],
            8: ["Occult knowledge", "Transformation", "Healing"],
            9: ["Philosophy", "Spirituality", "Teaching"],
            10: ["Authority", "Organization", "Leadership"],
            11: ["Networking", "Friendship", "Groups"],
            12: ["Mysticism", "Spirituality", "Meditation"],
        }
        return skills.get(ketu_house, ["Spiritual knowledge"])

    def _describe_past_mastery(self, ketu_house: int) -> str:
        """Describe what was mastered in past life."""
        mastery = {
            1: "Self-discipline and spiritual awareness",
            2: "Material success and wealth accumulation",
            3: "Communication and intellectual mastery",
            4: "Family management and emotional balance",
            5: "Creative expression and leadership",
            6: "Service and practical skills",
            7: "Relationship harmony and diplomacy",
            8: "Occult knowledge and transformation",
            9: "Spiritual wisdom and philosophy",
            10: "Career success and public recognition",
            11: "Community building and networks",
            12: "Spiritual practices and meditation",
        }
        return mastery.get(ketu_house, "Spiritual development")

    def _abandonment_areas(self, ketu_house: int) -> str:
        """What needs to be abandoned (Ketu lessons)."""
        abandon = {
            1: "Ego, self-centeredness, pride",
            2: "Material obsession, greed, attachment",
            3: "Excessive talk, gossip, mental chatter",
            4: "Family dependency, emotional clinging",
            5: "Romantic obsession, ego in creativity",
            6: "Perfectionism, hypochondria, service obsession",
            7: "Relationship dependency, people-pleasing",
            8: "Obsession with secrets, power, control",
            9: "Spiritual superiority, dogmatism",
            10: "Career obsession, public image attachment",
            11: "Group dependency, network obsession",
            12: "Escapism, spiritual bypassing",
        }
        return abandon.get(ketu_house, "Attachment and obsession")

    def _rahu_karmic_area(self, rahu_house: int) -> str:
        """What karma is being worked on (Rahu)."""
        areas = {
            1: "Identity & Self-Development",
            2: "Finances & Resources",
            3: "Communication & Intellect",
            4: "Family & Home",
            5: "Creativity & Romance",
            6: "Health & Service",
            7: "Relationships & Partnership",
            8: "Transformation & Intimacy",
            9: "Spirituality & Higher Learning",
            10: "Career & Public Life",
            11: "Friendship & Community",
            12: "Spirituality & Liberation",
        }
        return areas.get(rahu_house, "Life Evolution")

    def _karma_timeline(self) -> str:
        """When karmic resolution typically occurs."""
        current_md = self.dasha.get("mahadasha", "Unknown")

        timeline_hints = {
            "Saturn": "Throughout Saturn period - slow resolution through discipline",
            "Rahu": "Transformative period - sudden karmic shifts",
            "Ketu": "Spiritual resolution - letting go and acceptance",
            "Jupiter": "Expansion period - karmic expansion and opportunity",
        }

        return timeline_hints.get(
            current_md, "Gradual resolution through life experience"
        )

    def _active_karmic_lessons(self) -> List[str]:
        """Current karmic lessons being worked on."""
        lessons = []
        planets = self.planets

        for planet, data in planets.items():
            if data.get("dignity") == "debilitated":
                lessons.append(f"{planet} debilitated - karmic test in {planet} areas")

        return lessons if lessons else ["Balancing karmic patterns"]

    def _core_mission(self, rahu_house: int) -> str:
        """Core life mission based on Rahu house."""
        missions = {
            1: "Develop authentic self, spiritual leadership",
            2: "Create abundance, share prosperity",
            3: "Communicate truth, build networks",
            4: "Create safe home, nurture family",
            5: "Express creativity, inspire others",
            6: "Serve humanity, improve systems",
            7: "Build harmonious partnerships",
            8: "Transform consciousness, heal",
            9: "Share wisdom, guide spiritually",
            10: "Lead and build institutions",
            11: "Unite communities, humanitarian work",
            12: "Spiritual awakening, transcendence",
        }
        return missions.get(rahu_house, "Spiritual evolution")

    def _dharma_activation_age(self) -> int:
        """Age when dharma typically activates."""
        # Typically after first Saturn Return (age 29-30)
        return 30

    def _soul_growth_areas(self, rahu_house: int) -> List[str]:
        """Areas of soul growth."""
        growth = {
            1: ["Self-awareness", "Independence", "Spirituality"],
            2: ["Generosity", "Sharing", "Financial wisdom"],
            3: ["Truth-speaking", "Teaching", "Connection"],
            4: ["Emotional maturity", "Family healing", "Roots"],
            5: ["Creative expression", "Joy", "Leadership"],
            6: ["Compassion", "Service", "Health"],
            7: ["Empathy", "Balance", "Partnership"],
            8: ["Depth", "Transformation", "Intimacy"],
            9: ["Wisdom", "Philosophy", "Spirituality"],
            10: ["Integrity", "Authority", "Purpose"],
            11: ["Inclusivity", "Community", "Cooperation"],
            12: ["Transcendence", "Surrender", "Unity"],
        }
        return growth.get(rahu_house, ["Spiritual growth"])

    def _world_contribution(self, rahu_house: int) -> str:
        """How this person can contribute to the world."""
        contribution = {
            1: "Model authentic living and spirituality",
            2: "Create shared prosperity and generosity",
            3: "Connect people and share important messages",
            4: "Create safe spaces and nurturing environments",
            5: "Inspire and uplift through creativity",
            6: "Serve and improve systems for others",
            7: "Create harmony and balance in relationships",
            8: "Help others transform and heal deeply",
            9: "Share wisdom and guide spiritually",
            10: "Build institutions and inspire leadership",
            11: "Unite communities and serve humanity",
            12: "Model spiritual transcendence and peace",
        }
        return contribution.get(rahu_house, "Contribute to spiritual evolution")


class DetailedLifeAreaPredictions:
    """Detailed predictions for each life area."""

    def __init__(self, chart: dict):
        self.chart = chart
        self.planets = chart.get("planets", {})
        self.dasha = chart.get("dasha", {})
        self.analysis = chart.get("analysis", {})

    def predict_health(self) -> Dict[str, Any]:
        """Detailed health predictions."""
        sun = self.planets.get("Sun", {})
        mars = self.planets.get("Mars", {})
        saturn = self.planets.get("Saturn", {})

        vulnerabilities = []
        if sun.get("dignity") == "debilitated":
            vulnerabilities.append("Heart/vitality - build immunity")
        if mars.get("dignity") == "debilitated":
            vulnerabilities.append("Energy/blood - physical weakening")
        if saturn.get("house") == 1:
            vulnerabilities.append("General weakness in youth - strengthens after 36")

        return {
            "overall_health": "Strong" if not vulnerabilities else "Requires attention",
            "vulnerabilities": vulnerabilities,
            "strengthening_age": 36,
            "key_practices": [
                "Yoga or exercise",
                "Regular sleep",
                "Stress management",
            ],
            "health_warning_periods": self._health_warning_periods(),
            "longevity_outlook": "Good" if len(vulnerabilities) < 2 else "Moderate",
        }

    def predict_wealth(self) -> Dict[str, Any]:
        """Detailed wealth predictions."""
        jupiter = self.planets.get("Jupiter", {})
        saturn = self.planets.get("Saturn", {})
        venus = self.planets.get("Venus", {})

        wealth_indicators = []
        if jupiter.get("dignity") in ("exalted", "own"):
            wealth_indicators.append("Jupiter strong - natural prosperity")
        if saturn.get("dignity") in ("exalted", "own"):
            wealth_indicators.append("Saturn strong - lasting wealth through effort")

        return {
            "wealth_potential": "High" if len(wealth_indicators) > 0 else "Moderate",
            "indicators": wealth_indicators,
            "accumulation_path": self._wealth_path(),
            "wealth_peaks": ["Age 36-42", "Age 48-54"],
            "investment_areas": ["Real estate", "Stocks", "Business"],
            "warning_periods": self._wealth_warning_periods(),
        }

    def predict_career(self) -> Dict[str, Any]:
        """Detailed career predictions."""
        sun = self.planets.get("Sun", {})
        saturn = self.planets.get("Saturn", {})
        mercury = self.planets.get("Mercury", {})

        career_strengths = []
        if sun.get("house") == 10:
            career_strengths.append("10th house Sun - natural leader")
        if saturn.get("dignity") in ("exalted", "own"):
            career_strengths.append("Saturn strong - build lasting career")

        return {
            "career_potential": "High" if len(career_strengths) > 0 else "Moderate",
            "strengths": career_strengths,
            "ideal_careers": self._ideal_careers(),
            "peak_career_periods": ["Age 30-42", "Age 50-60"],
            "challenges": self._career_challenges(),
            "advancement_timing": "Post-Saturn Return (age 30+)",
        }

    def predict_marriage_love(self) -> Dict[str, Any]:
        """Detailed marriage and love predictions."""
        venus = self.planets.get("Venus", {})
        mars = self.planets.get("Mars", {})
        mercury = self.planets.get("Mercury", {})

        relationship_indicators = []
        if venus.get("dignity") in ("exalted", "own"):
            relationship_indicators.append("Venus strong - harmonious relationships")
        if mars.get("house") in (1, 7):
            relationship_indicators.append("Mars in angles - passionate nature")

        return {
            "relationship_potential": "Strong" if len(relationship_indicators) > 0 else "Moderate",
            "indicators": relationship_indicators,
            "marriage_timing": self._marriage_timing(),
            "partner_traits": self._partner_traits(),
            "relationship_challenges": self._relationship_challenges(),
            "key_periods_for_romance": ["Jupiter periods", "Venus periods"],
            "longevity_of_marriage": "Long-term" if len(relationship_indicators) > 0 else "Requires work",
        }

    def _wealth_path(self) -> str:
        """How wealth is accumulated."""
        jupiter = self.planets.get("Jupiter", {})
        saturn = self.planets.get("Saturn", {})

        if jupiter.get("dignity") in ("exalted", "own"):
            return "Natural expansion, inheritance, business growth"
        elif saturn.get("dignity") in ("exalted", "own"):
            return "Hard work, saving, real estate, long-term investments"
        else:
            return "Varied sources, requires effort and planning"

    def _health_warning_periods(self) -> List[str]:
        """Periods requiring health vigilance."""
        return [
            "Age 28-30 (Saturn aspects)",
            "During Saturn MD",
            "Age 54-56 (Saturn Return cycles)",
        ]

    def _wealth_warning_periods(self) -> List[str]:
        """Periods requiring financial caution."""
        return [
            "During Rahu periods",
            "Saturn transits",
            "After major gains (consolidate)",
        ]

    def _ideal_careers(self) -> List[str]:
        """Suitable career paths."""
        planets = self.planets
        careers = []

        if planets.get("Sun", {}).get("dignity") == "exalted":
            careers.extend(["Leadership", "Politics", "CEO"])
        if planets.get("Jupiter", {}).get("dignity") == "exalted":
            careers.extend(["Teaching", "Philosophy", "Law"])
        if planets.get("Mercury", {}).get("dignity") == "exalted":
            careers.extend(["Business", "Communication", "Technology"])

        return careers if careers else ["Varied options available"]

    def _career_challenges(self) -> List[str]:
        """Career obstacles to watch for."""
        challenges = []
        if self.planets.get("Saturn", {}).get("dignity") == "debilitated":
            challenges.append("Career delays - requires persistence")
        if self.planets.get("Mars", {}).get("dignity") == "debilitated":
            challenges.append("Energy management - avoid overcommitment")

        return challenges if challenges else []

    def _marriage_timing(self) -> str:
        """Typical age of marriage."""
        venus = self.planets.get("Venus", {})
        jupiter = self.planets.get("Jupiter", {})

        if venus.get("house") in (5, 7):
            return "Age 22-28 (early)"
        elif jupiter.get("house") == 7:
            return "Age 26-35 (moderate)"
        else:
            return "Age 25-35 (variable)"

    def _partner_traits(self) -> List[str]:
        """Traits of ideal partner."""
        venus = self.planets.get("Venus", {})
        venus_sign = venus.get("sign", "Unknown")

        traits = {
            "Aries": ["Energetic", "Ambitious", "Adventurous"],
            "Taurus": ["Stable", "Loyal", "Practical"],
            "Gemini": ["Intellectual", "Communicative", "Playful"],
            "Cancer": ["Nurturing", "Emotional", "Family-oriented"],
            "Leo": ["Confident", "Creative", "Generous"],
            "Virgo": ["Practical", "Devoted", "Helpful"],
            "Libra": ["Balanced", "Artistic", "Social"],
            "Scorpio": ["Intense", "Deep", "Loyal"],
            "Sagittarius": ["Free-spirited", "Philosophical", "Adventurous"],
            "Capricorn": ["Ambitious", "Responsible", "Grounded"],
            "Aquarius": ["Independent", "Intellectual", "Unconventional"],
            "Pisces": ["Spiritual", "Intuitive", "Compassionate"],
        }

        return traits.get(venus_sign, ["Complementary qualities"])

    def _relationship_challenges(self) -> List[str]:
        """Potential relationship challenges."""
        challenges = []
        venus = self.planets.get("Venus", {})

        if venus.get("dignity") == "debilitated":
            challenges.append("Venus debilitated - work on emotional expression")
        if venus.get("aspect_houses", []):
            challenges.append("Venus aspects may create intensity")

        return challenges if challenges else ["Generally harmonious"]


def generate_advanced_predictions(chart: dict) -> Dict[str, Any]:
    """Generate all advanced predictions."""

    karma_analyzer = KarmaAnalyzer(chart)
    life_areas = DetailedLifeAreaPredictions(chart)

    return {
        "past_lives": karma_analyzer.analyze_past_lives(),
        "karma_debts": karma_analyzer.analyze_karma_debts(),
        "dharma": karma_analyzer.analyze_dharma_purpose(),
        "detailed_predictions": {
            "health": life_areas.predict_health(),
            "wealth": life_areas.predict_wealth(),
            "career": life_areas.predict_career(),
            "marriage_love": life_areas.predict_marriage_love(),
        },
        "generated_at": datetime.now().isoformat(),
    }

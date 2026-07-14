"""
Multi-Agent Reasoning: Break chart interpretation into specialized agents.
Each agent analyzes specific aspects in parallel, then synthesizes.
"""

from typing import Any


class ChartReasoningAgent:
    """Base agent for chart interpretation."""

    def __init__(self, name: str, focus: str, chart: dict):
        self.name = name
        self.focus = focus
        self.chart = chart
        self.analysis = {}

    def reason(self) -> dict:
        """Override in subclasses."""
        return {"agent": self.name, "focus": self.focus, "analysis": self.analysis}


class NatalChartAgent(ChartReasoningAgent):
    """Agent 1: Analyze natal chart fundamentals."""

    def __init__(self, chart: dict):
        super().__init__(
            "Natal Chart Analyst",
            "Birth chart foundation, lagna, moon, sun",
            chart
        )

    def reason(self) -> dict:
        lagna = self.chart["lagna"]
        moon = self.chart["moon"]
        planets = self.chart["planets"]

        self.analysis = {
            "lagna_archetype": f"{lagna['sign']} (ruled by {lagna['lord']})",
            "lagna_strength": planets.get(lagna["lord"], {}).get("dignity", "unknown"),
            "moon_emotional_nature": f"{moon['sign']} in {moon['nakshatra']} (Pada {moon['nakshatra_pada']})",
            "key_placements": [
                f"{p}: {d['sign']} H{d['house']} ({d['dignity']})"
                for p, d in list(planets.items())[:3]
            ],
            "foundational_reading": f"The native is fundamentally a {lagna['sign']} personality "
                                   f"with {moon['sign']} emotional nature.",
        }
        return super().reason()


class DashaAgent(ChartReasoningAgent):
    """Agent 2: Analyze dasha periods and timing."""

    def __init__(self, chart: dict):
        super().__init__(
            "Dasha Analyst",
            "Dasha periods, activation timeline",
            chart
        )

    def reason(self) -> dict:
        dasha = self.chart["dasha"]
        upcoming = dasha.get("upcoming_dashas", [])

        current_md = dasha.get("mahadasha", "Unknown")
        current_ad = dasha.get("antardasha", "Unknown")

        timeline_summary = f"{current_md} MD active (ends {dasha.get('mahadasha_end')}), "
        timeline_summary += f"with {current_ad} AD (ends {dasha.get('antardasha_end')}). "

        if upcoming:
            next_md = upcoming[1] if len(upcoming) > 1 else upcoming[0]
            timeline_summary += f"Next major shift: {next_md['lord']} MD ({next_md['start']})"

        self.analysis = {
            "current_mahadasha": current_md,
            "current_antardasha": current_ad,
            "timeline_summary": timeline_summary,
            "period_reading": f"Currently in {current_md} period. "
                            f"This activates {current_md}'s themes and tests. "
                            f"Transition to next dasha at {dasha.get('mahadasha_end')}.",
        }
        return super().reason()


class YogaAgent(ChartReasoningAgent):
    """Agent 3: Analyze yogas and success patterns."""

    def __init__(self, chart: dict):
        super().__init__(
            "Yoga Analyst",
            "Yogas, success patterns, strengths",
            chart
        )

    def reason(self) -> dict:
        yogas = self.chart.get("yogas", [])
        analysis = self.chart.get("analysis", {})
        mechanisms = analysis.get("dominant_mechanisms", [])

        yoga_summary = ""
        if yogas:
            yoga_names = [y["name"] for y in yogas]
            yoga_summary = f"Detected: {', '.join(yoga_names)}. "
            yoga_summary += f"These amplify {yogas[0]['effect']}. "
            yoga_summary += "Strong success potential when properly activated."
        else:
            yoga_summary = "No major yogas. Success comes through persistent effort."

        self.analysis = {
            "yogas_present": [y["name"] for y in yogas],
            "yoga_summary": yoga_summary,
            "strength_factors": [m["name"] for m in mechanisms[:3]],
            "yoga_reading": yoga_summary,
        }
        return super().reason()


class ContradictionResolverAgent(ChartReasoningAgent):
    """Agent 4: Identify and resolve contradictions."""

    def __init__(self, chart: dict):
        super().__init__(
            "Contradiction Resolver",
            "Conflicting indicators, paradoxes",
            chart
        )

    def reason(self) -> dict:
        analysis = self.chart.get("analysis", {})
        contradictions = analysis.get("contradictions", {})

        resolution_summary = ""
        if contradictions:
            themes = list(contradictions.keys())
            resolution_summary = f"Found conflicts in: {', '.join(themes)}. "
            for theme, info in list(contradictions.items())[:1]:
                resolution_summary += f"\n  {theme.title()}: {info['resolution']}"
        else:
            resolution_summary = "Chart shows consistency across major themes."

        self.analysis = {
            "contradictions_found": list(contradictions.keys()),
            "resolution_summary": resolution_summary,
            "net_effect": "Positive factors outweigh negative ones when dasha activation is favorable.",
        }
        return super().reason()


class SynthesisAgent(ChartReasoningAgent):
    """Agent 5: Synthesize all agents into coherent interpretation."""

    def __init__(self, chart: dict, agent_reports: list):
        super().__init__(
            "Synthesis Agent",
            "Integrate all analyses into one reading",
            chart
        )
        self.agent_reports = agent_reports

    def reason(self) -> dict:
        from .chart_dna import extract_chart_dna

        dna = extract_chart_dna(self.chart)

        synthesis = {
            "archetype": dna["archetype_name"],
            "one_liner": dna["one_liner"],
            "integrated_reading": self._build_integrated_reading(dna),
            "key_takeaways": self._extract_takeaways(dna),
        }

        self.analysis = synthesis
        return super().reason()

    def _build_integrated_reading(self, dna: dict) -> str:
        """Synthesize agents into one narrative."""
        reading = f"""
        This is the chart of {dna['archetype_name']}.

        Core Theme: {dna['one_liner']}

        Life Axis: {dna['primary_life_axis']}

        The dominant planet, {dna['dominant_planet']}, channels energy toward {dna['primary_life_axis'].split('↔')[0]}.
        The current period ({self.chart['dasha'].get('mahadasha', 'Unknown')} MD) activates {dna['core_mechanism']}.

        Challenge: {dna['life_challenge']}

        Gift: {dna['life_gift']}

        Development should flow toward: {dna['developmental_direction']}

        Destiny Type: {dna['destiny_type']}
        """
        return reading.strip()

    def _extract_takeaways(self, dna: dict) -> list[str]:
        """Generate actionable takeaways."""
        takeaways = [
            f"Archetype: {dna['archetype_name']}",
            f"Primary Life Axis: {dna['primary_life_axis']}",
            f"Shadow Work: {dna['shadow_theme']}",
            f"Current Activation: {dna['core_mechanism']}",
            f"Next Step: {dna['developmental_direction'].split(';')[0]}",
        ]
        return takeaways


def run_multi_agent_analysis(chart: dict) -> dict:
    """Execute all agents and synthesize results."""
    # Run specialized agents
    natal_agent = NatalChartAgent(chart)
    dasha_agent = DashaAgent(chart)
    yoga_agent = YogaAgent(chart)
    resolver_agent = ContradictionResolverAgent(chart)

    agent_reports = [
        natal_agent.reason(),
        dasha_agent.reason(),
        yoga_agent.reason(),
        resolver_agent.reason(),
    ]

    # Run synthesis agent
    synthesis_agent = SynthesisAgent(chart, agent_reports)
    synthesis = synthesis_agent.reason()

    return {
        "agents": agent_reports,
        "synthesis": synthesis,
    }

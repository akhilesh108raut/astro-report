"""
Rule engine: evaluates rule conditions against a structured chart dict.
Returns matched rules ranked by relevance score.
"""

import json
from pathlib import Path
from typing import Any


_DB_PATH = Path(__file__).parent / "rules_db.json"
_RULES: list[dict] | None = None


def _load_rules() -> list[dict]:
    global _RULES
    if _RULES is None:
        with open(_DB_PATH, encoding="utf-8") as f:
            _RULES = json.load(f)
    return _RULES


# ── Condition evaluators ──────────────────────────────────────────────────────

def _eval_condition(cond: dict, chart: dict) -> bool:
    t = cond["type"]
    planets = chart.get("planets", {})
    house_lords = chart.get("house_lords", {})
    yogas = {y["name"] for y in chart.get("yogas", [])}
    dasha = chart.get("dasha", {})

    if t == "nakshatra":
        # A planet occupies a specific nakshatra. The Moon's nakshatra (Janma
        # Nakshatra / birth star) is the most personalising layer — matched via
        # planet="Moon". Works for any planet that carries a "nakshatra" field.
        # The top-level chart["moon"]["nakshatra"] is preferred for the Moon
        # since it's the canonical birth-star field.
        planet = cond["planet"]
        if planet == "Moon" and chart.get("moon", {}).get("nakshatra"):
            actual = chart["moon"]["nakshatra"]
        else:
            actual = (planets.get(planet) or {}).get("nakshatra")
        return actual is not None and actual == cond["nakshatra"]

    if t == "planet_in_house":
        p = planets.get(cond["planet"])
        return p is not None and p["house"] == cond["house"]

    if t == "planet_in_sign":
        p = planets.get(cond["planet"])
        return p is not None and p["sign"] == cond["sign"]

    if t == "planet_dignity":
        p = planets.get(cond["planet"])
        return p is not None and p["dignity"] == cond["dignity"]

    if t == "planet_conjunct":
        p1 = planets.get(cond["p1"])
        p2 = planets.get(cond["p2"])
        return p1 is not None and p2 is not None and p1["house"] == p2["house"]

    if t == "planet_aspected_by":
        p = planets.get(cond["planet"])
        asp = planets.get(cond["aspected_by"])
        if p is None or asp is None:
            return False
        return p["house"] in asp.get("aspects", [])

    if t == "house_lord_in_house":
        key = f"house_{cond['from_house']}_lord"
        entry = house_lords.get(key)
        return entry is not None and entry["placed_in_house"] == cond["to_house"]

    if t == "dasha_active":
        return (dasha.get("mahadasha") == cond["planet"] or
                dasha.get("antardasha") == cond["planet"])

    if t == "yoga_present":
        return cond["name"] in yogas

    return False


def _score_rule(rule: dict, chart: dict) -> float | None:
    """
    Returns a relevance score for a rule given a chart.
    Returns None if required conditions are not all met.
    """
    # All required conditions must match
    for cond in rule.get("required", []):
        if not _eval_condition(cond, chart):
            return None

    # Base score
    score = rule.get("weight", 1.0)

    # Optional conditions boost the score
    optional_matches = sum(
        1 for cond in rule.get("optional", [])
        if _eval_condition(cond, chart)
    )
    if rule.get("optional"):
        score *= (1 + 0.3 * optional_matches / len(rule["optional"]))

    return score


def query_rules(chart: dict, top_k: int = 15, tags: list[str] | None = None) -> list[dict]:
    """
    Returns up to top_k rules that match the chart, sorted by relevance.

    Args:
        chart:  structured chart dict from build_chart()
        top_k:  max number of rules to return
        tags:   optional filter — only return rules with these tags
    """
    rules = _load_rules()
    scored = []

    for rule in rules:
        if tags:
            if not any(t in rule.get("tags", []) for t in tags):
                continue
        score = _score_rule(rule, chart)
        if score is not None:
            scored.append((score, rule))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:top_k]]


def rules_to_context(matched_rules: list[dict]) -> str:
    """
    Formats matched rules into a context block for the SLM prompt.
    Groups by theme, deduplicates, and orders by score.
    """
    if not matched_rules:
        return "No specific classical rules matched.\n"

    lines = ["=== CLASSICAL RULES APPLICABLE TO THIS CHART ===\n"]
    for i, rule in enumerate(matched_rules, 1):
        effects_str = ", ".join(
            f"{k}:{v:.0%}" for k, v in sorted(
                rule["effects"].items(), key=lambda x: -x[1]
            )[:3]
        )
        lines.append(
            f"[{i}] {rule['source']}\n"
            f"    Rule: {rule['interpretation']}\n"
            f"    Key effects: {effects_str}\n"
        )

    return "\n".join(lines)


def augment_prompt(base_prompt: str, chart: dict, top_k: int = 12) -> str:
    """
    Inserts matched classical rules into the SLM reasoning prompt.
    Call this instead of chart_to_reasoning_prompt() when using RAG.
    """
    matched = query_rules(chart, top_k=top_k)
    context = rules_to_context(matched)

    # Insert context block before the REASONING TASK section
    if "=== REASONING TASK ===" in base_prompt:
        return base_prompt.replace(
            "=== REASONING TASK ===",
            context + "\n=== REASONING TASK ==="
        )
    return base_prompt + "\n\n" + context

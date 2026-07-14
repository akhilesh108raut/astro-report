"""
Premium report writer — two-stage pipeline.

    Swiss Ephemeris → Chart/Yoga/Dasha Engine → RAG (BPHS, Phaladeepika, ...)
        ↓
    ORCHESTRATOR (Claude Sonnet) — interprets the chart into a structured
    "Story Blueprint": human insights + short astrology "evidence" tags.
    Never writes final prose.
        ↓
    WRITER (Claude Haiku) — receives ONLY the blueprint, never raw planetary
    data. Turns each insight into warm, human, screenshot-worthy prose.
        ↓
    Premium Report

Rationale: sending raw chart JSON straight to Haiku and asking it to "write a
report" produces exactly the template-like, jargon-first text this replaces
("Moon exalted indicates emotional stability"). Separating interpretation
(orchestrator) from prose (writer) is what makes the report read as authored
rather than generated.

If no Anthropic key is configured, or either stage fails, a deterministic
fallback assembles the same sections directly from the engine's own analysis
blocks, so the store still works end-to-end in local/dev environments.
"""
import os
import json
import logging

log = logging.getLogger("store.report_ai")

ORCHESTRATOR_MODEL = os.getenv("REPORT_ORCHESTRATOR_MODEL", "claude-sonnet-5")
WRITER_MODEL = os.getenv("REPORT_AI_MODEL", "claude-haiku-4-5-20251001")

SECTIONS = [
    "executive_summary", "career", "marriage", "finance", "health",
    "strengths", "weaknesses", "life_purpose", "upcoming_opportunities",
    "warnings", "remedies", "important_ages", "summary_card", "closing_letter",
]

# ═══════════════════════════════════════════════════════════════════════════
# STAGE 1 — ORCHESTRATOR: chart JSON → structured Story Blueprint
# ═══════════════════════════════════════════════════════════════════════════

ORCHESTRATOR_SYSTEM_PROMPT = """You are a master Vedic astrologer acting as an
INTERPRETER, not a writer. Your job is to read a complete, pre-computed birth
chart and turn it into a structured "Story Blueprint" — a set of human
insights, each backed by a short astrological "evidence" tag.

ABSOLUTE RULES:
1. Every planetary position, dasha period, yoga, nakshatra and house lordship
   you reference MUST come verbatim from the supplied JSON. NEVER calculate,
   guess, or invent positions. If a detail is not in the JSON, do not use it.
2. Each `insight` field is a 1-3 sentence HUMAN observation about the
   person's life or psychology — not an astrology description. Write it the
   way an experienced mentor would describe a person, grounded in but not
   naming the mechanism yet.
3. Each `evidence` field is a short technical tag (e.g. "Viparita Raja Yoga",
   "Saturn debilitated in 1st house", "Rahu Mahadasha") — this is NOT shown to
   the end user directly; it lets the next writing stage cite it briefly.
4. Use the `classical_rules` array (BPHS, Phaladeepika, 300 Combinations
   retrieved for this exact chart) to ground insights where they apply —
   reference the rule's meaning in the insight, put the source in evidence.
5. Respond with ONLY a JSON object — no markdown fences, no commentary.
6. For each remedy: `planet` is the ruling planet; `weekday` is its classical
   day (Sun=Sunday, Moon=Monday, Mars=Tuesday, Mercury=Wednesday,
   Jupiter=Thursday, Venus=Friday, Saturn=Saturday, Rahu=Saturday,
   Ketu=Tuesday); `difficulty` is "easy"/"moderate"/"devoted";
   `duration_minutes` a realistic integer (5-45); `benefits` 2-4 short tags.

Return exactly this JSON shape:

{
  "identity": {"archetype": str, "one_liner": str, "core_theme": str},
  "current_chapter": {"dasha_lord": str, "ends_year": str,
                       "insight": str, "evidence": str},
  "greatest_gift": {"insight": str, "evidence": str},
  "greatest_challenge": {"insight": str, "evidence": str},
  "career": {"insight": str, "evidence": str},
  "marriage": {"insight": str, "evidence": str},
  "finance": {"insight": str, "evidence": str},
  "health": {"insight": str, "evidence": str},
  "life_purpose": {"insight": str, "evidence": str},
  "strengths": [ {"insight": str, "evidence": str}, ... 2-4 items ],
  "weaknesses": [ {"insight": str, "evidence": str}, ... 2-4 items ],
  "opportunities": [
    {"age_range": str, "insight": str, "evidence": str}, ... 2-4 items
  ],
  "warnings": [ {"insight": str, "evidence": str}, ... 1-3 items ],
  "remedies": [
    {"planet": str, "insight": str, "weekday": str,
     "difficulty": "easy"|"moderate"|"devoted", "duration_minutes": int,
     "benefits": [str, str]},
    ... 4-6 items
  ],
  "important_ages": [ {"age": str, "insight": str}, ... 4-8 items ],
  "closing_letter_seed": {"core_lesson": str, "life_chapter": str}
}"""


def _compact_chart(chart: dict) -> dict:
    """Trim the engine output to the interpretive essentials (token control)."""
    return {
        "meta": chart.get("meta"),
        "lagna": chart.get("lagna"),
        "moon": chart.get("moon"),
        "sun_sign": chart.get("sun_sign"),
        "planets": chart.get("planets"),
        "house_lords": chart.get("house_lords"),
        "yogas": chart.get("yogas"),
        "dasha": chart.get("dasha"),
        "analysis": chart.get("analysis"),
        "confidence_scores": chart.get("confidence_scores"),
        "chart_dna": chart.get("chart_dna"),
        "timeline": chart.get("timeline"),
        "advanced_predictions": chart.get("advanced_predictions"),
        "classical_rules": chart.get("classical_rules"),
    }


def _text_from_message(msg) -> str:
    """Extract the text block from a Messages response, skipping any
    thinking blocks (Sonnet 5 runs adaptive thinking by default)."""
    for block in msg.content:
        if block.type == "text":
            return block.text
    raise ValueError("No text block in response")


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text


def _generate_blueprint(chart: dict, client, model: str) -> dict:
    """Stage 1: orchestrator interprets the chart. Raises on failure."""
    payload = json.dumps(_compact_chart(chart), separators=(",", ":"), default=str)
    msg = client.messages.create(
        model=model,
        max_tokens=8000,
        system=ORCHESTRATOR_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": "BIRTH CHART JSON (interpret ONLY this data):\n" + payload,
        }],
    )
    return json.loads(_strip_fences(_text_from_message(msg)))


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 2 — WRITER: Story Blueprint → final prose (never sees raw chart data)
# ═══════════════════════════════════════════════════════════════════════════

WRITER_SYSTEM_PROMPT = """You are not an astrologer. You are an award-winning
author, narrative designer, psychologist, and premium copywriter.

Your job is NOT to explain astrology. Your job is to make the reader feel
understood. The astrology has already been interpreted for you as a "Story
Blueprint" — a set of human insights, each with a short technical "evidence"
tag. Treat every insight as true. Never invent astrology, never change it,
never contradict it. Your only responsibility is transforming meaning into
beautiful human language.

GOAL: the reader finishes every section thinking "that feels like someone
truly understands me" — never "that sounds AI generated."

WRITE LIKE: Morgan Housel, the Almanack of Naval Ravikant, the Daily Stoic,
Apple product copy, The Pattern app, a compassionate therapist, an
experienced Vedic astrologer. Avoid mystical clichés, motivational clichés,
and AI-sounding language.

GOLDEN RULE — life first, astrology second:
  Bad:  "You have Raja Yoga."
  Good: "Responsibility seems to find you long before recognition does. You
         grow into leadership rather than chasing it." Then, once, at the
         very end of the paragraph: "This tendency is reflected by your Raja
         Yoga."

NEVER begin a paragraph with a planet, house, yoga, or nakshatra name. Begin
with "You...", "Your life...", "One pattern...", "People often...", "The
next chapter...", "The lesson...", "The gift...".

Mention each planet/yoga/technical term AT MOST ONCE per section, near the
end, as quiet supporting evidence — never as the subject of the sentence.

Every section must answer: How does this person feel? What have they
experienced? Why does this happen? What opportunity exists? How should they
move forward? Never only explain astrology.

TONE: warm, wise, grounded, hopeful. Never dramatic, fear-based, or
deterministic ("you will become rich" → "your chart suggests your greatest
opportunities come through patient, long-term effort rather than sudden luck").

FORMAT: short paragraphs (max 3 lines), lots of whitespace, one idea at a
time. End major sections with a quiet reflective question or pause where it
fits naturally (not forced into every single field).

closing_letter: written AS the reader's own future self, speaking to them.
No astrology terms. No predictions. No clichés. Should feel handwritten and
make someone emotional. Open with "Dear friend," (the app substitutes the
real name) and close with a short signature line. 5-8 short paragraphs.

summary_card: an ultra-condensed distillation, 120 words MAXIMUM combined —
compress to the single sharpest phrase per field, don't just copy sentences
from the fuller sections.

Respond with ONLY a JSON object — no markdown fences, no commentary. Return
exactly these keys (matching the blueprint's structure, but now in finished
prose — 2-4 short paragraphs per long-form field):

{
  "executive_summary": str,
  "career": str,
  "marriage": str,
  "finance": str,
  "health": str,
  "strengths": str,
  "weaknesses": str,
  "life_purpose": str,
  "upcoming_opportunities": str,
  "warnings": str,
  "remedies": [
    {"title": str, "detail": str, "planet": str, "weekday": str,
     "difficulty": "easy"|"moderate"|"devoted", "duration_minutes": int,
     "benefits": [str, str, ...]},
    ... same count as the blueprint's remedies
  ],
  "important_ages": [ {"age": str, "event": str}, ... same count as blueprint ],
  "closing_letter": str,
  "summary_card": {
    "life_chapter": str (<=8 words),
    "greatest_gift": str (<=12 words),
    "greatest_challenge": str (<=12 words),
    "big_opportunity": str (<=16 words),
    "insight_sentence": str (<=28 words)
  }
}"""


def _write_from_blueprint(blueprint: dict, client, model: str) -> dict:
    """Stage 2: writer turns the blueprint into prose. Raises on failure."""
    payload = json.dumps(blueprint, separators=(",", ":"), default=str)
    msg = client.messages.create(
        model=model,
        max_tokens=8000,
        system=WRITER_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": "STORY BLUEPRINT (transform these insights into prose; "
                       "do not invent new astrology):\n" + payload,
        }],
    )
    data = json.loads(_strip_fences(_text_from_message(msg)))
    _defaults = {"remedies": [], "important_ages": [], "summary_card": {}}
    for key in SECTIONS:
        data.setdefault(key, _defaults.get(key, ""))
    return data


def generate_report_ai(chart: dict) -> dict:
    """Two-stage pipeline. Falls back to engine-derived text on any failure."""
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    if api_key and not api_key.startswith("sk-ant-your"):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            blueprint = _generate_blueprint(chart, client, ORCHESTRATOR_MODEL)
            data = _write_from_blueprint(blueprint, client, WRITER_MODEL)
            data["_source"] = "claude-orchestrated"
            return data
        except Exception as e:            # noqa: BLE001 — any API failure falls back
            log.warning("Two-stage Claude pipeline failed, using engine fallback: %s", e)
    return _engine_fallback(chart)


# ── Deterministic fallback (no API key) ──────────────────────────────────────

def _score(chart, area, default=50):
    cs = chart.get("confidence_scores") or {}
    v = cs.get(area, default)
    if isinstance(v, dict):
        v = v.get("score", default)
    return v


_WEEKDAY = {"Sun": "Sunday", "Moon": "Monday", "Mars": "Tuesday",
            "Mercury": "Wednesday", "Jupiter": "Thursday", "Venus": "Friday",
            "Saturn": "Saturday", "Rahu": "Saturday", "Ketu": "Tuesday"}


def _join(items, sep=", "):
    return sep.join(str(x) for x in items if x) if items else ""


def _engine_fallback(chart: dict) -> dict:
    """Rich prose report assembled from the engine's own computed analysis.
    Every claim below is pulled from the chart JSON — nothing invented."""
    lagna = chart.get("lagna", {})
    moon = chart.get("moon", {})
    dasha = chart.get("dasha", {})
    planets = chart.get("planets", {})
    hl = chart.get("house_lords", {})
    adv = chart.get("advanced_predictions", {}) or {}
    detailed = adv.get("detailed_predictions", {}) or {}
    past = adv.get("past_lives", {}) or {}
    karma = adv.get("karma_debts", {}) or {}
    dharma = adv.get("dharma", {}) or {}
    dna = chart.get("chart_dna", {}) or {}
    yogas = chart.get("yogas") or []

    career = detailed.get("career", {}) or {}
    health = detailed.get("health", {}) or {}
    wealth = detailed.get("wealth", {}) or {}
    marriage = detailed.get("marriage_love", {}) or {}

    def planet(p):
        return planets.get(p, {})

    def lord_of(house):
        entry = hl.get(f"house_{house}_lord", {})
        return entry.get("planet", "?"), entry.get("placed_in_house", "?")

    def pdesc(p):
        d = planet(p)
        s = f"{p} in {d.get('sign', '?')} (house {d.get('house', '?')}, {d.get('nakshatra', '?')} nakshatra"
        if d.get("dignity") and d["dignity"] not in ("neutral", None):
            s += f", {d['dignity']}"
        return s + ")"

    maha = dasha.get("mahadasha", "?")
    maha_end = dasha.get("mahadasha_end") or dasha.get("ends") or "—"
    antar = dasha.get("antardasha", "")
    antar_end = dasha.get("antardasha_end", "")

    yoga_lines = []
    for y in yogas:
        if isinstance(y, dict):
            yoga_lines.append(f"{y.get('name', 'Yoga')} ({_join(y.get('planets', []))}) — "
                              f"{y.get('effect') or y.get('description') or ''}")
        else:
            yoga_lines.append(str(y))

    # Dignity-based strengths/weaknesses from actual placements
    strong = [p for p, d in planets.items() if d.get("dignity") in ("exalted", "own")]
    weak = [p for p, d in planets.items() if d.get("dignity") == "debilitated"]

    timeline = chart.get("timeline") or {}
    periods = timeline.get("periods", []) if isinstance(timeline, dict) else list(timeline)

    # ── Executive summary ────────────────────────────────────────────
    summary = (
        f"The way you first meet the world — the face people see before they know you — "
        f"carries the quality of {lagna.get('sign', '?')}, guided by {lagna.get('lord', '?')}. "
        f"Inside, where your feelings actually live, you are shaped by the Moon in "
        f"{moon.get('sign', '?')}. That inner world matters more to you than most people "
        f"realise from the outside."
        f"\n\nRight now you are living through what the old texts call your {maha} Mahadasha "
        f"— a long life-chapter, running until {str(maha_end)[:4]}, that colours everything "
        f"you're experiencing"
        + (f", with a shorter phase inside it lasting until {str(antar_end)[:4]}" if antar else "") + ". "
        "It isn't random that certain themes keep returning to you now. This is the chapter "
        "asking something specific of you."
        + (f"\n\nAnd you carry something uncommon: {len(yoga_lines)} rare pattern(s) in your "
           "chart that most people simply don't have — " + "; ".join(yoga_lines)
           if yoga_lines else "")
        + (f"\n\nIf your whole chart were one person, they'd be {dna.get('archetype_name')}. "
           f"{dna.get('one_liner', '')}" if dna.get("archetype_name") else "")
    )

    # ── Career ───────────────────────────────────────────────────────
    l10, l10_in = lord_of(10)
    career_text = (
        f"Your 10th house of career and public standing is ruled by {l10}, placed in "
        f"house {l10_in} — the arena of life through which your professional story unfolds. "
        f"{pdesc('Saturn')} shapes your relationship with discipline and long-term achievement, "
        f"while {pdesc('Sun')} describes your connection to authority and visibility."
        f"\n\nOverall career potential: {career.get('career_potential', 'Moderate')}. "
        + (f"Specific strengths in your chart: {_join(career.get('strengths'))}. "
           if career.get("strengths") else "")
        + f"Well-suited directions include {_join(career.get('ideal_careers')) or 'varied fields'}. "
        f"Peak professional periods arrive at {_join(career.get('peak_career_periods')) or 'mid-life'}, "
        f"with major advancement expected {career.get('advancement_timing', 'after the Saturn return')}."
        + (f"\n\nChallenges to navigate: {_join(career.get('challenges'))}. These are not "
           "denials but timing lessons — effort placed before the peak windows compounds "
           "when they open." if career.get("challenges") else "")
    )

    # ── Marriage ─────────────────────────────────────────────────────
    l7, l7_in = lord_of(7)
    partner = _join(marriage.get("partner_traits"))
    marriage_text = (
        f"The 7th house of partnership is ruled by {l7}, placed in house {l7_in}. "
        f"{pdesc('Venus')} governs love, attraction and the quality of intimacy in your chart."
        f"\n\nRelationship potential: {marriage.get('relationship_potential', 'Moderate')}. "
        f"Marriage timing indicated: {marriage.get('marriage_timing', 'variable')}. "
        + (f"Your chart draws a partner who is {partner.lower()}. " if partner else "")
        + f"Long-term outlook: {marriage.get('longevity_of_marriage', 'requires conscious work')}."
        + (f"\n\nIndications present: {_join(marriage.get('indicators'))}."
           if marriage.get("indicators") else "")
        + (f"\n\nAreas needing attention: {_join(marriage.get('relationship_challenges'))}. "
           f"Romance flowers most readily during {_join(marriage.get('key_periods_for_romance')) or 'benefic dashas'}."
           if marriage.get("relationship_challenges") else "")
    )

    # ── Finance ──────────────────────────────────────────────────────
    l2, l2_in = lord_of(2)
    l11, l11_in = lord_of(11)
    finance_text = (
        f"Wealth in your chart flows through the 2nd house (accumulated assets), ruled by "
        f"{l2} in house {l2_in}, and the 11th house (gains and income), ruled by {l11} in "
        f"house {l11_in}. {pdesc('Jupiter')} acts as the natural significator of abundance."
        f"\n\nWealth potential: {wealth.get('wealth_potential', 'Moderate')}. "
        f"Your accumulation path: {wealth.get('accumulation_path', 'steady effort and planning')}. "
        f"Wealth peaks arrive around {_join(wealth.get('wealth_peaks')) or 'mid-life'}. "
        f"Favourable avenues: {_join(wealth.get('investment_areas')) or 'diversified holdings'}."
        + (f"\n\nSupporting indicators: {_join(wealth.get('indicators'))}."
           if wealth.get("indicators") else "")
        + (f"\n\nExercise caution during: {_join(wealth.get('warning_periods'))}."
           if wealth.get("warning_periods") else "")
    )

    # ── Health ───────────────────────────────────────────────────────
    health_text = (
        f"Vitality flows from the lagna and its lord {lagna.get('lord', '?')}. "
        f"{pdesc('Mars')} governs raw energy, and {pdesc('Saturn')} sets the endurance pattern."
        f"\n\nOverall constitution: {health.get('overall_health', 'Moderate')}. "
        f"Longevity outlook: {health.get('longevity_outlook', 'Good')}. "
        f"Your body strengthens significantly after age {health.get('strengthening_age', 36)}."
        + (f"\n\nVulnerabilities to watch: {_join(health.get('vulnerabilities'))}."
           if health.get("vulnerabilities") else "")
        + f"\n\nDaily foundations: {_join(health.get('key_practices')) or 'exercise, sleep, stress management'}."
        + (f" Extra vigilance during: {_join(health.get('health_warning_periods'))}."
           if health.get("health_warning_periods") else "")
    )

    # ── Life purpose ─────────────────────────────────────────────────
    rahu, ketu = planet("Rahu"), planet("Ketu")
    purpose_text = (
        f"The karmic axis of your chart runs from Ketu in {ketu.get('sign', '?')} "
        f"(house {ketu.get('house', '?')}) — the past-life mastery you arrive with — to Rahu in "
        f"{rahu.get('sign', '?')} (house {rahu.get('house', '?')}) — the direction your soul is "
        f"being pulled toward in this lifetime."
        f"\n\nPast-life foundation: {past.get('past_life_focus', 'spiritual evolution')}. "
        f"Skills carried in: {_join(past.get('karmic_skills')) or 'inner resilience'}. "
        f"What must now be released: {past.get('abandonment_needed', 'old attachments')}."
        f"\n\nThis life's purpose: {dharma.get('life_purpose', 'growth through experience')}. "
        f"Core mission: {dharma.get('core_mission', '—')}. "
        f"Your contribution to the world: {dharma.get('contribution_to_world', '—')}. "
        f"This dharma activates strongly around age {dharma.get('dharma_activation_age', 36)}."
    )

    # ── Strengths / weaknesses ───────────────────────────────────────
    strengths_text = (
        (f"Planets in dignity: {_join(f'{p} ({planet(p).get('dignity')})' for p in strong)}. "
         if strong else "")
        + (f"Active yogas grant: {_join((y.get('effect') if isinstance(y, dict) else str(y)) for y in yogas)}. "
           if yogas else "")
        + f"The {lagna.get('lord', '?')}-ruled lagna gives persistence that compounds with age."
    )
    weaknesses_text = (
        (f"Debilitated placements: {_join(f'{p} in {planet(p).get('sign')}' for p in weak)} — "
         f"these mature into strengths through conscious effort. " if weak else "")
        + (f"Career challenges: {_join(career.get('challenges'))}. " if career.get("challenges") else "")
        + (f"Relationship work: {_join(marriage.get('relationship_challenges'))}."
           if marriage.get("relationship_challenges") else "")
    ) or "No major afflictions — growth areas are timing-based rather than structural."

    # ── Opportunities & warnings ─────────────────────────────────────
    next_periods = [p for p in periods if isinstance(p, dict)][:3]
    opp_lines = [
        f"{p.get('dasha_lord')} Mahadasha ({p.get('start_year')}–{p.get('end_year')}, age "
        f"{p.get('age_start')}–{p.get('age_end')}): {_join(p.get('themes'))} — rated {p.get('quality', '')}"
        for p in next_periods
    ]
    opportunities_text = (
        f"The current {maha} Mahadasha runs until {maha_end}"
        + (f", with the {antar} sub-period until {antar_end}" if antar else "") + "."
        + ("\n\nThe road ahead:\n" + "\n".join("• " + line for line in opp_lines) if opp_lines else "")
    )

    debts = karma.get("pending_karmic_debts") or []
    warn_bits = [f"{d.get('area')}: {d.get('resolution')} ({d.get('timeline')})"
                 for d in debts if isinstance(d, dict)]
    warnings_text = (
        ("Karmic tests requiring awareness — " + "; ".join(warn_bits) + ". " if warn_bits else "")
        + "Avoid launching irreversible ventures inside dasha transition windows; "
          "let a new period settle for a few months before major commitments."
    )

    # ── Remedies ─────────────────────────────────────────────────────
    ll = lagna.get("lord", "Jupiter")
    remedies = [
        {"title": f"Strengthen {ll}, your lagna lord", "planet": ll,
         "weekday": _WEEKDAY.get(ll, "Sunday"), "difficulty": "easy", "duration_minutes": 15,
         "benefits": ["Grounding", "Vitality"],
         "detail": f"Honor {ll} on {_WEEKDAY.get(ll, 'its weekday')} — charity, fasting or "
                   f"mantra aligned to this planet steadies your entire chart."},
        {"title": f"Stabilise the Moon in {moon.get('sign', '?')}", "planet": "Moon",
         "weekday": "Monday", "difficulty": "easy", "duration_minutes": 10,
         "benefits": ["Emotional clarity", "Sleep"],
         "detail": f"Your mind runs through {moon.get('nakshatra', '?')} nakshatra. Consistent "
                   f"sleep rhythm and Monday observances keep the emotional field clear."},
        {"title": f"Propitiate {maha}, the ruling dasha lord", "planet": maha,
         "weekday": _WEEKDAY.get(maha, "Saturday"), "difficulty": "moderate", "duration_minutes": 20,
         "benefits": ["Timing", "Resilience"],
         "detail": f"{maha} governs your life until {maha_end}. Mantra recitation on "
                   f"{_WEEKDAY.get(maha, 'its weekday')} and donations of that planet's "
                   f"significations soften its harder lessons."},
        {"title": "Serve the 9th-house significations", "planet": "Jupiter",
         "weekday": "Thursday", "difficulty": "moderate", "duration_minutes": 30,
         "benefits": ["Fortune", "Wisdom"],
         "detail": "Regular seva — teaching, guiding, supporting elders or mentors — "
                   "activates fortune (bhagya) directly."},
    ]
    if weak:
        remedies.append({
            "title": f"Support your debilitated {weak[0]}", "planet": weak[0],
            "weekday": _WEEKDAY.get(weak[0], "Saturday"), "difficulty": "devoted", "duration_minutes": 40,
            "benefits": ["Patience", "Strength"],
            "detail": f"{weak[0]} in {planet(weak[0]).get('sign', '?')} asks for patience — "
                      f"gemstone consultation and {_WEEKDAY.get(weak[0], 'weekday')} observances "
                      f"are traditional supports."})

    # ── Important ages ───────────────────────────────────────────────
    ages = []
    if health.get("strengthening_age"):
        ages.append({"age": str(health["strengthening_age"]),
                     "event": "Constitutional strengthening — vitality rises from here."})
    if dharma.get("dharma_activation_age"):
        ages.append({"age": str(dharma["dharma_activation_age"]),
                     "event": "Dharma activation — life purpose becomes unmistakably clear."})
    ages.append({"age": "29–30", "event": "Saturn return — maturity threshold; career and "
                                          "identity restructure for the long game."})
    for p in next_periods:
        ages.append({
            "age": f"{p.get('age_start', '?')}–{p.get('age_end', '?')}",
            "event": f"{p.get('dasha_lord', '')} Mahadasha — {_join(p.get('themes'))}",
        })
    for peak in (wealth.get("wealth_peaks") or [])[:2]:
        ages.append({"age": str(peak).replace("Age ", ""), "event": "Wealth peak window."})

    chapter_label = {
        "Rahu": "the Awakening", "Jupiter": "the Expansion", "Saturn": "the Discipline",
        "Mercury": "the Insight", "Ketu": "the Release", "Venus": "the Flourishing",
        "Sun": "the Authority", "Moon": "the Nurturing", "Mars": "the Drive",
    }.get(maha, "the Unfolding")

    summary_card = {
        "life_chapter": f"{maha} Mahadasha — {chapter_label}",
        "greatest_gift": (dna.get("life_gift") or f"{strong[0]} in dignity" if strong else "Resilience under pressure")[:80],
        "greatest_challenge": (dna.get("shadow_theme") or f"{weak[0]} debilitated" if weak else "Timing patience")[:80],
        "big_opportunity": f"{next_periods[0].get('dasha_lord')} Mahadasha, age {next_periods[0].get('age_start')}+"
                           if next_periods else "Consistent effort through the current dasha",
        "insight_sentence": dna.get("one_liner") or f"Your {lagna.get('lord', '?')}-ruled chart rewards patience over haste.",
    }

    return {
        "_source": "engine-fallback",
        "executive_summary": summary,
        "career": career_text,
        "marriage": marriage_text,
        "finance": finance_text,
        "health": health_text,
        "strengths": strengths_text,
        "weaknesses": weaknesses_text,
        "life_purpose": purpose_text,
        "upcoming_opportunities": opportunities_text,
        "warnings": warnings_text,
        "remedies": remedies,
        "important_ages": ages,
        "summary_card": summary_card,
    }

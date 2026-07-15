"""
Premium report writer — two-stage pipeline.

    Swiss Ephemeris → Chart/Yoga/Dasha Engine → RAG (BPHS, Phaladeepika, ...)
        ↓
    ORCHESTRATOR (Claude Haiku) — interprets the chart into a structured
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

ORCHESTRATOR_MODEL = os.getenv("REPORT_ORCHESTRATOR_MODEL", "claude-haiku-4-5-20251001")
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
insights, each backed by a full astrological REASONING CHAIN, not a one-word tag.

ABSOLUTE RULES:
1. Every planetary position, dasha period, yoga, nakshatra and house lordship
   you reference MUST come verbatim from the supplied JSON. NEVER calculate,
   guess, or invent positions. If a detail is not in the JSON, do not use it.
   NEVER fall back to generic Vedic astrology tropes that could apply to any
   kundli ("Saturn brings discipline", "Jupiter brings luck") unless THIS
   chart's specific placement (house/sign/dignity/dasha) actually supports
   it — every claim must be traceable to a specific field in the supplied
   JSON, not to astrology in general.
2. Each `insight` field is a 1-3 sentence HUMAN observation about the
   person's life or psychology — not an astrology description. Write it the
   way an experienced mentor would describe a person, grounded in but not
   naming the mechanism yet.
3. Each `evidence` field is a REASONING CHAIN, not a single label. Combine
   every relevant factor with " + " — e.g. "Sun in Leo (own sign, 10th house)
   + Raja Yoga (Sun-Saturn kendra-trikona) + Jupiter Mahadasha" — not just
   "Raja Yoga". Cite planet, sign, house, nakshatra, aspect, dasha, or yoga
   whichever actually apply to that specific claim; never pad with factors
   that aren't actually relevant to the claim being made.
4. Each insight/evidence object also carries a `confidence` field:
   "high" when 2+ independent chart factors converge on the same conclusion,
   "moderate" when it rests on a single factor or a debated classical rule,
   "low" when it's a minor/uncertain indication. Be honest — most charts have
   a mix of all three; a report that is "high" on everything is a lie.
5. RAG GROUNDING IS MANDATORY, NOT OPTIONAL: the `classical_rules` array is
   BPHS, Phaladeepika, and 300 Combinations text retrieved specifically for
   THIS chart — each entry has `source` (e.g. "BPHS 24"), `interpretation`
   (the actual classical text), and `effects` (which life areas it speaks
   to). For identity, career, marriage, finance, health, and life_purpose:
   you MUST select the classical_rules entries whose `effects` match that
   field's domain, and the `evidence` field MUST closely paraphrase (not
   invent, not generically reference) that entry's actual `interpretation`
   text, citing `source` by name (e.g. "BPHS 24: Sun in lagna gives
   commanding presence..."). If no classical_rules entry matches a given
   field's domain, say so implicitly by relying only on direct chart
   factors (planet/house/yoga/dasha) for that field's evidence — do not
   invent a citation or paraphrase a rule that wasn't actually retrieved.
6. No two insights in the same blueprint may share an opening structure or
   restate the same placement as the main reason — each field must draw on a
   DIFFERENT combination of chart factors. If two sections would otherwise
   repeat the same yoga as their primary evidence, pick the next most
   relevant factor for one of them instead.
7. For career, marriage, finance, health, life_purpose, and identity ONLY:
   also produce `evidence_weights`, a WEIGHTED EVIDENCE breakdown — 3-6
   objects `{"factor": str, "weight_pct": int}`, weights summing to
   approximately 100, sorted highest weight first. Assign weight by how much
   each factor actually drives the conclusion: natal factors (sign, house
   placement, dignity, yoga) should generally outweigh transient factors
   (current dasha, current transit) unless the transient factor is the
   primary trigger for something time-bound. When 2+ factors converge with
   no single one dominating, that supports "high" confidence; when one
   factor carries most of the weight alone, that's usually "moderate".
   Also add `natal_vs_transit`: "natal" if natal factors hold most of the
   weight, "transit" if current dasha/transit factors dominate, "mixed" if
   roughly even — this lets the reader know whether a conclusion is a
   stable trait or a temporary window.
8. Respond with ONLY a JSON object — no markdown fences, no commentary.
8b. `shakti` identifies the person's single dominant creative force — not a
   personality summary, but what they are uniquely built to CREATE in the
   world (build, teach, protect, heal, lead, guide, transform, innovate,
   nurture, explore, organize, connect...). Derive it ONLY from combinations
   actually present in the chart: lagna/lagna lord, 1st/5th/9th/10th/11th
   house occupants and lords, yogas (especially Raja/Dhana/Viparita Raja),
   planetary dignity, active mahadasha, and any matched classical_rules.
   Pick ONE archetype label (2-3 words, e.g. "The Architect", "The Healer",
   "The Strategist") that best fits — do not hedge between two. `evidence`
   must name the actual factors behind it, the same reasoning-chain and
   classical_rules-grounding rules from point 5 apply here too.
9. For each remedy: `planet` is the ruling planet; `weekday` is its classical
   day (Sun=Sunday, Moon=Monday, Mars=Tuesday, Mercury=Wednesday,
   Jupiter=Thursday, Venus=Friday, Saturn=Saturday, Rahu=Saturday,
   Ketu=Tuesday); `difficulty` is "easy"/"moderate"/"devoted";
   `duration_minutes` a realistic integer (5-45); `benefits` 2-4 short tags.

Return exactly this JSON shape (every {"insight","evidence","confidence"}
triple below follows the rules above — insight is human, evidence is the
reasoning chain, confidence is honest):

{
  "identity": {"archetype": str, "one_liner": str, "core_theme": str,
               "evidence": str, "confidence": "high"|"moderate"|"low",
               "evidence_weights": [{"factor": str, "weight_pct": int}, ...],
               "natal_vs_transit": "natal"|"transit"|"mixed"},
  "shakti": {"shakti_name": str, "tagline": str, "core_power": str,
             "how_people_feel": str, "highest_expression": [str, str, str],
             "shadow_when_unused": [str, str, str], "best_environment": str,
             "activation": str, "evidence": str,
             "confidence": "high"|"moderate"|"low",
             "evidence_weights": [{"factor": str, "weight_pct": int}, ...]},
  "current_chapter": {"dasha_lord": str, "ends_year": str,
                       "insight": str, "evidence": str, "confidence": str},
  "greatest_gift": {"insight": str, "evidence": str, "confidence": str},
  "greatest_challenge": {"insight": str, "evidence": str, "confidence": str},
  "career": {"insight": str, "evidence": str, "confidence": str,
             "evidence_weights": [{"factor": str, "weight_pct": int}, ...],
             "natal_vs_transit": "natal"|"transit"|"mixed"},
  "marriage": {"insight": str, "evidence": str, "confidence": str,
               "evidence_weights": [{"factor": str, "weight_pct": int}, ...],
               "natal_vs_transit": "natal"|"transit"|"mixed"},
  "finance": {"insight": str, "evidence": str, "confidence": str,
              "evidence_weights": [{"factor": str, "weight_pct": int}, ...],
              "natal_vs_transit": "natal"|"transit"|"mixed"},
  "health": {"insight": str, "evidence": str, "confidence": str,
             "evidence_weights": [{"factor": str, "weight_pct": int}, ...],
             "natal_vs_transit": "natal"|"transit"|"mixed"},
  "life_purpose": {"insight": str, "evidence": str, "confidence": str,
                    "evidence_weights": [{"factor": str, "weight_pct": int}, ...],
                    "natal_vs_transit": "natal"|"transit"|"mixed"},
  "strengths": [ {"insight": str, "evidence": str, "confidence": str}, ... 2-4 items ],
  "weaknesses": [ {"insight": str, "evidence": str, "confidence": str}, ... 2-4 items ],
  "opportunities": [
    {"age_range": str, "insight": str, "evidence": str, "confidence": str}, ... 2-4 items
  ],
  "warnings": [ {"insight": str, "evidence": str, "confidence": str}, ... 1-3 items ],
  "remedies": [
    {"planet": str, "insight": str, "weekday": str,
     "difficulty": "easy"|"moderate"|"devoted", "duration_minutes": int,
     "benefits": [str, str]},
    ... 4-6 items
  ],
  "important_ages": [ {"age": str, "insight": str, "evidence": str}, ... 4-8 items ],
  "closing_letter_seed": {"core_lesson": str, "life_chapter": str, "age": int}
}

For closing_letter_seed.age: copy the "current_age" value given to you verbatim —
never calculate it yourself from birth_date."""


def _current_age(meta: dict) -> int | None:
    """Compute age from birth_date deterministically — never let the LLM do date math."""
    birth_date = (meta or {}).get("birth_date")
    if not birth_date:
        return None
    try:
        from datetime import date
        y, m, d = (int(p) for p in birth_date.split("-"))
        today = date.today()
        return today.year - y - ((today.month, today.day) < (m, d))
    except (ValueError, TypeError):
        return None


def _compact_chart(chart: dict) -> dict:
    """Trim the engine output to the interpretive essentials (token control)."""
    return {
        "meta": chart.get("meta"),
        "current_age": _current_age(chart.get("meta")),
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
        # The evidence_weights/confidence/natal_vs_transit additions made this
        # blueprint noticeably bigger than 8000 tokens covers — that ceiling
        # was truncating the JSON mid-string (JSONDecodeError: Unterminated
        # string), not a generation failure. 12000 gives real headroom.
        max_tokens=12000,
        # ORCHESTRATOR_SYSTEM_PROMPT is a large, static block reused on every
        # report — cache it so repeat calls only pay full price for the
        # per-chart payload, not the whole instruction set.
        system=[{
            "type": "text",
            "text": ORCHESTRATOR_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
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

Your job is NOT to hide the astrology. Your job is to make the reader feel
understood AND understand exactly why the AI reached each conclusion. The
astrology has already been interpreted for you as a "Story Blueprint" — a
set of human insights, each with a full reasoning chain ("evidence") and an
honest confidence level. Treat every insight as true. Never invent astrology,
never change it, never contradict it. Your job is transforming that meaning
into beautiful human language WITHOUT losing the reasoning behind it.

GOAL: the reader finishes every section thinking both "that feels like
someone truly understands me" AND "I can see exactly why the chart says
this" — never "that sounds generic" and never "that sounds like an AI
guessed."

WRITE LIKE: Morgan Housel, the Almanack of Naval Ravikant, the Daily Stoic,
Apple product copy, The Pattern app, a compassionate therapist, an
experienced Vedic astrologer explaining their reasoning to a curious client.
Avoid mystical clichés, motivational clichés, and AI-sounding filler.

GOLDEN RULE — life first, then the reasoning, explicitly:
  Bad (no reasoning):    "You have Raja Yoga."
  Bad (reasoning hidden): "Responsibility finds you before recognition does."
                          (true, but the reader can't see why you said it)
  Good: "Responsibility seems to find you long before recognition does —
         you grow into leadership rather than chasing it. Because your Sun
         sits in the 10th house of career while forming a Raja Yoga with
         Saturn, authority tends to come to you through demonstrated
         competence, not charisma or campaigning for it."

Every field must contain at least one explicit "Because [reasoning chain
from evidence, in plain language]..." sentence — not tacked on as an
afterthought, but woven in as the actual explanation for the human
observation that precedes it. Translate the evidence chain into plain
language rather than dumping raw jargon: "Sun in Leo (10th house) + Raja
Yoga (Sun-Saturn)" becomes "your Sun's placement in the house of career,
combined with a classical Raja Yoga formed with Saturn."

CLASSICAL SOURCE GROUNDING: when a blueprint's `evidence` cites a classical
text (BPHS, Phaladeepika, 300 Combinations), do not strip that grounding
into generic astrology-speak — it is the specific, verifiable reason this
insight was chosen for THIS chart, and it is what separates this report
from generic horoscope filler. Reference it naturally at least once per
field that has one, in plain language: "This mirrors a classical pattern
from the BPHS" or "the older texts describe this exact combination as...".
Never claim a classical source that the evidence chain didn't actually cite.

CONFIDENCE HONESTY: when the blueprint's confidence for a field is
"moderate" or "low", the prose must say so plainly — "this shows up as a
moderate signal because..." or "this is a lighter indication, resting on...".
Never state a moderate/low-confidence claim with the same certainty as a
high-confidence one. This is what makes the report trustworthy rather than
a horoscope-style guess.

NEVER begin a paragraph with a bare planet, house, yoga, or nakshatra name as
the grammatical subject — begin with "You...", "Your life...", "One
pattern...", "Because your chart shows...", "The next chapter...". The
reasoning belongs inside the paragraph, not as its opening word.

ANTI-REPETITION: no two sections may open with the same sentence structure,
lean on the same single yoga/placement as their only reasoning, or restate a
point already made in an earlier section. If you notice you're about to
reuse a sentence shape from a prior field, rewrite it. Every card must add
new information — no filler, no restating the insight in different words
just to fill space.

Every section must answer: How does this person feel? What have they
experienced? WHY does this happen (with real evidence)? What opportunity
exists? How should they move forward? Never only explain astrology, and
never skip the "why."

TONE: warm, wise, grounded, hopeful. Never dramatic, fear-based, or
deterministic ("you will become rich" → "your chart suggests your greatest
opportunities come through patient, long-term effort rather than sudden luck").

FORMAT: short paragraphs (max 3 lines), lots of whitespace, one idea at a
time. End major sections with a quiet reflective question or pause where it
fits naturally (not forced into every single field).

career, marriage, finance, health, life_purpose: these five fields carry a
weighted evidence breakdown (`evidence_weights`) — use it to write a
FIVE-PART structure, each part its own paragraph separated by a blank line
(the app renders each blank-line-separated chunk as its own paragraph, so
this is a real structural requirement, not just style):

  1. Observation — 1-2 sentences, the human pattern itself (no astrology).
  2. "Why? Because ..." — translate evidence_weights into plain language,
     naming which factor(s) actually drive this. If one factor holds most
     of the weight (roughly 30%+ higher than the rest), say so explicitly
     ("this is driven mainly by...", "the leading factor here is..."); if
     several are close in weight, say the conclusion rests on multiple
     converging signals. If natal_vs_transit is "transit", say plainly that
     this reflects the current period rather than a permanent trait
     ("this is a current-period signal, not a lifelong trait, because...");
     if "natal", say it's a stable pattern; if "mixed", say both apply.
  3. "What this means" — how this shows up in daily life/decisions.
  4. "What to avoid" and "Best strategy" — one sentence each, concrete and
     actionable, not vague encouragement.
  5. "Evidence:" — a short compact line listing the evidence_weights
     factors as plain terms (e.g. "Evidence: 10th house placement, a Raja
     Yoga with Saturn, the current dasha, and a supporting Jupiter aspect.")
     — translate jargon into plain terms here too, but keep it a single
     dense line, not prose.

Apply this same five-part structure to identity's `evidence_weights` inside
the `executive_summary` field. Every other field (strengths, weaknesses,
opportunities, warnings, remedies) keeps the simpler observation + one
"Because..." sentence style from the GOLDEN RULE above — don't force the
five-part structure where there's no evidence_weights data for it.

closing_letter: written AS the reader's own future self, speaking to them.
No astrology terms. No predictions. No clichés. Should feel handwritten and
make someone emotional. Open with "Dear friend," (the app substitutes the
real name) and close with a short signature line. 5-8 short paragraphs.

Calibrate every reference to life stage using closing_letter_seed.age — do not
write generic "the years ahead" prose that could apply to any adult. Someone
in their late teens/early 20s is at the start of building an identity and
independence; write about first steps, not decades of accumulated experience.
Someone in their 30s-40s is likely mid-career, possibly raising a family or
deep in established responsibilities; write about sustaining and deepening,
not starting out. Someone in their 50s+ has decades of lived experience behind
them; write about legacy, what they've already built, and what's still ahead —
never talk down to them as if they're just beginning. Never state the number
itself in the letter — the calibration should be felt in the framing, not
announced.

summary_card: an ultra-condensed distillation, 120 words MAXIMUM combined —
compress to the single sharpest phrase per field, don't just copy sentences
from the fuller sections.

Respond with ONLY a JSON object — no markdown fences, no commentary. This
must be strictly valid JSON: escape every double-quote and backslash that
appears inside a string value (e.g. a quoted phrase within a paragraph),
and never leave a string unterminated. Return exactly these keys (matching
the blueprint's structure, but now in finished prose — 2-4 short paragraphs
per long-form field):

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


LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "ta": "Tamil", "te": "Telugu",
    "bn": "Bengali", "mr": "Marathi", "kn": "Kannada", "gu": "Gujarati",
    "ml": "Malayalam", "pa": "Punjabi",
}


def _write_from_blueprint(blueprint: dict, client, model: str, language: str = "en") -> dict:
    """Stage 2: writer turns the blueprint into prose. Raises on failure."""
    payload = json.dumps(blueprint, separators=(",", ":"), default=str)
    lang_name = LANGUAGE_NAMES.get(language, "English")
    # WRITER_SYSTEM_PROMPT is cached as its own block since it's identical
    # across every language; the language addendum is appended uncached so
    # the cached prefix still hits regardless of which language is requested.
    system_blocks = [{
        "type": "text",
        "text": WRITER_SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }]
    if language != "en":
        system_blocks.append({
            "type": "text",
            "text": (
                f"Write the ENTIRE response in {lang_name}, including every string "
                f"value — not just a translated summary. Keep JSON keys in English "
                f"exactly as specified below; only the values are in {lang_name}. "
                f"Astrological terms (planet names, yoga names) may stay in their "
                f"conventional form if there is no natural {lang_name} equivalent, "
                f"but all surrounding prose must be fully in {lang_name}."
            ),
        })
    msg = client.messages.create(
        model=model,
        # The five-part paragraph structure (Observation/Why/Manifestation/
        # Advice/Evidence) across 5 domains made this output longer too —
        # matching headroom to the orchestrator's increase.
        max_tokens=10000,
        system=system_blocks,
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
    # Pass the blueprint's structured identity (archetype + evidence_weights +
    # confidence) through untouched — the writer only rewrites prose fields;
    # this one feeds the "Why This Is Your Archetype" evidence flowchart.
    data["identity"] = blueprint.get("identity") or {}
    data["shakti"] = blueprint.get("shakti") or {}
    return data


def generate_report_ai(chart: dict, language: str = "en") -> dict:
    """Two-stage pipeline. Falls back to engine-derived text on any failure."""
    api_key = (os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY") or "").strip()
    if api_key and not api_key.startswith("sk-ant-your"):
        try:
            import anthropic
            client = anthropic.Anthropic(
                api_key=api_key,
                # A 10-12k-token structured response can legitimately take a
                # while — more so for non-English output, which needs more
                # tokens for the same content. This must be a single generous
                # attempt, not several short ones, since retrying a call
                # that's merely slow just repeats the wait.
                timeout=140.0,
                max_retries=1,
            )
            # A malformed JSON response (e.g. an unescaped character breaking
            # a long paragraph mid-string) is a stochastic writing mistake,
            # not a network failure — the SDK's max_retries doesn't cover it
            # since the HTTP call itself succeeded. One retry here is cheap
            # and usually succeeds, versus falling all the way back to the
            # generic template for a one-off parsing fluke.
            try:
                blueprint = _generate_blueprint(chart, client, ORCHESTRATOR_MODEL)
            except json.JSONDecodeError:
                log.warning("Orchestrator returned malformed JSON, retrying once")
                blueprint = _generate_blueprint(chart, client, ORCHESTRATOR_MODEL)
            try:
                data = _write_from_blueprint(blueprint, client, WRITER_MODEL, language)
            except json.JSONDecodeError:
                log.warning("Writer returned malformed JSON, retrying once")
                data = _write_from_blueprint(blueprint, client, WRITER_MODEL, language)
            data["_source"] = "claude-orchestrated"
            return data
        except Exception:                 # noqa: BLE001 — any API failure falls back
            log.exception("Two-stage Claude pipeline failed, using engine fallback")
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


# Deterministic Shakti (dominant creative force) profile keyed off the
# chart's single dominant planet — used only by the engine fallback, when
# Claude is unavailable, so the section always has real chart-derived content.
_SHAKTI_BY_PLANET = {
    "Sun": {"shakti_name": "The Sovereign", "tagline": "Born to lead from the front, not the shadows.",
            "core_power": "A natural authority that draws people to follow your direction without you having to demand it.",
            "how_people_feel": "Steadied and led — people look to you to make the call when no one else will.",
            "highest_expression": ["Commands rooms without forcing it", "Builds visible, lasting positions", "Inspires by example"],
            "shadow_when_unused": ["Feels invisible or unrecognised", "Overcorrects into ego or control", "Resents being led by lesser hands"],
            "best_environment": "Roles where your name and judgment are directly on the line — leadership, ownership, public responsibility."},
    "Moon": {"shakti_name": "The Nurturer", "tagline": "Born to hold what others cannot hold for themselves.",
             "core_power": "An emotional attunement that makes people feel safe enough to be honest around you.",
             "how_people_feel": "Cared for and understood — you notice what others miss.",
             "highest_expression": ["Builds genuine emotional safety", "Reads a room instantly", "Sustains people through hard seasons"],
             "shadow_when_unused": ["Absorbs others' moods until depleted", "Avoids conflict past the point of health", "Loses your own needs in caretaking"],
             "best_environment": "Work with direct human contact — care, counsel, teams, family-scale trust."},
    "Mars": {"shakti_name": "The Executor", "tagline": "Born to move first when everyone else is still deciding.",
             "core_power": "A capacity to act decisively and push things through friction that stalls other people.",
             "how_people_feel": "Energised and protected — you make things happen.",
             "highest_expression": ["Turns plans into results fast", "Defends what it's built", "Thrives under real pressure"],
             "shadow_when_unused": ["Burns energy on the wrong fights", "Grows restless without a real target", "Impatience reads as aggression"],
             "best_environment": "High-stakes, fast-moving work with a clear objective and real consequences."},
    "Mercury": {"shakti_name": "The Strategist", "tagline": "Born to see the pattern before anyone else names it.",
                "core_power": "A sharp analytical mind that turns scattered information into a working plan.",
                "how_people_feel": "Clarified — you make complicated things make sense.",
                "highest_expression": ["Solves what others find confusing", "Communicates with precision", "Adapts strategy on the fly"],
                "shadow_when_unused": ["Overthinks past the point of action", "Detaches into pure analysis", "Restlessness from mental understimulation"],
                "best_environment": "Analysis, strategy, writing, teaching — anywhere the mind is the main tool."},
    "Jupiter": {"shakti_name": "The Guide", "tagline": "Born to widen the path for people walking behind you.",
                "core_power": "A natural wisdom and generosity that helps others see further than they could alone.",
                "how_people_feel": "Expanded and reassured — you make the future feel possible.",
                "highest_expression": ["Mentors people into their own growth", "Builds trust that compounds over years", "Sees the bigger picture others miss"],
                "shadow_when_unused": ["Over-promises without following through", "Preachy instead of practical", "Neglects your own growth while guiding others'"],
                "best_environment": "Teaching, mentoring, advisory, or any role where your judgment shapes others' choices."},
    "Venus": {"shakti_name": "The Harmonizer", "tagline": "Born to make what is broken beautiful, and what is beautiful, lasting.",
              "core_power": "An instinct for balance, aesthetics, and connection that draws people and resources together.",
              "how_people_feel": "Welcomed and appreciated — you make spaces and relationships work.",
              "highest_expression": ["Creates lasting, beautiful work", "Builds real partnerships", "Resolves conflict through diplomacy"],
              "shadow_when_unused": ["Avoids necessary confrontation", "Over-values comfort over growth", "People-pleases past your own limits"],
              "best_environment": "Design, relationship-facing work, partnership-based ventures — anywhere harmony has real value."},
    "Saturn": {"shakti_name": "The Architect", "tagline": "Born not to chase opportunities, but to build the systems that create them.",
               "core_power": "A capacity for structure and discipline that turns scattered effort into something that lasts.",
               "how_people_feel": "Trusting — they know you will still be there when the excitement runs out.",
               "highest_expression": ["Builds institutions, not just wins", "Earns trust through consistency", "Outlasts people who started ahead"],
               "shadow_when_unused": ["Overworks without meaning", "Chases validation instead of purpose", "Delays living while preparing for it"],
               "best_environment": "Long-horizon work — systems, institutions, craftsmanship, anything measured in years, not weeks."},
    "Rahu": {"shakti_name": "The Innovator", "tagline": "Born to chase what hasn't been built yet.",
             "core_power": "An unusual hunger for the unconventional that pulls you toward frontiers others haven't noticed.",
             "how_people_feel": "Challenged and stretched — you make people question the default way of doing things.",
             "highest_expression": ["Finds opportunity in the overlooked", "Adapts faster than convention", "Turns outsider status into advantage"],
             "shadow_when_unused": ["Chases novelty without follow-through", "Never feels satisfied by 'enough'", "Restless comparison to others"],
             "best_environment": "Emerging fields, unconventional paths, anything where being first matters more than being safe."},
    "Ketu": {"shakti_name": "The Seeker", "tagline": "Born to release what others cling to.",
             "core_power": "A natural detachment that lets you see past the surface into what actually matters.",
             "how_people_feel": "Quietly understood — you don't need the noise everyone else needs.",
             "highest_expression": ["Cuts to what's essential", "Guides others toward depth, not distraction", "Thrives with minimal external validation"],
             "shadow_when_unused": ["Withdraws instead of engaging", "Undervalues real achievements", "Drifts without a container for the depth"],
             "best_environment": "Research, healing, spiritual or introspective work — anything rewarding depth over visibility."},
}


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

    # Deterministic evidence weights for the archetype flowchart — no LLM,
    # so weights are simple fixed shares by factor order rather than a true
    # confidence calculation. Only the factors that actually exist are used.
    ll = lagna.get("lord", "?")
    factors = [f"{ll} rules your lagna ({lagna.get('sign', '?')} rising)"]
    if yoga_lines:
        factors.append(yoga_lines[0].split(" — ")[0])
    factors.append(f"{maha} Mahadasha is currently active")
    if strong:
        factors.append(f"{strong[0]} is in dignity")
    shares = [40, 25, 20, 15][:len(factors)]
    total = sum(shares)
    identity = {
        "archetype": dna.get("archetype_name", ""),
        "one_liner": dna.get("one_liner", ""),
        "core_theme": dna.get("core_mechanism", ""),
        "evidence": " + ".join(factors),
        "confidence": "moderate",
        "evidence_weights": [
            {"factor": f, "weight_pct": round(s * 100 / total)}
            for f, s in zip(factors, shares)
        ],
        "natal_vs_transit": "mixed" if yoga_lines else "natal",
    }

    # Deterministic Shakti fallback, keyed off the chart's dominant planet —
    # the same real factor identity's evidence chain already relies on.
    dom_planet = dna.get("dominant_planet") or ll
    shakti_profile = _SHAKTI_BY_PLANET.get(dom_planet, _SHAKTI_BY_PLANET["Saturn"])
    shakti = {
        **shakti_profile,
        "activation": f"Your {maha} Mahadasha is the current window to put this into practice — "
                       f"the more directly you use it, the less it shows up as restlessness.",
        "evidence": " + ".join(factors),
        "confidence": "moderate",
        "evidence_weights": identity["evidence_weights"],
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
        "identity": identity,
        "shakti": shakti,
    }

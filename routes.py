"""
Astro Report Store — routes.

Blueprint-mounted at /store. Completely independent of the observatory:
its own templates, static files, models and payment flow.
"""
import json
import time
import logging
import os
import re
from datetime import datetime, timedelta

from flask import (Blueprint, render_template, request, jsonify, session,
                   current_app, abort, url_for)

from database import db
from models import Purchase, Report, PaymentEvent, PricingHistory
from pricing import get_current_price, get_price_info, PRICE_TIERS
import payments

log = logging.getLogger("store")

store_bp = Blueprint(
    "report_store", __name__,
    url_prefix="/store",
    template_folder="templates",
    static_folder="static",
    static_url_path="/store-static",
)

# ── Lightweight per-IP rate limiting (mutating endpoints) ────────────────────
_hits: dict[str, list[float]] = {}

def _rate_limited(key: str, limit: int = 12, window: int = 60) -> bool:
    now = time.time()
    bucket = _hits.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False


def _dev_mode() -> bool:
    """Simulated payments allowed only when Razorpay is absent AND debug is on."""
    return (not payments.razorpay_configured()) and current_app.debug


def _owned_uuids() -> list:
    return session.get("store_owned", [])


def _grant_ownership(report_uuid: str):
    owned = session.get("store_owned", [])
    if report_uuid not in owned:
        owned.append(report_uuid)
    session["store_owned"] = owned


# ── Chart helpers ────────────────────────────────────────────────────────────

def _overall_score(chart: dict) -> int:
    cs = chart.get("confidence_scores") or {}
    vals = []
    for v in cs.values():
        if isinstance(v, dict):
            v = v.get("score")
        if isinstance(v, (int, float)):
            vals.append(v)
    return round(sum(vals) / len(vals)) if vals else 62


def _preview_payload(chart: dict) -> dict:
    yogas = []
    for y in (chart.get("yogas") or [])[:2]:
        if isinstance(y, dict):
            yogas.append({"name": y.get("name", "Yoga"),
                          "effect": y.get("effect") or y.get("description") or ""})
        else:
            yogas.append({"name": str(y), "effect": ""})
    return {
        "lagna": chart.get("lagna", {}),
        "moon": chart.get("moon", {}),
        "sun_sign": chart.get("sun_sign", ""),
        "yogas": yogas,
        "overall_score": _overall_score(chart),
    }


def _ensure_ai(report: Report) -> dict:
    """Generate the AI sections once; afterwards always serve from DB."""
    if report.ai_json:
        return json.loads(report.ai_json)
    from services.report_ai import generate_report_ai
    ai = generate_report_ai(report.chart())
    report.ai_json = json.dumps(ai, separators=(",", ":"), default=str)
    report.generated_at = datetime.utcnow()
    db.session.commit()
    return ai


def _record_tier_change(before: int, after: int):
    p_before, p_after = get_current_price(before), get_current_price(after)
    if p_after != p_before:
        db.session.add(PricingHistory(price=p_after, total_reports_at=after))


# ── PAGES ────────────────────────────────────────────────────────────────────

@store_bp.route("/")
def landing():
    total = Purchase.total_paid()
    info = get_price_info(total)
    # Marketing stats: real sales count layered over a launch baseline
    display_reports = 128_000 + total
    return render_template("store/landing.html", price=info,
                           display_reports=display_reports)


@store_bp.route("/checkout/<purchase_uuid>")
def checkout(purchase_uuid):
    purchase = Purchase.query.filter_by(uuid=purchase_uuid).first_or_404()
    report = purchase.report
    if not report:
        abort(404)
    if purchase.status == "paid":
        # Already unlocked — send straight to the report
        _grant_ownership(report.uuid)
        return render_template("store/success.html", report_uuid=report.uuid,
                               price=purchase.price_paid)
    total = Purchase.total_paid()
    info = get_price_info(total)
    return render_template(
        "store/payment.html",
        purchase=purchase,
        preview=_preview_payload(report.chart()),
        price=info,
        dev_mode=_dev_mode(),
        razorpay_key_id=(payments.get_keys()[0] or ""),
        payment_link_url=os.getenv("RAZORPAY_PAYMENT_LINK_URL", "").strip(),
    )


@store_bp.route("/report/<report_uuid>")
def view_report(report_uuid):
    report = Report.query.filter_by(uuid=report_uuid).first_or_404()
    purchase = report.purchase

    owns = (report_uuid in _owned_uuids()) or (
        purchase.user_id and session.get("user_id") == purchase.user_id
    ) or _dev_mode()  # local dev only: no Razorpay keys + debug on
    if purchase.status != "paid" or not owns:
        return render_template("store/cancel.html",
                               title="Report locked",
                               message="This report belongs to another purchase. "
                                       "Open it from the device you paid on, or sign in "
                                       "with the account used at checkout."), 403

    chart = report.chart()
    ai = _ensure_ai(report)
    return render_template("store/report.html", chart=chart, ai=ai,
                           purchase=purchase, report=report)


_PLANET_EPITHET = {
    "Sun": "The Sovereign-Self", "Moon": "The Nurturer", "Mars": "The Warrior",
    "Mercury": "The Messenger", "Jupiter": "The Sage", "Venus": "The Artist",
    "Saturn": "The Disciplinarian", "Rahu": "The Seeker", "Ketu": "The Mystic",
}
_PLANET_STARS = {"exalted": 5, "own": 4, "neutral": 3, "debilitated": 1}
_CHAPTER_TITLE = {
    "Rahu": "The Awakening", "Jupiter": "The Leader", "Saturn": "The Builder",
    "Mercury": "The Strategist", "Ketu": "The Release", "Venus": "The Flourishing",
    "Sun": "The Authority", "Moon": "The Nurturer", "Mars": "The Driver",
}
_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
_PLANET_SYMBOL = {
    "Sun": "☉", "Moon": "☽", "Mars": "♂", "Mercury": "☿", "Jupiter": "♃",
    "Venus": "♀", "Saturn": "♄", "Rahu": "☊", "Ketu": "☋",
}

# ── Human-voice lookup tables (life first, astrology second) ──────────────
# Each planet as a character who "speaks" in first person — the Inner Council.
_COUNCIL = {
    "Sun":     ("The Sovereign", "I am the part of you that wants to matter — to be seen for who you truly are, not what you do for others."),
    "Moon":    ("The Caregiver", "When life turns chaotic, I am the one who reminds you what home feels like. Your softness is not weakness."),
    "Mars":    ("The Warrior", "You move best when your actions line up with something you actually believe in. Give me a real reason and I am unstoppable."),
    "Mercury": ("The Messenger", "I am your curiosity, your quick wit, the voice that needs to understand before it can rest."),
    "Jupiter": ("The Mentor", "I expand whatever you choose to believe in. Aim me at something worthy and I will grow it."),
    "Venus":   ("The Artist", "I am your longing for beauty, for love, for a life that feels worth living — not just one that works."),
    "Saturn":  ("The Old Teacher", "I will not hand you quick victories. I give you the permanent kind — slowly, and only after you have earned them."),
    "Rahu":    ("The Seeker", "I am your hunger for what you have not yet become. I pull you toward the unfamiliar, even when it frightens you."),
    "Ketu":    ("The Mystic", "I am the part of you already quietly tired of what others are still chasing. I know when to let go."),
}

# Dominant planet → a human "superpower" (headline, sentence)
_SUPERPOWER = {
    "Sun":     ("Quiet authority", "People sense you were meant to lead — not because you push, but because you carry a steadiness they instinctively trust."),
    "Moon":    ("A calming presence", "When life gets heavy, people come to you. You can steady a whole room without ever raising your voice."),
    "Mars":    ("Focused drive", "Once you decide something truly matters, you move toward it with a force very few people can match."),
    "Mercury": ("A quick, clear mind", "You grasp things fast and explain them in a way that makes other people feel smart too. That is rarer than it looks."),
    "Jupiter": ("Natural wisdom", "People come to you for perspective. You tend to see the larger pattern while everyone else is lost in the moment."),
    "Venus":   ("Magnetic warmth", "You draw people, beauty and good things toward you. Relationships and taste are quiet superpowers of yours."),
    "Saturn":  ("Endurance others lack", "You outlast. Slow, patient, unglamorous effort is exactly where you quietly beat people who started ahead of you."),
    "Rahu":    ("A gift for reinvention", "You are willing to walk into the unknown that stops most people. That courage keeps becoming your edge."),
    "Ketu":    ("Effortless detachment", "You can release what others cling to. That freedom lets you move on cleanly while others stay stuck."),
}

# Debilitated / difficult planet → a compassionate "blind spot" (headline, sentence)
_BLINDSPOT = {
    "Sun":     ("Waiting for permission", "You may have spent years feeling behind, or quietly waiting to be chosen. You were never behind — you were being prepared."),
    "Moon":    ("Absorbing everyone's weather", "You feel other people's moods as if they were your own. Protecting your inner quiet is not selfish — it is survival."),
    "Mars":    ("Forcing the timing", "When you push against a closed door, you only tire yourself out. Your real wins come when you move with the moment, not against it."),
    "Mercury": ("Overthinking the simple", "Your mind can turn a small decision into a storm. Not every thought you have deserves your full belief."),
    "Jupiter": ("Expecting too much of yourself", "You hold a standard almost no one could meet, then quietly feel you've fallen short. Growth here means softening that judge."),
    "Venus":   ("Losing yourself in others", "You give warmth so freely that you sometimes forget your own needs. Loving yourself is part of the work, not a distraction from it."),
    "Saturn":  ("Being hard on yourself", "A quiet voice tells you you're never doing enough. It has carried you far — but it does not have to run the whole show."),
    "Rahu":    ("Chasing the next thing", "You reach for more before you've felt what you already have. The hunger is a gift, but it can also keep you from ever arriving."),
    "Ketu":    ("Pulling away too soon", "You detach when things get close or uncertain. Some things are worth staying for, even when part of you wants to disappear."),
}


# Closing-letter "lesson" keyed to the life-chapter (Mahadasha) being lived now.
_LETTER_LESSON = {
    "Rahu": {
        "ask": "more patience",
        "body": "Your chart suggests this isn't because you're falling behind. It's because you're "
                "building something that was never meant to be rushed.",
        "close": "The qualities that feel like burdens today may quietly become the very reasons "
                 "people come to depend on you tomorrow.",
    },
    "Saturn": {
        "ask": "more from you",
        "body": "The weight you've carried was never a punishment. It was practice — the slow forging "
                "of someone strong enough to hold what's coming.",
        "close": "Authority earned slowly is the kind that lasts. You are becoming unshakeable, one "
                 "quiet year at a time.",
    },
    "Jupiter": {
        "ask": "a wider heart",
        "body": "You were not made to shrink. This is a season of expansion — of saying yes to more "
                "than feels comfortable and watching it grow.",
        "close": "Your generosity is not a weakness to guard against. It is the exact thing this "
                 "chapter is asking you to trust.",
    },
    "Moon": {
        "ask": "more tenderness",
        "body": "Your sensitivity was never something to fix. It is how you understand people others "
                "can only guess at.",
        "close": "Protect your inner quiet, and it will keep giving you a kind of wisdom the loud "
                 "world can't reach.",
    },
    "Mercury": {
        "ask": "sharper focus",
        "body": "Your mind moves fast and wants everything at once. This chapter is teaching you to "
                "choose — to pour that brilliance into fewer, truer things.",
        "close": "You don't need to understand everything. You need to finish the few things that "
                 "actually matter to you.",
    },
    "_default": {
        "ask": "more of you",
        "body": "Your chart suggests this isn't because you're falling behind. It's because you're "
                "being shaped for something that takes time to build.",
        "close": "The qualities that feel heavy today may quietly become the reasons people trust "
                 "you tomorrow.",
    },
}


def _v2_derived(chart: dict, ai: dict, name: str = "") -> dict:
    """Deterministic, non-AI derivations for the V2 storytelling layout."""
    from datetime import datetime as _dt

    # Age
    age = None
    try:
        bd = chart.get("meta", {}).get("birth_date", "")
        by = int(bd[:4])
        age = _dt.utcnow().year - by
    except (ValueError, TypeError):
        pass

    # Life chapters from timeline periods
    periods = chart.get("timeline", {})
    periods = periods.get("periods", []) if isinstance(periods, dict) else (periods or [])
    chapters = []
    for i, p in enumerate(periods[:4]):
        lord = p.get("dasha_lord", "")
        chapters.append({
            "roman": _ROMAN[i] if i < len(_ROMAN) else str(i + 1),
            "title": _CHAPTER_TITLE.get(lord, "The Unfolding"),
            "age_range": f"{p.get('age_start', '?')}–{p.get('age_end', '?')}",
            "themes": p.get("themes", []),
            "quality": p.get("quality", ""),
        })

    # Planet gallery: epithet + star rating
    planets = {}
    for pname, pdata in (chart.get("planets") or {}).items():
        planets[pname] = {
            **pdata,
            "epithet": _PLANET_EPITHET.get(pname, ""),
            "stars": _PLANET_STARS.get(pdata.get("dignity"), 3),
        }

    # Yoga rarity
    yogas = []
    for y in (chart.get("yogas") or []):
        if isinstance(y, dict):
            yname = y.get("name", "Yoga")
            rare = "Very Rare" if "Raja" in yname else "Rare" if "Viparita" in yname else "Notable"
            yogas.append({**y, "rarity": rare})

    # Top 6 classical rules by strongest effect
    rules = chart.get("classical_rules") or []

    def _max_effect(r):
        eff = r.get("effects") or {}
        return max(eff.values()) if eff else 0

    top_rules = sorted(rules, key=_max_effect, reverse=True)[:6]

    # ── Reveal cards: Hidden Gift / Superpower / Blind Spot ──────────
    dna = chart.get("chart_dna") or {}
    raw_yogas = chart.get("yogas") or []
    mechanisms = (chart.get("analysis") or {}).get("dominant_mechanisms") or []
    planets_raw = chart.get("planets") or {}

    # HIDDEN GIFT — human first; the yoga is the quiet "why" underneath.
    has_viparita = any(isinstance(y, dict) and "Viparita" in y.get("name", "") for y in raw_yogas)
    has_raja = any(isinstance(y, dict) and "Raja" in y.get("name", "") for y in raw_yogas)
    if has_viparita:
        hidden_gift = {
            "headline": "You rise when everything falls",
            "detail": "Setbacks that would stop other people tend to become your turning points. "
                      "You seem to find your footing exactly where others lose theirs.",
            "why": "Viparita Raja Yoga — a rare pattern of strength through adversity.",
        }
    elif has_raja:
        hidden_gift = {
            "headline": "You grow into power",
            "detail": "You don't chase authority — you grow into it. The older you get, the more "
                      "naturally people turn to you when a decision has to be made.",
            "why": "Raja Yoga — the classical signature of earned leadership.",
        }
    else:
        hidden_gift = {
            "headline": dna.get("life_gift", "A quiet, uncommon strength"),
            "detail": "Your chart holds an advantage most people never notice about you until "
                      "much later — often not until your thirties.",
            "why": dna.get("core_mechanism", ""),
        }

    # SUPERPOWER — keyed to the dominant planet, spoken in human terms.
    dom_planet = dna.get("dominant_planet") or ((mechanisms[0] or {}).get("name", "").split()[0]
                                                if mechanisms else "")
    sp = _SUPERPOWER.get(dom_planet)
    superpower = {
        "headline": sp[0] if sp else "A steadying strength",
        "detail": sp[1] if sp else "There is a quality in you others rely on, even if you've never named it.",
        "why": f"Your strongest planet is the {dom_planet}." if dom_planet else "",
    }

    # BLIND SPOT — compassionate, keyed to the weakest planet (or the Rahu lesson).
    weak_planet = next((p for p, d in planets_raw.items() if d.get("dignity") == "debilitated"), None)
    bs = _BLINDSPOT.get(weak_planet) if weak_planet else None
    if not bs and (chart.get("dasha") or {}).get("mahadasha") == "Rahu":
        bs = ("Forcing the next chapter",
              "Every time you try to force what comes next, life slows you down — not to punish you, "
              "but to make sure your foundation can hold the weight of what you're asking for.")
    blind_spot = {
        "headline": bs[0] if bs else "Impatience with your own timing",
        "detail": bs[1] if bs else "Your growth tends to come from patience, not force. "
                                   "The slow path is building something the fast one can't.",
        "why": (f"A tender spot: your {weak_planet} sits in a difficult sign." if weak_planet else ""),
    }

    # ── Achievement badges (only from real, verifiable placements) ───
    badges, _seen_labels = [], set()

    def _add_badge(icon, label):
        if label not in _seen_labels:
            _seen_labels.add(label)
            badges.append({"icon": icon, "label": label})

    for y in raw_yogas:
        if isinstance(y, dict) and "Raja" in y.get("name", ""):
            _add_badge("⚔", y["name"])
    for pname, pdata in planets_raw.items():
        if pdata.get("dignity") == "exalted":
            _add_badge("🌟", f"{pname} Exalted")
    lagna_lord_house = (chart.get("house_lords") or {}).get("house_1_lord", {}).get("placed_in_house")
    if lagna_lord_house in (9, 10):
        _add_badge("🏆", "Born Leader")
    if planets_raw.get("Moon", {}).get("dignity") == "exalted":
        _add_badge("🌙", "Emotional Intelligence")
    jup_house = planets_raw.get("Jupiter", {}).get("house")
    if jup_house in (1, 5, 9):
        _add_badge("♃", "Teacher's Blessing")
    rahu_house = planets_raw.get("Rahu", {}).get("house")
    if rahu_house in (3, 6, 10, 11):
        _add_badge("🌍", "Ambition Amplifier")
    badges = badges[:6]

    # ── "If I only read one page" summary — human copy, not raw fields ──
    sc = ai.get("summary_card") or {}
    next_turn = chapters[1] if len(chapters) > 1 else (chapters[0] if chapters else None)
    top_recs = [r.get("title") for r in (ai.get("remedies") or [])[:3] if isinstance(r, dict)]
    onepage = {
        "archetype": dna.get("archetype_name", ""),
        "life_chapter": sc.get("life_chapter", ""),
        "strength": superpower["headline"] + " — " + superpower["detail"],
        "challenge": blind_spot["headline"] + " — " + blind_spot["detail"],
        "turning_point": (f"Age {next_turn['age_range']} — {next_turn['title']}" if next_turn else ""),
        "recommendations": top_recs,
        "north_star": dna.get("one_liner") or sc.get("insight_sentence", ""),
    }

    # ── Inner Council — planets as characters who speak to you ──────────
    council = []
    for pname, pdata in planets_raw.items():
        c = _COUNCIL.get(pname)
        if c:
            council.append({
                "planet": pname, "symbol": _PLANET_SYMBOL.get(pname, "✦"),
                "character": c[0], "voice": c[1],
                "sign": pdata.get("sign", ""), "house": pdata.get("house", ""),
                "dignity": pdata.get("dignity", "neutral"),
            })

    # ── Letter From Your Future Self — Claude's if present, else templated ──
    closing_letter = ai.get("closing_letter")
    if closing_letter and name:
        first = name.strip().split()[0]
        closing_letter = closing_letter.replace("Dear friend,", f"Dear {first},")
    if not closing_letter:
        maha = (chart.get("dasha") or {}).get("mahadasha", "")
        lesson = _LETTER_LESSON.get(maha, _LETTER_LESSON["_default"])
        first = (name or "friend").strip().split()[0] if name else "friend"
        closing_letter = (
            f"Dear {first},\n\n"
            f"You may spend the coming years quietly wondering why life seems to ask {lesson['ask']} "
            f"of you than it asks of others.\n\n"
            f"{lesson['body']}\n\n"
            f"Don't measure yourself against faster lives. Measure yourself against the person "
            f"you were a year ago.\n\n"
            f"{lesson['close']}\n\n"
            f"Wherever your path leads, remember this: the slow, honest way you are growing "
            f"is the kind that lasts.\n\n"
            f"— With love, the you who is already on the other side of this."
        )

    return {
        "age": age, "chapters": chapters, "planets_v2": planets,
        "yogas_v2": yogas, "top_rules": top_rules,
        "hidden_gift": hidden_gift, "superpower": superpower, "blind_spot": blind_spot,
        "badges": badges, "onepage": onepage, "planet_symbol": _PLANET_SYMBOL,
        "council": council, "closing_letter": closing_letter,
    }


@store_bp.route("/report-v2/<report_uuid>")
def view_report_v2(report_uuid):
    """V2 storytelling report — new template, same access control and data."""
    report = Report.query.filter_by(uuid=report_uuid).first_or_404()
    purchase = report.purchase

    owns = (report_uuid in _owned_uuids()) or (
        purchase.user_id and session.get("user_id") == purchase.user_id
    ) or _dev_mode()  # local dev only: no Razorpay keys + debug on
    if purchase.status != "paid" or not owns:
        return render_template("store/cancel.html",
                               title="Report locked",
                               message="This report belongs to another purchase. "
                                       "Open it from the device you paid on, or sign in "
                                       "with the account used at checkout."), 403

    chart = report.chart()
    ai = _ensure_ai(report)
    derived = _v2_derived(chart, ai, purchase.name or "")
    return render_template("store/report_v2.html", chart=chart, ai=ai,
                           purchase=purchase, report=report, **derived)


@store_bp.route("/cancel")
def cancel():
    return render_template("store/cancel.html",
                           title="Payment cancelled",
                           message="No charge was made. Your preview is saved — "
                                   "you can unlock the full report any time.")


@store_bp.route("/admin")
def admin():
    key = current_app.config.get("STORE_ADMIN_KEY") or ""
    import os
    key = key or os.getenv("STORE_ADMIN_KEY", "")
    if key:
        if request.args.get("key") != key:
            abort(403)
    elif not current_app.debug:
        abort(403)

    total_paid = Purchase.total_paid()
    info = get_price_info(total_paid)

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_rows = Purchase.query.filter(Purchase.status == "paid",
                                       Purchase.paid_at >= today).all()
    todays_revenue = sum(p.price_paid or 0 for p in today_rows)

    pending = Purchase.query.filter_by(status="created").count()
    recent = (Purchase.query.order_by(Purchase.created_at.desc()).limit(12).all())

    # 14-day revenue series for the bar chart
    days = []
    for i in range(13, -1, -1):
        d0 = today - timedelta(days=i)
        d1 = d0 + timedelta(days=1)
        rows = Purchase.query.filter(Purchase.status == "paid",
                                     Purchase.paid_at >= d0,
                                     Purchase.paid_at < d1).all()
        days.append({"label": d0.strftime("%d %b"),
                     "revenue": sum(p.price_paid or 0 for p in rows),
                     "count": len(rows)})
    max_rev = max((d["revenue"] for d in days), default=0) or 1

    total_revenue = sum(
        p.price_paid or 0
        for p in Purchase.query.filter_by(status="paid").all()
    )

    return render_template("store/admin.html",
                           total_paid=total_paid, info=info,
                           todays_revenue=todays_revenue,
                           total_revenue=total_revenue,
                           pending=pending, recent=recent,
                           days=days, max_rev=max_rev, tiers=PRICE_TIERS)


# ── API ──────────────────────────────────────────────────────────────────────

@store_bp.route("/api/preview", methods=["POST"])
def api_preview():
    """Build the chart once, cache it, return the checkout URL."""
    if _rate_limited(f"prev:{request.remote_addr}", limit=8):
        return jsonify(error="Too many requests — please wait a minute."), 429

    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    mobile = re.sub(r"[\s()\-]", "", str(data.get("mobile", "")))
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return jsonify(error="Enter a valid email address."), 400
    if mobile and not re.fullmatch(r"\+?[0-9]{8,15}", mobile):
        return jsonify(error="Enter a valid mobile number or leave it blank."), 400
    try:
        year, month, day = int(data["year"]), int(data["month"]), int(data["day"])
        hour, minute = int(data["hour"]), int(data["minute"])
        lat, lon = float(data["lat"]), float(data["lon"])
        tz = float(data.get("timezone", 5.5))
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Invalid birth details."), 400
    if not (-90 <= lat <= 90 and -180 <= lon <= 180 and 1 <= month <= 12):
        return jsonify(error="Invalid coordinates or date."), 400

    from engine.chart import build_chart
    from rag.rule_engine import query_rules
    try:
        chart = build_chart(year, month, day, hour, minute, lat, lon,
                            timezone_offset=tz, name=str(data.get("name", ""))[:100])
        # RAG: retrieve matching classical rules (BPHS, Phaladeepika, 300 Combinations)
        chart["classical_rules"] = query_rules(chart, top_k=12)
    except Exception as e:                       # noqa: BLE001
        log.exception("chart build failed")
        return jsonify(error=f"Chart calculation failed: {e}"), 500

    purchase = Purchase(
        name=str(data.get("name", ""))[:100],
        email=email[:255],
        mobile=mobile[:20] or None,
        birth_place=str(data.get("birth_place", ""))[:180],
        year=year, month=month, day=day, hour=hour, minute=minute,
        lat=lat, lon=lon, timezone=tz,
        user_id=session.get("user_id"),
    )
    db.session.add(purchase)
    db.session.flush()
    report = Report(purchase_id=purchase.id,
                    chart_json=json.dumps(chart, separators=(",", ":"), default=str))
    db.session.add(report)
    db.session.commit()

    return jsonify(checkout_url=f"/store/checkout/{purchase.uuid}")


@store_bp.route("/api/create-order", methods=["POST"])
def api_create_order():
    """Lock the server-side price and create a Razorpay order."""
    if _rate_limited(f"order:{request.remote_addr}", limit=10):
        return jsonify(error="Too many requests."), 429

    data = request.get_json(silent=True) or {}
    purchase = Purchase.query.filter_by(uuid=data.get("purchase_uuid", "")).first()
    if not purchase:
        return jsonify(error="Purchase not found."), 404
    if purchase.status == "paid":
        return jsonify(error="Already paid.",
                       report_url=f"/store/report-v2/{purchase.report.uuid}"), 409

    price = get_current_price(Purchase.total_paid())   # server-side, always
    purchase.price_paid = price

    if _dev_mode():
        purchase.razorpay_order_id = f"dev_order_{purchase.uuid[:12]}"
        db.session.add(PaymentEvent(purchase_id=purchase.id, event="order_created",
                                    detail="dev-mode simulated order"))
        db.session.commit()
        return jsonify(dev_mode=True, amount=price * 100,
                       order_id=purchase.razorpay_order_id)

    try:
        order = payments.create_order(price, receipt=purchase.uuid)
    except RuntimeError as e:
        log.error("razorpay order failed: %s", e)
        return jsonify(error="Payment gateway unavailable. Try again shortly."), 502

    purchase.razorpay_order_id = order["id"]
    db.session.add(PaymentEvent(purchase_id=purchase.id, event="order_created",
                                detail=order["id"]))
    db.session.commit()
    return jsonify(dev_mode=False, order_id=order["id"], amount=order["amount"],
                   currency="INR", key_id=payments.get_keys()[0],
                   name=purchase.name or "Astro Report")


def _mark_paid_and_generate(purchase: Purchase, event: str, detail: str) -> str:
    """Shared success path: mark paid, track tier, generate + cache report."""
    before = Purchase.total_paid()
    purchase.status = "paid"
    purchase.paid_at = datetime.utcnow()
    db.session.add(PaymentEvent(purchase_id=purchase.id, event=event, detail=detail))
    _record_tier_change(before, before + 1)
    db.session.commit()

    report = purchase.report
    _grant_ownership(report.uuid)
    _ensure_ai(report)          # generate once, cache forever
    relative_url = f"/store/report-v2/{report.uuid}"
    _deliver_report_email(purchase, report)
    return relative_url


def _deliver_report_email(purchase: Purchase, report: Report) -> None:
    """Send one delivery email after a verified payment; retries are webhook-safe."""
    already_sent = PaymentEvent.query.filter_by(
        purchase_id=purchase.id, event="report_email_sent"
    ).first()
    if already_sent or not purchase.email:
        return
    from services.mailer import send_report_link
    report_url = url_for("report_store.view_report_v2", report_uuid=report.uuid,
                         _external=True)
    if send_report_link(purchase.email, purchase.name, report_url):
        db.session.add(PaymentEvent(purchase_id=purchase.id,
                                    event="report_email_sent", detail=report_url))
        db.session.commit()


@store_bp.route("/api/verify", methods=["POST"])
def api_verify():
    """Server-side Razorpay signature verification. Never trusts the frontend."""
    data = request.get_json(silent=True) or {}
    order_id = data.get("razorpay_order_id", "")
    payment_id = data.get("razorpay_payment_id", "")
    signature = data.get("razorpay_signature", "")

    purchase = Purchase.query.filter_by(razorpay_order_id=order_id).first()
    if not purchase:
        return jsonify(error="Unknown order."), 404
    if purchase.status == "paid":
        return jsonify(success=True,
                       report_url=f"/store/report-v2/{purchase.report.uuid}")

    if not payments.verify_signature(order_id, payment_id, signature):
        purchase.status = "failed"
        db.session.add(PaymentEvent(purchase_id=purchase.id,
                                    event="signature_mismatch", detail=payment_id))
        db.session.commit()
        return jsonify(error="Payment verification failed."), 400

    purchase.razorpay_payment_id = payment_id
    purchase.razorpay_signature = signature
    url = _mark_paid_and_generate(purchase, "payment_verified", payment_id)
    return jsonify(success=True, report_url=url)


@store_bp.route("/api/razorpay/webhook", methods=["POST"])
def razorpay_webhook():
    """Razorpay server-to-server payment confirmation and email delivery."""
    raw_body = request.get_data(cache=True)
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not payments.verify_webhook_signature(raw_body, signature):
        log.warning("Rejected Razorpay webhook with invalid signature")
        return jsonify(error="Invalid webhook signature"), 400
    payload = request.get_json(silent=True) or {}
    if payload.get("event") not in {"payment.captured", "order.paid"}:
        return jsonify(status="ignored"), 200
    payment = ((payload.get("payload") or {}).get("payment") or {}).get("entity") or {}
    order_id = payment.get("order_id", "")
    purchase = Purchase.query.filter_by(razorpay_order_id=order_id).first()
    if not purchase:
        log.warning("Razorpay webhook for unknown order %s", order_id)
        return jsonify(status="unknown_order"), 200
    if purchase.status == "paid":
        _deliver_report_email(purchase, purchase.report)
        return jsonify(status="already_processed"), 200
    purchase.razorpay_payment_id = payment.get("id") or purchase.razorpay_payment_id
    _mark_paid_and_generate(purchase, "webhook_payment_captured",
                            payment.get("id", ""))
    return jsonify(status="processed"), 200


@store_bp.route("/api/dev-pay", methods=["POST"])
def api_dev_pay():
    """DEV-ONLY simulated payment — active only when Razorpay keys are absent
    and Flask debug is on. Never available in production."""
    if not _dev_mode():
        abort(404)
    data = request.get_json(silent=True) or {}
    purchase = Purchase.query.filter_by(uuid=data.get("purchase_uuid", "")).first()
    if not purchase:
        return jsonify(error="Purchase not found."), 404
    if purchase.status != "paid":
        purchase.razorpay_payment_id = "dev_payment_simulated"
        url = _mark_paid_and_generate(purchase, "dev_simulated", "local dev payment")
    else:
        url = f"/store/report-v2/{purchase.report.uuid}"
    return jsonify(success=True, report_url=url)


@store_bp.route("/api/pricing")
def api_pricing():
    return jsonify(get_price_info(Purchase.total_paid()))

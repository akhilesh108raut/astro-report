"""
Dynamic pricing engine for the Astro Report Store.

Price is a pure function of TOTAL PAID REPORTS, computed server-side only.
Never trust a price sent by the frontend.
"""

# (min_reports_inclusive, max_reports_inclusive, price_inr)
PRICE_TIERS = [
    (0,         999,        5),
    (1_000,     9_999,     10),
    (10_000,    99_999,    20),
    (100_000,   999_999,   30),
    (1_000_000, None,      49),   # hard ceiling — never exceed ₹49
]

MAX_PRICE = 49


def get_current_price(total_paid_reports: int) -> int:
    """Return the current report price in INR for a given sales count."""
    for lo, hi, price in PRICE_TIERS:
        if hi is None:
            if total_paid_reports >= lo:
                return min(price, MAX_PRICE)
        elif lo <= total_paid_reports <= hi:
            return price
    return MAX_PRICE


def get_price_info(total_paid_reports: int) -> dict:
    """
    Full pricing context for the landing page:
    current price, next price, and how many reports remain at this price.
    """
    current = get_current_price(total_paid_reports)
    next_price = None
    remaining = None
    for lo, hi, price in PRICE_TIERS:
        if hi is not None and lo <= total_paid_reports <= hi:
            remaining = hi - total_paid_reports + 1
            nxt = get_current_price(hi + 1)
            next_price = nxt if nxt != price else None
            break
    return {
        "total_paid_reports": total_paid_reports,
        "current_price": current,
        "next_price": next_price,
        "reports_left_at_this_price": remaining,
        "currency": "INR",
    }

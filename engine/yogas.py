"""
Classical Vedic yoga detection.
Each yoga returns a dict with name, planets involved, and brief rule.
"""

from .constants import KENDRA_HOUSES, TRIKONA_HOUSES, TRIK_HOUSES


def _planets_in_same_house(planet_data: dict) -> dict[int, list[str]]:
    house_map = {}
    for planet, info in planet_data.items():
        h = info["house"]
        house_map.setdefault(h, []).append(planet)
    return house_map


def _house_lord(house: int, house_lords: dict) -> str:
    return house_lords[house]


def detect_yogas(planet_data: dict, house_lords: dict) -> list[dict]:
    yogas = []
    house_map = _planets_in_same_house(planet_data)

    # --- Gajakesari Yoga ---
    # Jupiter in kendra (1,4,7,10) from Moon
    moon_house = planet_data["Moon"]["house"]
    jup_house = planet_data["Jupiter"]["house"]
    relative_house = (jup_house - moon_house) % 12 + 1
    if relative_house in KENDRA_HOUSES or jup_house == moon_house:
        yogas.append({
            "name": "Gajakesari Yoga",
            "planets": ["Jupiter", "Moon"],
            "rule": "Jupiter in kendra from Moon",
            "effect": "Intelligence, fame, prosperity"
        })

    # --- Budha-Aditya Yoga ---
    if "Mercury" in house_map.get(planet_data["Sun"]["house"], []):
        yogas.append({
            "name": "Budha-Aditya Yoga",
            "planets": ["Sun", "Mercury"],
            "rule": "Sun and Mercury conjunct",
            "effect": "Sharp intellect, administrative ability"
        })

    # --- Chandra-Mangal Yoga ---
    if planet_data["Moon"]["house"] == planet_data["Mars"]["house"]:
        yogas.append({
            "name": "Chandra-Mangal Yoga",
            "planets": ["Moon", "Mars"],
            "rule": "Moon and Mars conjunct",
            "effect": "Financial gains, bold and energetic temperament"
        })

    # --- Raja Yoga ---
    # Lord of kendra + lord of trikona conjunct, exchange, or aspect
    kendra_lords = {house_lords[h] for h in KENDRA_HOUSES}
    trikona_lords = {house_lords[h] for h in TRIKONA_HOUSES}
    raj_yoga_pairs = []
    for kl in kendra_lords:
        for tl in trikona_lords:
            if kl == tl:
                continue
            kl_house = planet_data.get(kl, {}).get("house")
            tl_house = planet_data.get(tl, {}).get("house")
            if kl_house is None or tl_house is None:
                continue
            # Conjunction
            if kl_house == tl_house:
                raj_yoga_pairs.append((kl, tl, "conjunction"))
            # Mutual aspect: planets 7 houses apart
            elif abs(kl_house - tl_house) == 6:
                raj_yoga_pairs.append((kl, tl, "mutual aspect"))

    for kl, tl, method in raj_yoga_pairs:
        yogas.append({
            "name": "Raja Yoga",
            "planets": [kl, tl],
            "rule": f"Kendra lord {kl} and trikona lord {tl} in {method}",
            "effect": "Authority, success, leadership"
        })

    # --- Dhana Yoga ---
    # Lords of 2nd and 11th conjunct or exchange
    lord_2 = house_lords[2]
    lord_11 = house_lords[11]
    if lord_2 != lord_11:
        h2 = planet_data.get(lord_2, {}).get("house")
        h11 = planet_data.get(lord_11, {}).get("house")
        if h2 is not None and h11 is not None:
            if h2 == h11:
                yogas.append({
                    "name": "Dhana Yoga",
                    "planets": [lord_2, lord_11],
                    "rule": f"2nd lord {lord_2} and 11th lord {lord_11} conjunct",
                    "effect": "Wealth accumulation"
                })

    # --- Viparita Raja Yoga ---
    # Lord of trik house (6,8,12) placed in another trik house
    for trik_house in TRIK_HOUSES:
        lord = house_lords[trik_house]
        lord_placement = planet_data.get(lord, {}).get("house")
        if lord_placement in TRIK_HOUSES and lord_placement != trik_house:
            yogas.append({
                "name": "Viparita Raja Yoga",
                "planets": [lord],
                "rule": f"{trik_house}th lord {lord} placed in {lord_placement}th house",
                "effect": "Success through adversity, resilience"
            })

    # --- Panch Mahapurusha Yogas ---
    # Strong planet in own/exalted sign in kendra
    mahapurusha_map = {
        "Mars": "Ruchaka",
        "Mercury": "Bhadra",
        "Jupiter": "Hamsa",
        "Venus": "Malavya",
        "Saturn": "Sasa",
    }
    for planet, yoga_name in mahapurusha_map.items():
        dignity = planet_data.get(planet, {}).get("dignity", "")
        house = planet_data.get(planet, {}).get("house")
        if dignity in ("exalted", "own") and house in KENDRA_HOUSES:
            yogas.append({
                "name": yoga_name + " Yoga (Pancha Mahapurusha)",
                "planets": [planet],
                "rule": f"{planet} exalted/own in kendra (house {house})",
                "effect": f"Strong {planet} qualities: exceptional traits of that planet"
            })

    return yogas

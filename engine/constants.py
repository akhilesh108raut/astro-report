SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "PurvaPhalguni", "UttaraPhalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "PurvaAshadha", "UttaraAshadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "PurvaBhadrapada", "UttaraBhadrapada", "Revati"
]

# Vimshottari dasha order and years
DASHA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
               "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
DASHA_CYCLE = 120

# Which nakshatra starts which dasha (index maps to DASHA_LORDS cycle)
# Ashwini(0)=Ketu, Bharani(1)=Venus, ..., cycling every 9
NAKSHATRA_DASHA_LORD = [DASHA_LORDS[i % 9] for i in range(27)]

PLANET_NAMES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

# Exaltation degrees (sign_index, degree)
EXALTATION = {
    "Sun": (0, 10),       # Aries 10°
    "Moon": (1, 3),       # Taurus 3°
    "Mars": (9, 28),      # Capricorn 28°
    "Mercury": (5, 15),   # Virgo 15°
    "Jupiter": (3, 5),    # Cancer 5°
    "Venus": (11, 27),    # Pisces 27°
    "Saturn": (6, 20),    # Libra 20°
    "Rahu": (1, 20),      # Taurus 20°
    "Ketu": (7, 20),      # Scorpio 20°
}

DEBILITATION = {
    "Sun": (6, 10),
    "Moon": (7, 3),
    "Mars": (3, 28),
    "Mercury": (11, 15),
    "Jupiter": (9, 5),
    "Venus": (5, 27),
    "Saturn": (0, 20),
    "Rahu": (7, 20),
    "Ketu": (1, 20),
}

# Own signs
OWN_SIGNS = {
    "Sun": ["Leo"],
    "Moon": ["Cancer"],
    "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"],
    "Saturn": ["Capricorn", "Aquarius"],
}

KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
TRIK_HOUSES = {6, 8, 12}

"""
Celestial Insights - Astrological Calculation Engine
=====================================================
A comprehensive astrology calculation engine that computes natal charts,
planetary positions, aspects, and houses based on birth data.

This engine is DETERMINISTIC - identical birth data will always produce
identical results because planetary positions are based on precise 
astronomical algorithms using ephemeris data.

Requirements:
    pip install ephem pytz timezonefinder

Author: Celestial Insights
License: Proprietary
"""

import ephem
import math
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import json
from enum import Enum
import hashlib

# ============================================
# CONSTANTS & CONFIGURATION
# ============================================

class Planet(Enum):
    SUN = "Sun"
    MOON = "Moon"
    MERCURY = "Mercury"
    VENUS = "Venus"
    MARS = "Mars"
    JUPITER = "Jupiter"
    SATURN = "Saturn"
    URANUS = "Uranus"
    NEPTUNE = "Neptune"
    PLUTO = "Pluto"
    NORTH_NODE = "North Node"
    CHIRON = "Chiron"

class ZodiacSign(Enum):
    ARIES = ("Aries", "♈", "Fire", "Cardinal")
    TAURUS = ("Taurus", "♉", "Earth", "Fixed")
    GEMINI = ("Gemini", "♊", "Air", "Mutable")
    CANCER = ("Cancer", "♋", "Water", "Cardinal")
    LEO = ("Leo", "♌", "Fire", "Fixed")
    VIRGO = ("Virgo", "♍", "Earth", "Mutable")
    LIBRA = ("Libra", "♎", "Air", "Cardinal")
    SCORPIO = ("Scorpio", "♏", "Water", "Fixed")
    SAGITTARIUS = ("Sagittarius", "♐", "Fire", "Mutable")
    CAPRICORN = ("Capricorn", "♑", "Earth", "Cardinal")
    AQUARIUS = ("Aquarius", "♒", "Air", "Fixed")
    PISCES = ("Pisces", "♓", "Water", "Mutable")
    
    @property
    def name_str(self):
        return self.value[0]
    
    @property
    def symbol(self):
        return self.value[1]
    
    @property
    def element(self):
        return self.value[2]
    
    @property
    def modality(self):
        return self.value[3]

class AspectType(Enum):
    CONJUNCTION = ("Conjunction", 0, 8, "Major")
    SEXTILE = ("Sextile", 60, 6, "Major")
    SQUARE = ("Square", 90, 8, "Major")
    TRINE = ("Trine", 120, 8, "Major")
    OPPOSITION = ("Opposition", 180, 8, "Major")
    QUINCUNX = ("Quincunx", 150, 3, "Minor")
    SEMI_SEXTILE = ("Semi-Sextile", 30, 2, "Minor")
    SEMI_SQUARE = ("Semi-Square", 45, 2, "Minor")
    SESQUIQUADRATE = ("Sesquiquadrate", 135, 2, "Minor")

HOUSE_MEANINGS = {
    1: {"name": "First House", "theme": "Self, Identity, Appearance", 
        "description": "The house of self-identity, physical appearance, and how you present yourself to the world."},
    2: {"name": "Second House", "theme": "Values, Possessions, Money",
        "description": "The house of personal resources, values, self-worth, and material possessions."},
    3: {"name": "Third House", "theme": "Communication, Siblings, Short Journeys",
        "description": "The house of communication, learning, siblings, and local environment."},
    4: {"name": "Fourth House", "theme": "Home, Family, Roots",
        "description": "The house of home, family, ancestry, and emotional foundations."},
    5: {"name": "Fifth House", "theme": "Creativity, Romance, Children",
        "description": "The house of creativity, self-expression, romance, and children."},
    6: {"name": "Sixth House", "theme": "Health, Work, Service",
        "description": "The house of daily routines, health, work, and service to others."},
    7: {"name": "Seventh House", "theme": "Partnerships, Marriage, Contracts",
        "description": "The house of partnerships, marriage, and one-on-one relationships."},
    8: {"name": "Eighth House", "theme": "Transformation, Shared Resources, Intimacy",
        "description": "The house of transformation, shared resources, and deep psychological processes."},
    9: {"name": "Ninth House", "theme": "Philosophy, Travel, Higher Learning",
        "description": "The house of philosophy, higher education, long-distance travel, and beliefs."},
    10: {"name": "Tenth House", "theme": "Career, Public Image, Achievement",
        "description": "The house of career, public reputation, and life achievements."},
    11: {"name": "Eleventh House", "theme": "Friends, Groups, Hopes",
        "description": "The house of friendships, social groups, hopes, and humanitarian ideals."},
    12: {"name": "Twelfth House", "theme": "Subconscious, Spirituality, Hidden Matters",
        "description": "The house of the subconscious, spirituality, and hidden aspects of life."}
}

# ============================================
# DATA CLASSES
# ============================================

@dataclass
class BirthData:
    """Birth information required for chart calculation."""
    name: str
    birth_date: datetime
    latitude: float
    longitude: float
    timezone_str: str
    
    def get_unique_hash(self) -> str:
        """Generate deterministic hash for caching/consistency verification."""
        data_str = f"{self.birth_date.isoformat()}|{self.latitude:.6f}|{self.longitude:.6f}"
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

@dataclass
class PlanetaryPosition:
    """Position of a celestial body."""
    planet: Planet
    longitude: float
    latitude: float
    sign: ZodiacSign
    sign_degree: float
    retrograde: bool
    house: int = 0
    
    @property
    def formatted_position(self) -> str:
        degrees = int(self.sign_degree)
        minutes = int((self.sign_degree - degrees) * 60)
        retro = " ℞" if self.retrograde else ""
        return f"{degrees}° {minutes}' {self.sign.name_str}{retro}"

@dataclass
class Aspect:
    """Aspect between two planets."""
    planet1: Planet
    planet2: Planet
    aspect_type: AspectType
    orb: float
    applying: bool
    
    @property
    def strength(self) -> str:
        if self.orb <= 1:
            return "Exact"
        elif self.orb <= 3:
            return "Strong"
        elif self.orb <= 5:
            return "Moderate"
        else:
            return "Weak"

@dataclass
class HouseCusp:
    """House cusp position."""
    house_number: int
    longitude: float
    sign: ZodiacSign
    sign_degree: float
    
    @property
    def formatted_position(self) -> str:
        degrees = int(self.sign_degree)
        minutes = int((self.sign_degree - degrees) * 60)
        return f"{degrees}° {minutes}' {self.sign.name_str}"

@dataclass
class NatalChart:
    """Complete natal chart data."""
    birth_data: BirthData
    planets: Dict[Planet, PlanetaryPosition]
    houses: List[HouseCusp]
    aspects: List[Aspect]
    ascendant: float
    midheaven: float
    chart_hash: str
    
    @property
    def sun_sign(self) -> ZodiacSign:
        return self.planets[Planet.SUN].sign
    
    @property
    def moon_sign(self) -> ZodiacSign:
        return self.planets[Planet.MOON].sign
    
    @property
    def rising_sign(self) -> ZodiacSign:
        return get_zodiac_sign(self.ascendant)
    
    def to_dict(self) -> dict:
        return {
            "birth_data": {
                "name": self.birth_data.name,
                "birth_date": self.birth_data.birth_date.isoformat(),
                "latitude": self.birth_data.latitude,
                "longitude": self.birth_data.longitude,
                "timezone": self.birth_data.timezone_str
            },
            "chart_hash": self.chart_hash,
            "ascendant": self.ascendant,
            "midheaven": self.midheaven,
            "sun_sign": self.sun_sign.name_str,
            "moon_sign": self.moon_sign.name_str,
            "rising_sign": self.rising_sign.name_str,
            "planets": {
                p.planet.value: {
                    "longitude": p.longitude,
                    "sign": p.sign.name_str,
                    "sign_degree": p.sign_degree,
                    "house": p.house,
                    "retrograde": p.retrograde,
                    "formatted": p.formatted_position
                } for p in self.planets.values()
            },
            "houses": [
                {
                    "house": h.house_number,
                    "longitude": h.longitude,
                    "sign": h.sign.name_str,
                    "sign_degree": h.sign_degree,
                    "formatted": h.formatted_position
                } for h in self.houses
            ],
            "aspects": [
                {
                    "planet1": a.planet1.value,
                    "planet2": a.planet2.value,
                    "type": a.aspect_type.value[0],
                    "orb": round(a.orb, 2),
                    "applying": a.applying,
                    "strength": a.strength
                } for a in self.aspects
            ]
        }

# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_zodiac_sign(longitude: float) -> ZodiacSign:
    signs = list(ZodiacSign)
    sign_index = int(longitude / 30) % 12
    return signs[sign_index]

def get_sign_degree(longitude: float) -> float:
    return longitude % 30

def normalize_angle(angle: float) -> float:
    while angle < 0:
        angle += 360
    while angle >= 360:
        angle -= 360
    return angle

# ============================================
# MAIN CALCULATION ENGINE
# ============================================

class AstrologyEngine:
    """Main engine for calculating natal charts."""
    
    def __init__(self):
        self.planet_objects = {
            Planet.SUN: ephem.Sun,
            Planet.MOON: ephem.Moon,
            Planet.MERCURY: ephem.Mercury,
            Planet.VENUS: ephem.Venus,
            Planet.MARS: ephem.Mars,
            Planet.JUPITER: ephem.Jupiter,
            Planet.SATURN: ephem.Saturn,
            Planet.URANUS: ephem.Uranus,
            Planet.NEPTUNE: ephem.Neptune,
            Planet.PLUTO: ephem.Pluto,
        }
    
    def calculate_chart(self, birth_data: BirthData) -> NatalChart:
        observer = ephem.Observer()
        observer.lat = str(birth_data.latitude)
        observer.lon = str(birth_data.longitude)
        observer.date = ephem.Date(birth_data.birth_date)
        observer.pressure = 0
        
        planets = self._calculate_planets(observer)
        houses = self._calculate_houses(observer, birth_data.latitude)
        ascendant = houses[0].longitude
        midheaven = houses[9].longitude
        planets = self._assign_houses(planets, houses)
        aspects = self._calculate_aspects(planets)
        chart_hash = birth_data.get_unique_hash()
        
        return NatalChart(
            birth_data=birth_data,
            planets=planets,
            houses=houses,
            aspects=aspects,
            ascendant=ascendant,
            midheaven=midheaven,
            chart_hash=chart_hash
        )
    
    def _calculate_planets(self, observer: ephem.Observer) -> Dict[Planet, PlanetaryPosition]:
        positions = {}
        
        for planet_enum, planet_class in self.planet_objects.items():
            body = planet_class()
            body.compute(observer)
            
            ecl = ephem.Ecliptic(body)
            longitude = math.degrees(float(ecl.lon))
            latitude = math.degrees(float(ecl.lat))
            longitude = normalize_angle(longitude)
            
            sign = get_zodiac_sign(longitude)
            sign_degree = get_sign_degree(longitude)
            
            retrograde = False
            if planet_enum not in [Planet.SUN, Planet.MOON]:
                observer_future = observer.copy()
                observer_future.date = observer.date + 1
                body_future = planet_class()
                body_future.compute(observer_future)
                ecl_future = ephem.Ecliptic(body_future)
                future_lon = math.degrees(float(ecl_future.lon))
                diff = normalize_angle(future_lon - longitude)
                if diff > 180:
                    diff -= 360
                retrograde = diff < 0
            
            positions[planet_enum] = PlanetaryPosition(
                planet=planet_enum,
                longitude=longitude,
                latitude=latitude,
                sign=sign,
                sign_degree=sign_degree,
                retrograde=retrograde
            )
        
        north_node = self._calculate_north_node(observer)
        positions[Planet.NORTH_NODE] = north_node
        
        return positions
    
    def _calculate_north_node(self, observer: ephem.Observer) -> PlanetaryPosition:
        jd = ephem.julian_date(observer.date)
        T = (jd - 2451545.0) / 36525.0
        omega = 125.04452 - 1934.136261 * T + 0.0020708 * T**2
        longitude = normalize_angle(omega)
        sign = get_zodiac_sign(longitude)
        sign_degree = get_sign_degree(longitude)
        
        return PlanetaryPosition(
            planet=Planet.NORTH_NODE,
            longitude=longitude,
            latitude=0,
            sign=sign,
            sign_degree=sign_degree,
            retrograde=True
        )
    
    def _calculate_houses(self, observer: ephem.Observer, latitude: float) -> List[HouseCusp]:
        houses = []
        lst = float(observer.sidereal_time()) * 180 / math.pi
        obliquity = 23.4393
        ramc = lst
        
        mc = math.atan2(math.sin(math.radians(ramc)), 
                       math.cos(math.radians(ramc)) * math.cos(math.radians(obliquity)))
        mc = math.degrees(mc)
        mc = normalize_angle(mc)
        
        lat_rad = math.radians(latitude)
        obl_rad = math.radians(obliquity)
        
        y = -math.cos(math.radians(ramc))
        x = math.sin(math.radians(ramc)) * math.cos(obl_rad) + math.tan(lat_rad) * math.sin(obl_rad)
        asc = math.degrees(math.atan2(y, x))
        asc = normalize_angle(asc + 180)
        
        house_cusps = [asc]
        
        for i in range(1, 12):
            if i == 9:
                cusp = mc
            elif i == 3:
                cusp = normalize_angle(mc + 180)
            elif i == 6:
                cusp = normalize_angle(asc + 180)
            else:
                if i < 3:
                    cusp = normalize_angle(asc + (i * 30))
                elif i < 6:
                    cusp = normalize_angle(asc + 180 - ((6 - i) * 30))
                elif i < 9:
                    cusp = normalize_angle(asc + 180 + ((i - 6) * 30))
                else:
                    cusp = normalize_angle(asc - ((12 - i) * 30))
            
            house_cusps.append(cusp)
        
        for i, cusp_lon in enumerate(house_cusps):
            sign = get_zodiac_sign(cusp_lon)
            sign_degree = get_sign_degree(cusp_lon)
            houses.append(HouseCusp(
                house_number=i + 1,
                longitude=cusp_lon,
                sign=sign,
                sign_degree=sign_degree
            ))
        
        return houses
    
    def _assign_houses(self, planets: Dict[Planet, PlanetaryPosition], 
                       houses: List[HouseCusp]) -> Dict[Planet, PlanetaryPosition]:
        house_cusps = [h.longitude for h in houses]
        
        for planet in planets.values():
            planet_lon = planet.longitude
            
            for i in range(12):
                cusp_start = house_cusps[i]
                cusp_end = house_cusps[(i + 1) % 12]
                
                if cusp_start > cusp_end:
                    if planet_lon >= cusp_start or planet_lon < cusp_end:
                        planet.house = i + 1
                        break
                else:
                    if cusp_start <= planet_lon < cusp_end:
                        planet.house = i + 1
                        break
        
        return planets
    
    def _calculate_aspects(self, planets: Dict[Planet, PlanetaryPosition]) -> List[Aspect]:
        aspects = []
        planet_list = list(planets.values())
        
        for i, p1 in enumerate(planet_list):
            for p2 in planet_list[i + 1:]:
                angle = abs(p1.longitude - p2.longitude)
                if angle > 180:
                    angle = 360 - angle
                
                for aspect_type in AspectType:
                    aspect_angle = aspect_type.value[1]
                    orb_allowed = aspect_type.value[2]
                    
                    orb = abs(angle - aspect_angle)
                    
                    if orb <= orb_allowed:
                        applying = p1.retrograde != p2.retrograde
                        
                        aspects.append(Aspect(
                            planet1=p1.planet,
                            planet2=p2.planet,
                            aspect_type=aspect_type,
                            orb=orb,
                            applying=applying
                        ))
                        break
        
        aspects.sort(key=lambda a: a.orb)
        return aspects


# ============================================
# INTERPRETATION ENGINE
# ============================================

class InterpretationEngine:
    """Generate interpretive text for chart placements."""
    
    def __init__(self):
        self._load_interpretations()
    
    def _load_interpretations(self):
        self.sun_interpretations = {
            ZodiacSign.ARIES: {
                "title": "The Trailblazer",
                "core_identity": """With your Sun in Aries, you possess an innate pioneering spirit that drives you to be first in all endeavors. Your soul craves new beginnings, fresh challenges, and the thrill of uncharted territory. You are a natural leader, blessed with courage, enthusiasm, and an infectious energy that inspires others to follow your vision.

Your identity is forged through action and initiative. You learn about yourself by doing, not by contemplating. This cardinal fire energy gives you remarkable self-starting abilities—you don't wait for permission or perfect conditions. When you see something that needs to be done, you act.

The Aries Sun bestows upon you an honest, direct nature. You value authenticity and have little patience for pretense or manipulation. What you see is what you get with you, and you expect the same from others.""",
                "strengths": ["Natural leadership", "Courage and bravery", "Initiative and self-starting ability", "Enthusiasm and optimism", "Honesty and directness"],
                "challenges": ["Impatience with slower processes", "Tendency toward impulsiveness", "May overlook details in eagerness to act", "Can be perceived as aggressive"],
                "life_purpose": "Your purpose involves breaking new ground and inspiring others through your courageous example."
            },
            ZodiacSign.TAURUS: {
                "title": "The Builder",
                "core_identity": """With your Sun in Taurus, you embody the archetype of the steadfast builder who creates lasting value in the world. Your soul seeks security, beauty, and the sensual pleasures that make life worth living. You understand that good things take time to cultivate.

Your identity is rooted in what you can touch, taste, and hold. You have a profound appreciation for the material world—not from greed, but from understanding that physical comfort and beauty nourish the soul.

The Taurus Sun grants you remarkable determination and patience. Once you commit to a path, you pursue it with unwavering persistence.""",
                "strengths": ["Remarkable patience and persistence", "Strong practical abilities", "Appreciation for beauty and quality", "Loyal and dependable nature"],
                "challenges": ["Resistance to necessary change", "Can be possessive", "May become too focused on material security", "Stubbornness"],
                "life_purpose": "Your purpose involves building lasting structures that provide security and beauty for yourself and others."
            },
            ZodiacSign.GEMINI: {
                "title": "The Communicator",
                "core_identity": """With your Sun in Gemini, you are blessed with one of the zodiac's most versatile and curious minds. Your soul hungers for information, connection, and endless variety. You are the eternal student, finding fascination in subjects that others might overlook.

Your identity is expressed through communication in all its forms. Whether through writing, speaking, or engaging conversation, you come alive when exchanging ideas.

The Gemini Sun bestows upon you remarkable adaptability. You can shift between different roles, social groups, and topics with enviable ease.""",
                "strengths": ["Quick, versatile intelligence", "Excellent communication skills", "Adaptability and flexibility", "Youthful curiosity and wit"],
                "challenges": ["May scatter energy across too many interests", "Can be perceived as superficial", "Difficulty with deep emotional commitment", "Restlessness"],
                "life_purpose": "Your purpose involves gathering and sharing information, connecting people and ideas."
            },
            ZodiacSign.CANCER: {
                "title": "The Nurturer",
                "core_identity": """With your Sun in Cancer, you carry within you the archetype of the Great Mother—the one who nurtures, protects, and creates sanctuary. Your soul is profoundly connected to the rhythms of emotion, family, and invisible bonds that connect people across time.

Your identity is intimately connected to your roots—your family, heritage, and home. These aren't just external circumstances; they are part of who you are at the deepest level.

The Cancer Sun grants you remarkable emotional intelligence. You sense what others feel, often before they do themselves.""",
                "strengths": ["Deep emotional intelligence", "Strong nurturing instincts", "Powerful intuition", "Tenacious protective nature"],
                "challenges": ["Tendency to take things personally", "Can be moody or withdrawn", "May cling to the past", "Indirect communication"],
                "life_purpose": "Your purpose involves creating emotional security for yourself and others, honoring the past while nurturing growth."
            },
            ZodiacSign.LEO: {
                "title": "The Radiant One",
                "core_identity": """With your Sun in Leo, you carry the solar fire at the center of your being. Your soul seeks to shine, to create, and to be recognized for your unique gifts. There is nothing small about your spirit—you are here to make an impression.

Your identity is expressed through creative self-expression in whatever form calls to you. Whether through art, performance, or leadership, you are meant to be noticed.

The Leo Sun bestows upon you a generous heart and natural dignity. You have an instinct for nobility in yourself and others.""",
                "strengths": ["Natural charisma and leadership", "Generous and warm-hearted nature", "Creative self-expression", "Courage and confidence"],
                "challenges": ["Need for recognition can become excessive", "Pride may prevent asking for help", "Can dominate rather than lead", "May struggle when not in spotlight"],
                "life_purpose": "Your purpose involves expressing your unique creative gifts and inspiring others through warmth and generosity."
            },
            ZodiacSign.VIRGO: {
                "title": "The Analyst",
                "core_identity": """With your Sun in Virgo, you possess one of the zodiac's most refined and analytical minds. Your soul finds meaning through service, improvement, and the pursuit of excellence. You see the potential for perfection in imperfect things.

Your identity is expressed through your work and dedication to craft. You are the artisan of the zodiac, finding satisfaction in doing things well.

The Virgo Sun grants you exceptional powers of discrimination and analysis. You can break complex problems into manageable parts.""",
                "strengths": ["Exceptional analytical abilities", "Dedication to excellence and craft", "Practical problem-solving skills", "Humble and service-oriented nature"],
                "challenges": ["Tendency toward excessive self-criticism", "May become lost in details", "Can be overly critical of others", "Difficulty accepting imperfection"],
                "life_purpose": "Your purpose involves refining, improving, and serving—using your gifts to make the world work better."
            },
            ZodiacSign.LIBRA: {
                "title": "The Harmonizer",
                "core_identity": """With your Sun in Libra, you are the zodiac's natural diplomat and artist, blessed with an innate sense of balance and beauty. Your soul seeks harmony—in relationships, aesthetics, and the social fabric of the world.

Your identity is profoundly relational. You understand yourself through connections with others, and you have a gift for seeing multiple perspectives simultaneously.

The Libra Sun bestows upon you refined aesthetic sensibilities and social grace. You naturally create beauty and harmony wherever you go.""",
                "strengths": ["Natural diplomatic abilities", "Strong aesthetic sense", "Fairness and objectivity", "Grace in social situations"],
                "challenges": ["Difficulty making decisions", "May avoid necessary conflict", "Can lose self in relationships", "People-pleasing tendencies"],
                "life_purpose": "Your purpose involves creating harmony, beauty, and justice—serving as a bridge between opposing forces."
            },
            ZodiacSign.SCORPIO: {
                "title": "The Transformer",
                "core_identity": """With your Sun in Scorpio, you carry within you the power of transformation itself. Your soul is not content with surface appearances—you must know the truth, no matter how deep you have to dive. You are the zodiac's psychologist, detective, and alchemist.

Your identity is forged in the fires of emotional intensity. You feel everything deeply, and this depth is both your greatest gift and challenge.

The Scorpio Sun grants you extraordinary emotional power and psychological insight. You see beneath masks and through pretenses.""",
                "strengths": ["Profound psychological insight", "Emotional depth and intensity", "Transformative power", "Unwavering determination"],
                "challenges": ["Tendency toward intensity and jealousy", "May struggle to let go", "Can be secretive or controlling", "All-or-nothing approach"],
                "life_purpose": "Your purpose involves transformation—your own and others'. You are here to dive deep and emerge renewed."
            },
            ZodiacSign.SAGITTARIUS: {
                "title": "The Seeker",
                "core_identity": """With your Sun in Sagittarius, you embody the eternal quest for meaning, truth, and expansion. Your soul yearns for horizons—literal and metaphorical. You are the philosopher, adventurer, and eternal optimist.

Your identity is expressed through exploration and the pursuit of wisdom. Whether through travel, study, or spiritual seeking, you are constantly expanding.

The Sagittarius Sun bestows upon you infectious enthusiasm and unshakeable faith in life's goodness.""",
                "strengths": ["Philosophical depth and wisdom", "Adventurous spirit", "Optimism and faith", "Natural teaching abilities"],
                "challenges": ["May promise more than can be delivered", "Restlessness and difficulty with routine", "Tactlessness in pursuit of truth", "Can be preachy"],
                "life_purpose": "Your purpose involves seeking and sharing truth, expanding horizons, and inspiring others with your vision."
            },
            ZodiacSign.CAPRICORN: {
                "title": "The Achiever",
                "core_identity": """With your Sun in Capricorn, you are the zodiac's master builder, blessed with the patience, discipline, and ambition to create structures that endure. Your soul understands that lasting achievement requires time and effort.

Your identity is expressed through accomplishments and integrity. You measure yourself by what you've built, not by what you've dreamed.

The Capricorn Sun grants you remarkable self-discipline and strategic thinking. You can see the long game when others are distracted.""",
                "strengths": ["Exceptional discipline and patience", "Strategic long-term thinking", "Natural authority and leadership", "Integrity and reliability"],
                "challenges": ["May prioritize achievement over connection", "Can be too serious or rigid", "Difficulty showing vulnerability", "Work may become all-consuming"],
                "life_purpose": "Your purpose involves building lasting structures—in career, community, and legacy—that will endure beyond your lifetime."
            },
            ZodiacSign.AQUARIUS: {
                "title": "The Visionary",
                "core_identity": """With your Sun in Aquarius, you are the zodiac's revolutionary and humanitarian, blessed with a vision that sees beyond the limitations of the present. Your soul is oriented toward the future and humanity's potential.

Your identity is expressed through your unique perspective and commitment to authentic individuality. You are here to question assumptions and imagine new possibilities.

The Aquarius Sun grants you intellectual independence and courage to think differently.""",
                "strengths": ["Innovative and original thinking", "Humanitarian vision", "Intellectual independence", "Ability to see future possibilities"],
                "challenges": ["Can seem emotionally detached", "May prioritize ideas over people", "Rebelliousness for its own sake", "Difficulty with intimacy"],
                "life_purpose": "Your purpose involves envisioning and working toward a better future for humanity."
            },
            ZodiacSign.PISCES: {
                "title": "The Mystic",
                "core_identity": """With your Sun in Pisces, you carry within you the wisdom of all the signs that came before—you are the zodiac's culmination, blessed with profound compassion, creativity, and spiritual sensitivity.

Your identity is fluid and permeable. You feel the suffering of the world, and you long to heal it. Your boundaries between self and other are naturally thin.

The Pisces Sun grants you extraordinary imagination and compassion. You can envision possibilities that transcend current limitations.""",
                "strengths": ["Profound compassion and empathy", "Exceptional creativity and imagination", "Spiritual sensitivity", "Intuitive wisdom"],
                "challenges": ["May escape rather than confront", "Boundaries can be too permeable", "Vulnerability to deception", "Can lose self in others' needs"],
                "life_purpose": "Your purpose involves bringing compassion, creativity, and spiritual awareness to the world."
            }
        }
        
        self.moon_interpretations = {sign: {
            "emotional_nature": f"Your Moon in {sign.name_str} shapes your emotional landscape in distinctive ways.",
            "needs": f"With Moon in {sign.name_str}, you need emotional experiences aligned with {sign.element.lower()} energy.",
            "nurturing_style": f"You nurture others through the lens of {sign.name_str}'s qualities."
        } for sign in ZodiacSign}
    
    def get_sun_interpretation(self, sign: ZodiacSign) -> dict:
        return self.sun_interpretations.get(sign, {})
    
    def get_moon_interpretation(self, sign: ZodiacSign) -> dict:
        return self.moon_interpretations.get(sign, {})


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def create_chart(name: str, birth_date: datetime, latitude: float, 
                 longitude: float, timezone_str: str = "UTC") -> NatalChart:
    birth_data = BirthData(
        name=name,
        birth_date=birth_date,
        latitude=latitude,
        longitude=longitude,
        timezone_str=timezone_str
    )
    
    engine = AstrologyEngine()
    return engine.calculate_chart(birth_data)


def chart_to_json(chart: NatalChart) -> str:
    return json.dumps(chart.to_dict(), indent=2)


if __name__ == "__main__":
    from datetime import datetime
    
    birth_dt = datetime(1990, 6, 15, 14, 30)
    
    chart = create_chart(
        name="Example Person",
        birth_date=birth_dt,
        latitude=40.7128,
        longitude=-74.0060,
        timezone_str="America/New_York"
    )
    
    print(f"Chart for: {chart.birth_data.name}")
    print(f"Chart Hash: {chart.chart_hash}")
    print(f"\nSun Sign: {chart.sun_sign.name_str}")
    print(f"Moon Sign: {chart.moon_sign.name_str}")
    print(f"Rising Sign: {chart.rising_sign.name_str}")
    
    print("\n--- Planetary Positions ---")
    for planet, pos in chart.planets.items():
        print(f"{planet.value}: {pos.formatted_position} (House {pos.house})")

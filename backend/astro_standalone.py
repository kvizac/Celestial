"""
Celestial Insights - Standalone Astrological Calculation Engine
================================================================
Pure Python implementation - no external dependencies required.
"""

import math
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Tuple
import json
from enum import Enum
import hashlib


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


class ZodiacSign(Enum):
    ARIES = ("Aries", "Fire", "Cardinal")
    TAURUS = ("Taurus", "Earth", "Fixed")
    GEMINI = ("Gemini", "Air", "Mutable")
    CANCER = ("Cancer", "Water", "Cardinal")
    LEO = ("Leo", "Fire", "Fixed")
    VIRGO = ("Virgo", "Earth", "Mutable")
    LIBRA = ("Libra", "Air", "Cardinal")
    SCORPIO = ("Scorpio", "Water", "Fixed")
    SAGITTARIUS = ("Sagittarius", "Fire", "Mutable")
    CAPRICORN = ("Capricorn", "Earth", "Cardinal")
    AQUARIUS = ("Aquarius", "Air", "Fixed")
    PISCES = ("Pisces", "Water", "Mutable")
    
    @property
    def name_str(self): return self.value[0]
    @property
    def element(self): return self.value[1]
    @property
    def modality(self): return self.value[2]


class AspectType(Enum):
    CONJUNCTION = ("Conjunction", 0, 8)
    SEXTILE = ("Sextile", 60, 6)
    SQUARE = ("Square", 90, 8)
    TRINE = ("Trine", 120, 8)
    OPPOSITION = ("Opposition", 180, 8)


HOUSE_MEANINGS = {
    1: {"name": "First House", "theme": "Self, Identity, Appearance"},
    2: {"name": "Second House", "theme": "Values, Possessions, Money"},
    3: {"name": "Third House", "theme": "Communication, Learning"},
    4: {"name": "Fourth House", "theme": "Home, Family, Roots"},
    5: {"name": "Fifth House", "theme": "Creativity, Romance"},
    6: {"name": "Sixth House", "theme": "Health, Work, Service"},
    7: {"name": "Seventh House", "theme": "Partnerships, Marriage"},
    8: {"name": "Eighth House", "theme": "Transformation"},
    9: {"name": "Ninth House", "theme": "Philosophy, Travel"},
    10: {"name": "Tenth House", "theme": "Career, Public Image"},
    11: {"name": "Eleventh House", "theme": "Friends, Groups"},
    12: {"name": "Twelfth House", "theme": "Subconscious, Spirituality"}
}


@dataclass
class BirthData:
    name: str
    birth_date: datetime
    latitude: float
    longitude: float
    timezone_str: str
    
    def get_unique_hash(self) -> str:
        data = f"{self.birth_date.isoformat()}|{self.latitude:.6f}|{self.longitude:.6f}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class PlanetaryPosition:
    planet: Planet
    longitude: float
    sign: ZodiacSign
    sign_degree: float
    retrograde: bool
    house: int = 0
    
    @property
    def formatted_position(self) -> str:
        deg = int(self.sign_degree)
        mins = int((self.sign_degree - deg) * 60)
        r = " R" if self.retrograde else ""
        return f"{deg} deg {mins}' {self.sign.name_str}{r}"


@dataclass
class Aspect:
    planet1: Planet
    planet2: Planet
    aspect_type: AspectType
    orb: float
    
    @property
    def strength(self) -> str:
        if self.orb <= 1: return "Exact"
        elif self.orb <= 3: return "Strong"
        elif self.orb <= 5: return "Moderate"
        return "Weak"


@dataclass
class HouseCusp:
    house_number: int
    longitude: float
    sign: ZodiacSign
    sign_degree: float


@dataclass
class NatalChart:
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
            "birth_data": {"name": self.birth_data.name, "birth_date": self.birth_data.birth_date.isoformat()},
            "chart_hash": self.chart_hash,
            "sun_sign": self.sun_sign.name_str,
            "moon_sign": self.moon_sign.name_str,
            "rising_sign": self.rising_sign.name_str,
            "planets": {p.planet.value: {"sign": p.sign.name_str, "degree": round(p.sign_degree, 2), "house": p.house} for p in self.planets.values()},
            "aspects": [{"p1": a.planet1.value, "p2": a.planet2.value, "type": a.aspect_type.value[0], "orb": round(a.orb, 2)} for a in self.aspects]
        }


def get_zodiac_sign(lon: float) -> ZodiacSign:
    return list(ZodiacSign)[int(lon / 30) % 12]

def get_sign_degree(lon: float) -> float:
    return lon % 30

def normalize(angle: float) -> float:
    while angle < 0: angle += 360
    while angle >= 360: angle -= 360
    return angle

def julian_day(dt: datetime) -> float:
    y, m = dt.year, dt.month
    d = dt.day + dt.hour/24 + dt.minute/1440
    if m <= 2: y, m = y-1, m+12
    A = int(y/100)
    B = 2 - A + int(A/4)
    return int(365.25*(y+4716)) + int(30.6001*(m+1)) + d + B - 1524.5

def calc_sun(jd: float) -> float:
    T = (jd - 2451545.0) / 36525.0
    L0 = normalize(280.46646 + 36000.76983*T)
    M = math.radians(normalize(357.52911 + 35999.05029*T))
    C = (1.914602 - 0.004817*T)*math.sin(M) + 0.019993*math.sin(2*M)
    return normalize(L0 + C)

def calc_moon(jd: float) -> float:
    T = (jd - 2451545.0) / 36525.0
    L = 218.3164477 + 481267.88123421*T
    M = 134.9633964 + 477198.8675055*T
    D = 297.8501921 + 445267.1114034*T
    lon = L + 6.289*math.sin(math.radians(M)) + 1.274*math.sin(math.radians(2*D-M))
    return normalize(lon)

def calc_planet(jd: float, planet: Planet) -> Tuple[float, bool]:
    T = (jd - 2451545.0) / 36525.0
    elems = {
        Planet.MERCURY: (252.25, 149472.67, 0.387), Planet.VENUS: (181.98, 58517.82, 0.723),
        Planet.MARS: (355.43, 19140.30, 1.524), Planet.JUPITER: (34.35, 3034.91, 5.203),
        Planet.SATURN: (50.08, 1222.11, 9.555), Planet.URANUS: (314.06, 428.47, 19.22),
        Planet.NEPTUNE: (304.35, 218.49, 30.11), Planet.PLUTO: (238.93, 145.21, 39.48)
    }
    if planet not in elems: return 0, False
    L0, Ldot, a = elems[planet]
    lon = normalize(L0 + Ldot*T)
    sun = calc_sun(jd)
    diff = normalize(lon - sun)
    retro = (150 < diff < 210) if a > 1 else (90 < diff < 270)
    return lon, retro

def calc_node(jd: float) -> float:
    T = (jd - 2451545.0) / 36525.0
    return normalize(125.04452 - 1934.136261*T)

def calc_asc(jd: float, lat: float, lon: float) -> float:
    T = (jd - 2451545.0) / 36525.0
    theta = normalize(280.46061837 + 360.98564736629*(jd-2451545.0) + lon)
    eps = math.radians(23.4393 - 0.0130*T)
    lat_r, lst_r = math.radians(lat), math.radians(theta)
    y = -math.cos(lst_r)
    x = math.sin(lst_r)*math.cos(eps) + math.tan(lat_r)*math.sin(eps)
    return normalize(math.degrees(math.atan2(y, x)) + 180)


class AstrologyEngine:
    def calculate_chart(self, bd: BirthData) -> NatalChart:
        jd = julian_day(bd.birth_date)
        planets = {}
        
        sun = calc_sun(jd)
        planets[Planet.SUN] = PlanetaryPosition(Planet.SUN, sun, get_zodiac_sign(sun), get_sign_degree(sun), False)
        
        moon = calc_moon(jd)
        planets[Planet.MOON] = PlanetaryPosition(Planet.MOON, moon, get_zodiac_sign(moon), get_sign_degree(moon), False)
        
        for p in [Planet.MERCURY, Planet.VENUS, Planet.MARS, Planet.JUPITER, Planet.SATURN, Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO]:
            lon, retro = calc_planet(jd, p)
            planets[p] = PlanetaryPosition(p, lon, get_zodiac_sign(lon), get_sign_degree(lon), retro)
        
        nn = calc_node(jd)
        planets[Planet.NORTH_NODE] = PlanetaryPosition(Planet.NORTH_NODE, nn, get_zodiac_sign(nn), get_sign_degree(nn), True)
        
        asc = calc_asc(jd, bd.latitude, bd.longitude)
        houses = [HouseCusp(i+1, normalize(asc+i*30), get_zodiac_sign(normalize(asc+i*30)), get_sign_degree(normalize(asc+i*30))) for i in range(12)]
        
        for p in planets.values():
            for i in range(12):
                c1, c2 = houses[i].longitude, houses[(i+1)%12].longitude
                if c1 > c2:
                    if p.longitude >= c1 or p.longitude < c2: p.house = i+1; break
                elif c1 <= p.longitude < c2: p.house = i+1; break
        
        aspects = []
        plist = list(planets.values())
        for i, p1 in enumerate(plist):
            for p2 in plist[i+1:]:
                ang = abs(p1.longitude - p2.longitude)
                if ang > 180: ang = 360 - ang
                for at in AspectType:
                    if abs(ang - at.value[1]) <= at.value[2]:
                        aspects.append(Aspect(p1.planet, p2.planet, at, abs(ang - at.value[1])))
                        break
        aspects.sort(key=lambda a: a.orb)
        
        return NatalChart(bd, planets, houses, aspects, asc, normalize(asc+270), bd.get_unique_hash())


class InterpretationEngine:
    def __init__(self):
        self.sun_interpretations = {s: {"title": f"The {s.name_str}", "core_identity": f"With Sun in {s.name_str}, you embody {s.element.lower()} energy.", "strengths": ["Leadership", "Creativity"], "challenges": ["Balance", "Patience"], "life_purpose": f"Express your {s.name_str} nature."} for s in ZodiacSign}
    
    def get_sun_interpretation(self, sign): return self.sun_interpretations.get(sign, {})
    def get_moon_interpretation(self, sign): return {"emotional_nature": f"Moon in {sign.name_str} shapes your emotions.", "needs": f"You need {sign.element.lower()} experiences.", "nurturing_style": f"You nurture through {sign.name_str} qualities."}


def create_chart(name: str, birth_date: datetime, latitude: float, longitude: float, timezone_str: str = "UTC") -> NatalChart:
    return AstrologyEngine().calculate_chart(BirthData(name, birth_date, latitude, longitude, timezone_str))

def chart_to_json(chart: NatalChart) -> str:
    return json.dumps(chart.to_dict(), indent=2)


if __name__ == "__main__":
    chart = create_chart("Isabella Moonrose", datetime(1992, 7, 22, 9, 45), 48.8566, 2.3522, "Europe/Paris")
    print(f"Chart: {chart.birth_data.name}")
    print(f"Sun: {chart.sun_sign.name_str} | Moon: {chart.moon_sign.name_str} | Rising: {chart.rising_sign.name_str}")
    print(f"Hash: {chart.chart_hash}")

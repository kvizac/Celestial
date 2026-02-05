"""
Celestial Insights - Standalone PDF Report Generator
=====================================================
Generates beautiful PDF astrology reports.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.graphics.shapes import Drawing, Circle, Line, String
import math
from datetime import datetime

from astro_standalone import NatalChart, Planet, ZodiacSign, HOUSE_MEANINGS, InterpretationEngine


class Colors:
    GOLD = colors.Color(0.83, 0.68, 0.21)
    GOLD_LIGHT = colors.Color(0.96, 0.89, 0.74)
    DEEP_SPACE = colors.Color(0.06, 0.06, 0.10)
    MIDNIGHT = colors.Color(0.12, 0.12, 0.20)
    COSMIC_BLUE = colors.Color(0.15, 0.18, 0.30)
    STAR_WHITE = colors.Color(0.97, 0.96, 1.0)
    PURPLE = colors.Color(0.40, 0.20, 0.60)


def get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('Title1', fontName='Helvetica-Bold', fontSize=26, textColor=Colors.GOLD, alignment=TA_CENTER, spaceAfter=20, spaceBefore=20))
    styles.add(ParagraphStyle('Subtitle', fontName='Helvetica-Oblique', fontSize=13, textColor=Colors.GOLD_LIGHT, alignment=TA_CENTER, spaceAfter=25))
    styles.add(ParagraphStyle('Section', fontName='Helvetica-Bold', fontSize=16, textColor=Colors.GOLD, alignment=TA_LEFT, spaceBefore=20, spaceAfter=12))
    styles.add(ParagraphStyle('Body', fontName='Helvetica', fontSize=11, textColor=colors.black, alignment=TA_JUSTIFY, spaceBefore=6, spaceAfter=6, leading=16, firstLineIndent=18))
    styles.add(ParagraphStyle('Highlight', fontName='Helvetica-Oblique', fontSize=11, textColor=Colors.PURPLE, alignment=TA_CENTER, spaceBefore=12, spaceAfter=12, leftIndent=25, rightIndent=25))
    styles.add(ParagraphStyle('Info', fontName='Helvetica', fontSize=9, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=8))
    return styles


def draw_chart_wheel(chart: NatalChart, size: int = 320) -> Drawing:
    d = Drawing(size, size)
    cx, cy = size/2, size/2
    r1, r2, r3 = size*0.44, size*0.34, size*0.24
    
    d.add(Circle(cx, cy, r1, fillColor=Colors.COSMIC_BLUE, strokeColor=Colors.GOLD, strokeWidth=2))
    d.add(Circle(cx, cy, r2, fillColor=Colors.MIDNIGHT, strokeColor=Colors.GOLD, strokeWidth=1))
    d.add(Circle(cx, cy, r3, fillColor=Colors.DEEP_SPACE, strokeColor=Colors.GOLD, strokeWidth=1))
    d.add(Circle(cx, cy, size*0.06, fillColor=Colors.GOLD))
    
    signs = ['Ari','Tau','Gem','Can','Leo','Vir','Lib','Sco','Sag','Cap','Aqu','Pis']
    for i in range(12):
        a = math.radians(i*30-90)
        d.add(Line(cx+r3*math.cos(a), cy+r3*math.sin(a), cx+r1*math.cos(a), cy+r1*math.sin(a), strokeColor=Colors.GOLD, strokeWidth=0.5))
        sa = math.radians(i*30+15-90)
        sr = (r1+r2)/2
        d.add(String(cx+sr*math.cos(sa)-8, cy+sr*math.sin(sa)-4, signs[i], fontName='Helvetica', fontSize=8, fillColor=Colors.GOLD_LIGHT))
    
    abbr = {Planet.SUN:'Su', Planet.MOON:'Mo', Planet.MERCURY:'Me', Planet.VENUS:'Ve', Planet.MARS:'Ma', Planet.JUPITER:'Ju', Planet.SATURN:'Sa', Planet.URANUS:'Ur', Planet.NEPTUNE:'Ne', Planet.PLUTO:'Pl', Planet.NORTH_NODE:'NN'}
    for p, pos in chart.planets.items():
        if p in abbr:
            a = math.radians(360-pos.longitude-90)
            pr = (r3+r2)/2
            px, py = cx+pr*math.cos(a)-7, cy+pr*math.sin(a)-4
            d.add(Circle(px+7, py+4, 9, fillColor=Colors.MIDNIGHT, strokeColor=Colors.GOLD, strokeWidth=1))
            d.add(String(px+2, py, abbr[p], fontName='Helvetica-Bold', fontSize=7, fillColor=Colors.GOLD_LIGHT))
    return d


class ReportGenerator:
    def __init__(self, chart: NatalChart):
        self.chart = chart
        self.styles = get_styles()
        self.interp = InterpretationEngine()
    
    def generate(self, path: str):
        doc = SimpleDocTemplate(path, pagesize=letter, rightMargin=0.7*inch, leftMargin=0.7*inch, topMargin=0.7*inch, bottomMargin=0.7*inch)
        story = []
        
        # Cover
        story.extend(self._cover())
        story.append(PageBreak())
        
        # Table of Contents
        story.extend(self._toc())
        story.append(PageBreak())
        
        # Overview
        story.extend(self._overview())
        story.append(PageBreak())
        
        # Chart
        story.extend(self._chart_page())
        story.append(PageBreak())
        
        # Sun Sign
        story.extend(self._sun_section())
        story.append(PageBreak())
        
        # Moon Sign
        story.extend(self._moon_section())
        story.append(PageBreak())
        
        # Rising Sign
        story.extend(self._rising_section())
        story.append(PageBreak())
        
        # Planets
        story.extend(self._planets_section())
        story.append(PageBreak())
        
        # Houses
        story.extend(self._houses_section())
        story.append(PageBreak())
        
        # Aspects
        story.extend(self._aspects_section())
        story.append(PageBreak())
        
        # Guidance
        story.extend(self._guidance())
        story.append(PageBreak())
        
        # Appendix
        story.extend(self._appendix())
        
        doc.build(story, onFirstPage=self._deco, onLaterPages=self._deco)
    
    def _deco(self, c, doc):
        c.saveState()
        c.setStrokeColor(Colors.GOLD)
        c.setLineWidth(0.5)
        c.rect(0.4*inch, 0.4*inch, letter[0]-0.8*inch, letter[1]-0.8*inch)
        c.setFont('Helvetica', 8)
        c.setFillColor(colors.grey)
        c.drawCentredString(letter[0]/2, 0.28*inch, f"Celestial Insights | {datetime.now().strftime('%B %d, %Y')}")
        c.drawRightString(letter[0]-0.6*inch, 0.28*inch, f"Page {c.getPageNumber()}")
        c.restoreState()
    
    def _cover(self):
        e = []
        e.append(Spacer(1, 1.8*inch))
        e.append(Paragraph("CELESTIAL INSIGHTS", self.styles['Title1']))
        e.append(Paragraph("A Personal Journey Through Your Stars", self.styles['Subtitle']))
        e.append(Spacer(1, 0.8*inch))
        e.append(Paragraph("Prepared Exclusively For", self.styles['Info']))
        e.append(Paragraph(f"<b>{self.chart.birth_data.name}</b>", self.styles['Title1']))
        e.append(Spacer(1, 0.4*inch))
        bd = self.chart.birth_data
        e.append(Paragraph(f"Born: {bd.birth_date.strftime('%B %d, %Y at %I:%M %p')}<br/>Location: {bd.latitude:.2f}, {bd.longitude:.2f}<br/>Chart ID: {self.chart.chart_hash}", self.styles['Info']))
        e.append(Spacer(1, 0.8*inch))
        e.append(Paragraph(f"Sun in {self.chart.sun_sign.name_str} | Moon in {self.chart.moon_sign.name_str} | {self.chart.rising_sign.name_str} Rising", self.styles['Highlight']))
        return e
    
    def _toc(self):
        e = [Paragraph("Table of Contents", self.styles['Section']), Spacer(1, 0.2*inch)]
        items = [("1. Your Cosmic Overview", "3"), ("2. Your Natal Chart", "4"), ("3. The Sun: Core Identity", "5"), ("4. The Moon: Emotional Self", "6"), ("5. Rising Sign: Outer Self", "7"), ("6. Planetary Positions", "8"), ("7. The Twelve Houses", "9"), ("8. Planetary Aspects", "10"), ("9. Life Guidance", "11"), ("10. Appendix", "12")]
        for t, p in items:
            e.append(Paragraph(f"{t} {'.'*50} {p}", self.styles['Body']))
        return e
    
    def _overview(self):
        e = [Paragraph("Your Cosmic Overview", self.styles['Section'])]
        e.append(Paragraph(f"Welcome to your personalized astrological report, {self.chart.birth_data.name}. This document represents a detailed analysis of the celestial configuration at the exact moment of your birth - a cosmic snapshot revealing the energies, potentials, and life themes woven into your being.", self.styles['Body']))
        e.append(Paragraph("Astrology is not about fate or fortune-telling. It is a symbolic language that helps us understand ourselves more deeply. Your natal chart is a map - it shows the terrain of your psyche, but you choose which paths to walk.", self.styles['Body']))
        e.append(Spacer(1, 0.2*inch))
        
        data = [['Placement', 'Sign', 'Element', 'Quality'],
                ['Sun (Identity)', self.chart.sun_sign.name_str, self.chart.sun_sign.element, self.chart.sun_sign.modality],
                ['Moon (Emotions)', self.chart.moon_sign.name_str, self.chart.moon_sign.element, self.chart.moon_sign.modality],
                ['Rising (Persona)', self.chart.rising_sign.name_str, self.chart.rising_sign.element, self.chart.rising_sign.modality]]
        
        t = Table(data, colWidths=[1.6*inch, 1.2*inch, 0.9*inch, 0.9*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), Colors.GOLD), ('TEXTCOLOR', (0,0), (-1,0), Colors.DEEP_SPACE),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10), ('BACKGROUND', (0,1), (-1,-1), Colors.STAR_WHITE),
            ('GRID', (0,0), (-1,-1), 1, Colors.GOLD), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6)
        ]))
        e.append(t)
        
        elem_cnt = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
        for p in self.chart.planets.values(): elem_cnt[p.sign.element] += 1
        dom = max(elem_cnt, key=elem_cnt.get)
        e.append(Spacer(1, 0.2*inch))
        e.append(Paragraph(f"<b>Your Elemental Balance:</b> Fire ({elem_cnt['Fire']}), Earth ({elem_cnt['Earth']}), Air ({elem_cnt['Air']}), Water ({elem_cnt['Water']}). Your dominant element is {dom}.", self.styles['Body']))
        return e
    
    def _chart_page(self):
        e = [Paragraph("Your Natal Chart", self.styles['Section'])]
        e.append(Paragraph("Below is a visual representation of your natal chart - a map of the heavens at the moment of your birth. The outer ring shows the twelve zodiac signs, the middle contains the planets, and the inner wheel shows the twelve houses.", self.styles['Body']))
        e.append(Spacer(1, 0.2*inch))
        e.append(draw_chart_wheel(self.chart))
        e.append(Spacer(1, 0.2*inch))
        e.append(Paragraph("The Ascendant (Rising Sign) is at the 9 o'clock position, marking the eastern horizon at your birth. Planets are placed according to their zodiac positions.", self.styles['Body']))
        return e
    
    def _sun_section(self):
        e = []
        sun = self.chart.planets[Planet.SUN]
        data = self.interp.get_sun_interpretation(self.chart.sun_sign)
        
        e.append(Paragraph(f"The Sun in {self.chart.sun_sign.name_str}: Your Core Self", self.styles['Section']))
        e.append(Paragraph(f"<i>Sun at {sun.formatted_position} in House {sun.house}</i>", self.styles['Info']))
        
        e.append(Paragraph("<b>Your Core Identity</b>", self.styles['Body']))
        e.append(Paragraph(f"With your Sun in {self.chart.sun_sign.name_str}, you express yourself through {self.chart.sun_sign.element.lower()} energy. The Sun represents your essential self, your ego, and your life purpose. It's the core of who you are and what you're here to become.", self.styles['Body']))
        e.append(Paragraph(f"As a {self.chart.sun_sign.modality.lower()} {self.chart.sun_sign.element.lower()} sign, you approach life with a particular style. You are driven by the qualities that define {self.chart.sun_sign.name_str} - whether that's pioneering courage, steadfast determination, curious adaptability, or deep emotional wisdom.", self.styles['Body']))
        
        e.append(Spacer(1, 0.15*inch))
        e.append(Paragraph("<b>Natural Strengths</b>", self.styles['Body']))
        for s in ["Self-expression and creativity", "Natural confidence", f"{self.chart.sun_sign.element} element qualities", "Life purpose clarity"]:
            e.append(Paragraph(f"* {s}", self.styles['Body']))
        
        e.append(Spacer(1, 0.15*inch))
        e.append(Paragraph("<b>Life Purpose</b>", self.styles['Body']))
        e.append(Paragraph(f"Your purpose involves expressing your authentic {self.chart.sun_sign.name_str} nature and bringing its gifts to the world.", self.styles['Highlight']))
        return e
    
    def _moon_section(self):
        e = []
        moon = self.chart.planets[Planet.MOON]
        
        e.append(Paragraph(f"The Moon in {self.chart.moon_sign.name_str}: Your Emotional Self", self.styles['Section']))
        e.append(Paragraph(f"<i>Moon at {moon.formatted_position} in House {moon.house}</i>", self.styles['Info']))
        
        e.append(Paragraph("While your Sun represents your conscious identity, your Moon reveals your emotional nature, instinctive reactions, and deepest needs. The Moon governs your inner world - how you feel, what makes you feel secure, and how you nurture yourself and others.", self.styles['Body']))
        
        e.append(Paragraph("<b>Your Emotional Nature</b>", self.styles['Body']))
        e.append(Paragraph(f"With your Moon in {self.chart.moon_sign.name_str}, your emotional responses are colored by {self.chart.moon_sign.element.lower()} energy. You process feelings through the lens of this sign, seeking emotional fulfillment in ways that align with its qualities.", self.styles['Body']))
        
        e.append(Paragraph("<b>What You Need</b>", self.styles['Body']))
        e.append(Paragraph(f"To feel emotionally secure, you need experiences and environments that honor your Moon sign's nature. This might mean seeking {self.chart.moon_sign.element.lower()} experiences, surrounding yourself with people who understand your emotional style, and creating spaces where your true feelings can be expressed.", self.styles['Body']))
        return e
    
    def _rising_section(self):
        e = []
        e.append(Paragraph(f"{self.chart.rising_sign.name_str} Rising: Your Outer Self", self.styles['Section']))
        e.append(Paragraph(f"<i>Ascendant at {self.chart.ascendant:.1f} degrees</i>", self.styles['Info']))
        
        e.append(Paragraph(f"Your Rising Sign, or Ascendant, is {self.chart.rising_sign.name_str}. This is the mask you wear when meeting the world, your automatic first response to new situations, and how others perceive you before they know you more deeply.", self.styles['Body']))
        e.append(Paragraph(f"With {self.chart.rising_sign.name_str} Rising, you approach life with {self.chart.rising_sign.element.lower()} energy on the surface. First impressions of you often include {self.chart.rising_sign.name_str}'s characteristic traits, even if your Sun or Moon suggest different internal realities.", self.styles['Body']))
        e.append(Paragraph("The Rising Sign also determines your house cusps, coloring all twelve areas of life with its energy. It's the lens through which you filter all experiences.", self.styles['Body']))
        return e
    
    def _planets_section(self):
        e = [Paragraph("Your Planetary Positions", self.styles['Section'])]
        e.append(Paragraph("Each planet represents a different facet of your personality. Their signs show how these energies express, while house placements reveal where they are most active.", self.styles['Body']))
        e.append(Spacer(1, 0.15*inch))
        
        data = [['Planet', 'Sign', 'House', 'Retrograde']]
        for p, pos in self.chart.planets.items():
            data.append([p.value, pos.sign.name_str, str(pos.house), "Yes" if pos.retrograde else "No"])
        
        t = Table(data, colWidths=[1.4*inch, 1.3*inch, 0.7*inch, 0.9*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), Colors.GOLD), ('TEXTCOLOR', (0,0), (-1,0), Colors.DEEP_SPACE),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9), ('BACKGROUND', (0,1), (-1,-1), Colors.STAR_WHITE),
            ('GRID', (0,0), (-1,-1), 0.5, Colors.GOLD), ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4)
        ]))
        e.append(t)
        return e
    
    def _houses_section(self):
        e = [Paragraph("The Twelve Houses", self.styles['Section'])]
        e.append(Paragraph("The houses represent different areas of life. Each cusp falls in a zodiac sign, coloring how you experience that domain.", self.styles['Body']))
        e.append(Spacer(1, 0.1*inch))
        
        for h in self.chart.houses:
            info = HOUSE_MEANINGS[h.house_number]
            planets_here = [p.planet.value for p in self.chart.planets.values() if p.house == h.house_number]
            txt = f"<b>House {h.house_number}</b> ({info['theme']}): Cusp in {h.sign.name_str}."
            if planets_here: txt += f" Contains: {', '.join(planets_here)}."
            e.append(Paragraph(txt, self.styles['Body']))
        return e
    
    def _aspects_section(self):
        e = [Paragraph("Planetary Aspects", self.styles['Section'])]
        e.append(Paragraph("Aspects are geometric angles between planets revealing how different parts of your psyche interact. Harmonious aspects indicate natural talents; challenging aspects point to growth areas.", self.styles['Body']))
        e.append(Spacer(1, 0.1*inch))
        
        data = [['Aspect', 'Type', 'Orb', 'Strength']]
        for a in self.chart.aspects[:12]:
            data.append([f"{a.planet1.value} - {a.planet2.value}", a.aspect_type.value[0], f"{a.orb:.1f} deg", a.strength])
        
        if len(data) > 1:
            t = Table(data, colWidths=[2.2*inch, 1.1*inch, 0.8*inch, 0.8*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), Colors.GOLD), ('TEXTCOLOR', (0,0), (-1,0), Colors.DEEP_SPACE),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9), ('BACKGROUND', (0,1), (-1,-1), Colors.STAR_WHITE),
                ('GRID', (0,0), (-1,-1), 0.5, Colors.GOLD)
            ]))
            e.append(t)
        return e
    
    def _guidance(self):
        e = [Paragraph("Life Guidance and Purpose", self.styles['Section'])]
        
        e.append(Paragraph(f"Based on your complete natal chart, here are key themes for your life journey:", self.styles['Body']))
        
        e.append(Paragraph("<b>Your Core Purpose</b>", self.styles['Body']))
        e.append(Paragraph(f"With your Sun in {self.chart.sun_sign.name_str} and Rising in {self.chart.rising_sign.name_str}, your life purpose involves expressing {self.chart.sun_sign.element.lower()} energy through the lens of {self.chart.rising_sign.name_str}'s approach to life.", self.styles['Body']))
        
        e.append(Paragraph("<b>Emotional Fulfillment</b>", self.styles['Body']))
        e.append(Paragraph(f"Your Moon in {self.chart.moon_sign.name_str} reveals that emotional fulfillment comes through {self.chart.moon_sign.element.lower()} experiences. Honor your need for what this sign represents.", self.styles['Body']))
        
        e.append(Paragraph("<b>Key Life Themes</b>", self.styles['Body']))
        e.append(Paragraph("The houses containing the most planets indicate areas of concentrated life focus. Pay special attention to these domains as they represent where much of your growth will occur.", self.styles['Body']))
        
        e.append(Spacer(1, 0.2*inch))
        e.append(Paragraph("The stars incline, but do not compel. You have the power to work with your cosmic blueprint in whatever way serves your highest good.", self.styles['Highlight']))
        return e
    
    def _appendix(self):
        e = [Paragraph("Appendix: Technical Details", self.styles['Section'])]
        bd = self.chart.birth_data
        e.append(Paragraph(f"Name: {bd.name}<br/>Birth: {bd.birth_date.strftime('%Y-%m-%d %H:%M')}<br/>Location: {bd.latitude:.4f}, {bd.longitude:.4f}<br/>Timezone: {bd.timezone_str}<br/>House System: Equal<br/>Chart Hash: {self.chart.chart_hash}<br/>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['Info']))
        
        e.append(Spacer(1, 0.2*inch))
        e.append(Paragraph("<b>Disclaimer</b>", self.styles['Body']))
        e.append(Paragraph("This astrological report is for entertainment and self-reflection purposes. Astrology should not substitute professional medical, psychological, financial, or legal advice. Individual experiences may vary.", self.styles['Body']))
        
        e.append(Spacer(1, 0.3*inch))
        e.append(Paragraph("Thank you for choosing Celestial Insights. May the stars guide your journey.", self.styles['Highlight']))
        return e


def generate_report(chart: NatalChart, path: str):
    ReportGenerator(chart).generate(path)
    print(f"Report generated: {path}")


if __name__ == "__main__":
    from astro_standalone import create_chart
    chart = create_chart("Isabella Moonrose", datetime(1992, 7, 22, 9, 45), 48.8566, 2.3522, "Europe/Paris")
    generate_report(chart, "/home/claude/celestial-insights/sample_report.pdf")

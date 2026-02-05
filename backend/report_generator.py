"""
Celestial Insights - PDF Report Generator
==========================================
Generates beautiful, personalized astrology reports with star maps.

Requirements:
    pip install reportlab
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

# Import astrology engine
from astro_engine import (
    NatalChart, Planet, ZodiacSign, AspectType, 
    InterpretationEngine, HOUSE_MEANINGS
)


class Colors:
    GOLD = colors.Color(0.83, 0.68, 0.21)
    GOLD_LIGHT = colors.Color(0.96, 0.89, 0.74)
    DEEP_SPACE = colors.Color(0.06, 0.06, 0.10)
    MIDNIGHT = colors.Color(0.08, 0.08, 0.15)
    COSMIC_BLUE = colors.Color(0.09, 0.13, 0.24)
    STAR_WHITE = colors.Color(0.97, 0.96, 1.0)
    NEBULA_PURPLE = colors.Color(0.40, 0.20, 0.60)


def get_custom_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='CelestialTitle',
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=Colors.GOLD,
        alignment=TA_CENTER,
        spaceAfter=20,
        spaceBefore=20
    ))
    
    styles.add(ParagraphStyle(
        name='CelestialSubtitle',
        fontName='Helvetica-Oblique',
        fontSize=14,
        textColor=Colors.GOLD_LIGHT,
        alignment=TA_CENTER,
        spaceAfter=30
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=Colors.GOLD,
        alignment=TA_LEFT,
        spaceBefore=25,
        spaceAfter=15
    ))
    
    styles.add(ParagraphStyle(
        name='BodyText',
        fontName='Helvetica',
        fontSize=11,
        textColor=colors.black,
        alignment=TA_JUSTIFY,
        spaceBefore=6,
        spaceAfter=6,
        leading=16,
        firstLineIndent=20
    ))
    
    styles.add(ParagraphStyle(
        name='Highlight',
        fontName='Helvetica-Oblique',
        fontSize=12,
        textColor=Colors.NEBULA_PURPLE,
        alignment=TA_CENTER,
        spaceBefore=15,
        spaceAfter=15,
        leftIndent=30,
        rightIndent=30
    ))
    
    styles.add(ParagraphStyle(
        name='InfoText',
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=10
    ))
    
    return styles


def create_natal_chart_wheel(chart: NatalChart, size: int = 350) -> Drawing:
    d = Drawing(size, size)
    cx, cy = size / 2, size / 2
    
    outer_r = size * 0.45
    middle_r = size * 0.35
    inner_r = size * 0.25
    center_r = size * 0.08
    
    d.add(Circle(cx, cy, outer_r, fillColor=Colors.COSMIC_BLUE, strokeColor=Colors.GOLD, strokeWidth=2))
    d.add(Circle(cx, cy, middle_r, fillColor=Colors.MIDNIGHT, strokeColor=Colors.GOLD, strokeWidth=1))
    d.add(Circle(cx, cy, inner_r, fillColor=Colors.DEEP_SPACE, strokeColor=Colors.GOLD, strokeWidth=1))
    d.add(Circle(cx, cy, center_r, fillColor=Colors.GOLD, strokeColor=Colors.GOLD_LIGHT, strokeWidth=1))
    
    symbols = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
    
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        x1 = cx + inner_r * math.cos(angle)
        y1 = cy + inner_r * math.sin(angle)
        x2 = cx + outer_r * math.cos(angle)
        y2 = cy + outer_r * math.sin(angle)
        d.add(Line(x1, y1, x2, y2, strokeColor=Colors.GOLD, strokeWidth=0.5))
        
        sym_angle = math.radians((i * 30) + 15 - 90)
        sym_r = (outer_r + middle_r) / 2
        sx = cx + sym_r * math.cos(sym_angle) - 10
        sy = cy + sym_r * math.sin(sym_angle) - 4
        d.add(String(sx, sy, symbols[i], fontName='Helvetica', fontSize=8, fillColor=Colors.GOLD_LIGHT))
    
    planet_abbr = {
        Planet.SUN: 'Su', Planet.MOON: 'Mo', Planet.MERCURY: 'Me',
        Planet.VENUS: 'Ve', Planet.MARS: 'Ma', Planet.JUPITER: 'Ju',
        Planet.SATURN: 'Sa', Planet.URANUS: 'Ur', Planet.NEPTUNE: 'Ne',
        Planet.PLUTO: 'Pl', Planet.NORTH_NODE: 'NN'
    }
    
    for planet, pos in chart.planets.items():
        if planet in planet_abbr:
            angle = math.radians(360 - pos.longitude - 90)
            pr = (inner_r + middle_r) / 2
            px = cx + pr * math.cos(angle) - 8
            py = cy + pr * math.sin(angle) - 4
            d.add(Circle(px + 8, py + 4, 10, fillColor=Colors.MIDNIGHT, strokeColor=Colors.GOLD, strokeWidth=1))
            d.add(String(px + 2, py, planet_abbr[planet], fontName='Helvetica-Bold', fontSize=7, fillColor=Colors.GOLD_LIGHT))
    
    return d


class ReportGenerator:
    def __init__(self, chart: NatalChart, language: str = 'en'):
        self.chart = chart
        self.language = language
        self.styles = get_custom_styles()
        self.interpreter = InterpretationEngine()
    
    def generate(self, output_path: str):
        doc = SimpleDocTemplate(
            output_path, pagesize=letter,
            rightMargin=0.75*inch, leftMargin=0.75*inch,
            topMargin=0.75*inch, bottomMargin=0.75*inch
        )
        
        story = []
        story.extend(self._cover_page())
        story.append(PageBreak())
        story.extend(self._overview())
        story.append(PageBreak())
        story.extend(self._chart_section())
        story.append(PageBreak())
        story.extend(self._sun_section())
        story.append(PageBreak())
        story.extend(self._moon_section())
        story.append(PageBreak())
        story.extend(self._rising_section())
        story.append(PageBreak())
        story.extend(self._planets_section())
        story.append(PageBreak())
        story.extend(self._houses_section())
        story.append(PageBreak())
        story.extend(self._aspects_section())
        story.append(PageBreak())
        story.extend(self._guidance_section())
        story.append(PageBreak())
        story.extend(self._appendix())
        
        doc.build(story, onFirstPage=self._page_deco, onLaterPages=self._page_deco)
    
    def _page_deco(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(Colors.GOLD)
        canvas.setLineWidth(0.5)
        canvas.rect(0.5*inch, 0.5*inch, letter[0] - inch, letter[1] - inch)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(letter[0]/2, 0.35*inch, f"Celestial Insights | {datetime.now().strftime('%B %d, %Y')}")
        canvas.drawRightString(letter[0] - 0.75*inch, 0.35*inch, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()
    
    def _cover_page(self):
        elements = []
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph("CELESTIAL INSIGHTS", self.styles['CelestialTitle']))
        elements.append(Paragraph("A Personal Journey Through Your Stars", self.styles['CelestialSubtitle']))
        elements.append(Spacer(1, inch))
        elements.append(Paragraph("Prepared Exclusively For", self.styles['InfoText']))
        elements.append(Paragraph(f"<b>{self.chart.birth_data.name}</b>", self.styles['CelestialTitle']))
        elements.append(Spacer(1, 0.5*inch))
        
        birth_info = f"""
        Born: {self.chart.birth_data.birth_date.strftime('%B %d, %Y at %I:%M %p')}<br/>
        Location: {self.chart.birth_data.latitude:.4f}, {self.chart.birth_data.longitude:.4f}<br/>
        Chart ID: {self.chart.chart_hash}
        """
        elements.append(Paragraph(birth_info, self.styles['InfoText']))
        elements.append(Spacer(1, inch))
        elements.append(Paragraph(
            f"Sun in {self.chart.sun_sign.name_str} | Moon in {self.chart.moon_sign.name_str} | {self.chart.rising_sign.name_str} Rising",
            self.styles['Highlight']
        ))
        return elements
    
    def _overview(self):
        elements = []
        elements.append(Paragraph("Your Cosmic Overview", self.styles['SectionHeader']))
        
        overview = f"""
        Welcome to your personalized astrological report, {self.chart.birth_data.name}. This document 
        represents a detailed analysis of the celestial configuration at the exact moment of your birth.
        
        Astrology is not about fate or fortune-telling. Rather, it is a symbolic language that helps us 
        understand ourselves more deeply. Your natal chart is like a map—it shows the terrain of your 
        psyche, but you choose which paths to walk.
        """
        elements.append(Paragraph(overview, self.styles['BodyText']))
        elements.append(Spacer(1, 0.3*inch))
        
        data = [
            ['Placement', 'Sign', 'Element', 'Quality'],
            ['Sun (Identity)', self.chart.sun_sign.name_str, self.chart.sun_sign.element, self.chart.sun_sign.modality],
            ['Moon (Emotions)', self.chart.moon_sign.name_str, self.chart.moon_sign.element, self.chart.moon_sign.modality],
            ['Rising (Persona)', self.chart.rising_sign.name_str, self.chart.rising_sign.element, self.chart.rising_sign.modality],
        ]
        
        table = Table(data, colWidths=[1.8*inch, 1.3*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Colors.GOLD),
            ('TEXTCOLOR', (0, 0), (-1, 0), Colors.DEEP_SPACE),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, -1), Colors.STAR_WHITE),
            ('GRID', (0, 0), (-1, -1), 1, Colors.GOLD),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        
        return elements
    
    def _chart_section(self):
        elements = []
        elements.append(Paragraph("Your Natal Chart", self.styles['SectionHeader']))
        
        intro = """
        Below is a visual representation of your natal chart—a map of the heavens at the moment of your 
        birth. The outer ring shows the twelve zodiac signs, the middle contains the planets, and 
        the inner wheel shows the twelve houses.
        """
        elements.append(Paragraph(intro, self.styles['BodyText']))
        elements.append(Spacer(1, 0.3*inch))
        
        chart_drawing = create_natal_chart_wheel(self.chart)
        elements.append(chart_drawing)
        
        return elements
    
    def _sun_section(self):
        elements = []
        sun_data = self.interpreter.get_sun_interpretation(self.chart.sun_sign)
        sun_pos = self.chart.planets[Planet.SUN]
        
        elements.append(Paragraph(
            f"The Sun in {self.chart.sun_sign.name_str}: {sun_data.get('title', 'Your Core Self')}",
            self.styles['SectionHeader']
        ))
        elements.append(Paragraph(f"<i>Your Sun at {sun_pos.formatted_position} in House {sun_pos.house}</i>", self.styles['InfoText']))
        
        elements.append(Paragraph("<b>Your Core Identity</b>", self.styles['BodyText']))
        core = sun_data.get('core_identity', f'Your Sun in {self.chart.sun_sign.name_str} represents your essential self.')
        for para in core.strip().split('\n\n'):
            if para.strip():
                elements.append(Paragraph(para.strip(), self.styles['BodyText']))
        
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("<b>Your Natural Strengths</b>", self.styles['BodyText']))
        for s in sun_data.get('strengths', ['Authenticity', 'Self-expression']):
            elements.append(Paragraph(f"* {s}", self.styles['BodyText']))
        
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("<b>Growth Areas</b>", self.styles['BodyText']))
        for c in sun_data.get('challenges', ['Balance', 'Patience']):
            elements.append(Paragraph(f"* {c}", self.styles['BodyText']))
        
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("<b>Life Purpose</b>", self.styles['BodyText']))
        elements.append(Paragraph(sun_data.get('life_purpose', 'Express your authentic self.'), self.styles['Highlight']))
        
        return elements
    
    def _moon_section(self):
        elements = []
        moon_data = self.interpreter.get_moon_interpretation(self.chart.moon_sign)
        moon_pos = self.chart.planets[Planet.MOON]
        
        elements.append(Paragraph(f"The Moon in {self.chart.moon_sign.name_str}: Your Emotional Self", self.styles['SectionHeader']))
        elements.append(Paragraph(f"<i>Your Moon at {moon_pos.formatted_position} in House {moon_pos.house}</i>", self.styles['InfoText']))
        
        intro = """
        While your Sun represents your conscious identity, your Moon reveals your emotional nature, 
        instinctive reactions, and deepest needs. The Moon governs your inner world.
        """
        elements.append(Paragraph(intro, self.styles['BodyText']))
        
        elements.append(Paragraph("<b>Your Emotional Nature</b>", self.styles['BodyText']))
        elements.append(Paragraph(moon_data.get('emotional_nature', ''), self.styles['BodyText']))
        
        elements.append(Paragraph("<b>Your Emotional Needs</b>", self.styles['BodyText']))
        elements.append(Paragraph(moon_data.get('needs', ''), self.styles['BodyText']))
        
        return elements
    
    def _rising_section(self):
        elements = []
        elements.append(Paragraph(f"{self.chart.rising_sign.name_str} Rising: Your Outer Self", self.styles['SectionHeader']))
        elements.append(Paragraph(f"<i>Ascendant at {self.chart.ascendant:.2f} degrees</i>", self.styles['InfoText']))
        
        intro = f"""
        Your Rising Sign, or Ascendant, is {self.chart.rising_sign.name_str}. This is the mask you 
        wear when meeting the world, your automatic first response to new situations, and how 
        others perceive you before they know you more deeply.
        
        With {self.chart.rising_sign.name_str} Rising, you approach life with {self.chart.rising_sign.element.lower()} 
        energy. First impressions of you often include {self.chart.rising_sign.name_str}'s characteristic traits.
        """
        elements.append(Paragraph(intro, self.styles['BodyText']))
        
        return elements
    
    def _planets_section(self):
        elements = []
        elements.append(Paragraph("Your Planetary Positions", self.styles['SectionHeader']))
        
        intro = """
        Each planet represents a different facet of your personality. Their signs show how these 
        energies express themselves, while house placements reveal where they are most active.
        """
        elements.append(Paragraph(intro, self.styles['BodyText']))
        elements.append(Spacer(1, 0.2*inch))
        
        data = [['Planet', 'Position', 'House', 'Retrograde']]
        for planet, pos in self.chart.planets.items():
            retro = "Yes" if pos.retrograde else "No"
            data.append([planet.value, pos.formatted_position, str(pos.house), retro])
        
        table = Table(data, colWidths=[1.5*inch, 2*inch, 0.8*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Colors.GOLD),
            ('TEXTCOLOR', (0, 0), (-1, 0), Colors.DEEP_SPACE),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -1), Colors.STAR_WHITE),
            ('GRID', (0, 0), (-1, -1), 0.5, Colors.GOLD),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table)
        
        return elements
    
    def _houses_section(self):
        elements = []
        elements.append(Paragraph("The Twelve Houses", self.styles['SectionHeader']))
        
        intro = """
        The twelve houses represent different areas of life. Each house cusp falls in a 
        zodiac sign, coloring how you experience that life domain.
        """
        elements.append(Paragraph(intro, self.styles['BodyText']))
        
        for house in self.chart.houses:
            info = HOUSE_MEANINGS[house.house_number]
            planets_here = [p.planet.value for p in self.chart.planets.values() if p.house == house.house_number]
            
            elements.append(Paragraph(f"<b>House {house.house_number}: {info['theme']}</b>", self.styles['BodyText']))
            txt = f"{info['description']} Cusp in {house.sign.name_str}."
            if planets_here:
                txt += f" Contains: {', '.join(planets_here)}."
            elements.append(Paragraph(txt, self.styles['BodyText']))
        
        return elements
    
    def _aspects_section(self):
        elements = []
        elements.append(Paragraph("Planetary Aspects", self.styles['SectionHeader']))
        
        intro = """
        Aspects are geometric angles between planets that reveal how different parts of your psyche 
        interact. Harmonious aspects indicate natural talents; challenging aspects point to growth areas.
        """
        elements.append(Paragraph(intro, self.styles['BodyText']))
        elements.append(Spacer(1, 0.2*inch))
        
        data = [['Aspect', 'Type', 'Orb', 'Strength']]
        for a in self.chart.aspects[:15]:
            data.append([f"{a.planet1.value} - {a.planet2.value}", a.aspect_type.value[0], f"{a.orb:.1f} deg", a.strength])
        
        if len(data) > 1:
            table = Table(data, colWidths=[2.5*inch, 1.2*inch, 0.8*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), Colors.GOLD),
                ('TEXTCOLOR', (0, 0), (-1, 0), Colors.DEEP_SPACE),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 1), (-1, -1), Colors.STAR_WHITE),
                ('GRID', (0, 0), (-1, -1), 0.5, Colors.GOLD),
            ]))
            elements.append(table)
        
        return elements
    
    def _guidance_section(self):
        elements = []
        elements.append(Paragraph("Life Guidance and Purpose", self.styles['SectionHeader']))
        
        guidance = f"""
        Based on your complete natal chart, here are key themes for your life journey:
        
        <b>Your Core Purpose</b>
        With your Sun in {self.chart.sun_sign.name_str} and Rising in {self.chart.rising_sign.name_str}, 
        your life purpose involves expressing {self.chart.sun_sign.element.lower()} energy through the 
        lens of {self.chart.rising_sign.name_str}'s approach to life.
        
        <b>Emotional Fulfillment</b>
        Your Moon in {self.chart.moon_sign.name_str} reveals that emotional fulfillment comes through 
        {self.chart.moon_sign.element.lower()} experiences. Honor your need for what this sign represents.
        
        <b>Key Life Themes</b>
        The houses containing the most planets indicate areas of concentrated life focus. Pay special 
        attention to these domains as they represent where much of your growth will occur.
        """
        elements.append(Paragraph(guidance, self.styles['BodyText']))
        
        elements.append(Paragraph(
            "The stars incline, but do not compel. You have the power to work with your cosmic blueprint in whatever way serves your highest good.",
            self.styles['Highlight']
        ))
        
        return elements
    
    def _appendix(self):
        elements = []
        elements.append(Paragraph("Appendix: Technical Details", self.styles['SectionHeader']))
        
        info = f"""
        Name: {self.chart.birth_data.name}<br/>
        Birth Date: {self.chart.birth_data.birth_date.strftime('%Y-%m-%d %H:%M:%S')}<br/>
        Location: {self.chart.birth_data.latitude:.6f}, {self.chart.birth_data.longitude:.6f}<br/>
        Timezone: {self.chart.birth_data.timezone_str}<br/>
        House System: Placidus<br/>
        Chart Hash: {self.chart.chart_hash}<br/>
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        elements.append(Paragraph(info, self.styles['InfoText']))
        
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("<b>Disclaimer</b>", self.styles['BodyText']))
        
        disclaimer = """
        This astrological report is provided for entertainment and self-reflection purposes. 
        Astrology should not be used as a substitute for professional medical, psychological, 
        financial, or legal advice. Individual experiences may vary.
        """
        elements.append(Paragraph(disclaimer, self.styles['BodyText']))
        
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("Thank you for choosing Celestial Insights. May the stars guide your journey.", self.styles['Highlight']))
        
        return elements


def generate_report(chart: NatalChart, output_path: str, language: str = 'en'):
    generator = ReportGenerator(chart, language)
    generator.generate(output_path)
    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    from astro_engine import create_chart
    from datetime import datetime
    
    birth_dt = datetime(1990, 3, 21, 10, 30)
    chart = create_chart(
        name="Alexandra Starweaver",
        birth_date=birth_dt,
        latitude=51.5074,
        longitude=-0.1278,
        timezone_str="Europe/London"
    )
    generate_report(chart, "sample_astrology_report.pdf")

"""
Celestial Insights - Flask Backend
"""
import os
import json
import stripe
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import hashlib

load_dotenv()

app = Flask(__name__)
CORS(app, origins=['*'])

stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_xxx')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_xxx')
DOMAIN = os.getenv('DOMAIN', 'https://celestial-lemon.vercel.app')
REPORTS_DIR = './generated_reports'
os.makedirs(REPORTS_DIR, exist_ok=True)

PRICES = {
    'essential': {'amount': 2999, 'name': 'Essential Report'},
    'premium': {'amount': 4999, 'name': 'Premium Report'},
    'ultimate': {'amount': 6999, 'name': 'Ultimate Report'}
}

# ============================================
# ASTROLOGY ENGINE (Built-in, no dependencies)
# ============================================
import math

class ZodiacSign:
    SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    ELEMENTS = ['Fire', 'Earth', 'Air', 'Water', 'Fire', 'Earth', 
                'Air', 'Water', 'Fire', 'Earth', 'Air', 'Water']
    
    def __init__(self, index):
        self.index = index % 12
        self.name = self.SIGNS[self.index]
        self.element = self.ELEMENTS[self.index]

def get_sign(longitude):
    return ZodiacSign(int(longitude / 30))

def normalize(angle):
    while angle < 0: angle += 360
    while angle >= 360: angle -= 360
    return angle

def julian_day(dt):
    y, m = dt.year, dt.month
    d = dt.day + dt.hour/24 + dt.minute/1440
    if m <= 2: y, m = y-1, m+12
    A = int(y/100)
    B = 2 - A + int(A/4)
    return int(365.25*(y+4716)) + int(30.6001*(m+1)) + d + B - 1524.5

def calc_sun(jd):
    T = (jd - 2451545.0) / 36525.0
    L0 = normalize(280.46646 + 36000.76983*T)
    M = math.radians(normalize(357.52911 + 35999.05029*T))
    C = (1.914602 - 0.004817*T)*math.sin(M) + 0.019993*math.sin(2*M)
    return normalize(L0 + C)

def calc_moon(jd):
    T = (jd - 2451545.0) / 36525.0
    L = 218.3164477 + 481267.88123421*T
    M = 134.9633964 + 477198.8675055*T
    D = 297.8501921 + 445267.1114034*T
    return normalize(L + 6.289*math.sin(math.radians(M)) + 1.274*math.sin(math.radians(2*D-M)))

def calc_asc(jd, lat, lon):
    T = (jd - 2451545.0) / 36525.0
    theta = normalize(280.46061837 + 360.98564736629*(jd-2451545.0) + lon)
    eps = math.radians(23.4393 - 0.0130*T)
    lat_r, lst_r = math.radians(lat), math.radians(theta)
    y = -math.cos(lst_r)
    x = math.sin(lst_r)*math.cos(eps) + math.tan(lat_r)*math.sin(eps)
    return normalize(math.degrees(math.atan2(y, x)) + 180)

def create_chart(name, birth_date, latitude, longitude, timezone_str='UTC'):
    jd = julian_day(birth_date)
    sun_lon = calc_sun(jd)
    moon_lon = calc_moon(jd)
    asc_lon = calc_asc(jd, latitude, longitude)
    
    data_str = f"{birth_date.isoformat()}|{latitude:.6f}|{longitude:.6f}"
    chart_hash = hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    return {
        'name': name,
        'birth_date': birth_date.isoformat(),
        'latitude': latitude,
        'longitude': longitude,
        'sun_sign': get_sign(sun_lon).name,
        'sun_degree': round(sun_lon % 30, 2),
        'moon_sign': get_sign(moon_lon).name,
        'moon_degree': round(moon_lon % 30, 2),
        'rising_sign': get_sign(asc_lon).name,
        'rising_degree': round(asc_lon % 30, 2),
        'chart_hash': chart_hash
    }

# ============================================
# API ROUTES
# ============================================

@app.route('/')
def home():
    return jsonify({'status': 'online', 'service': 'Celestial Insights API', 'version': '1.0.0'})

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.json
        plan = data.get('plan', 'essential')
        if plan not in PRICES:
            return jsonify({'error': 'Invalid plan'}), 400
        
        price = PRICES[plan]
        metadata = data.get('metadata', {})
        order_id = hashlib.sha256(f"{data.get('customerEmail','')}|{datetime.now().isoformat()}".encode()).hexdigest()[:12].upper()
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': price['amount'],
                    'product_data': {'name': f"Celestial Insights - {price['name']}"},
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{DOMAIN}/cancel',
            customer_email=data.get('customerEmail'),
            metadata={'order_id': order_id, **metadata}
        )
        return jsonify({'id': session.id, 'url': session.url, 'order_id': order_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
        if event['type'] == 'checkout.session.completed':
            print(f"Payment completed: {event['data']['object']['id']}")
        return jsonify({'received': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/preview-chart', methods=['POST'])
def preview_chart():
    try:
        data = request.json
        birth_dt = datetime.strptime(f"{data.get('birthDate', '1990-01-01')} {data.get('birthTime', '12:00')}", "%Y-%m-%d %H:%M")
        chart = create_chart(
            name=data.get('name', 'Preview'),
            birth_date=birth_dt,
            latitude=float(data.get('latitude', 0)),
            longitude=float(data.get('longitude', 0))
        )
        return jsonify({'success': True, 'chart': chart})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

"""
Celestial Insights - Flask Backend with Stripe Integration
==========================================================
Complete backend server handling:
- Stripe payment processing
- Report generation
- Email delivery
- Webhook handling

Requirements:
    pip install flask flask-cors stripe python-dotenv sendgrid
"""

import os
import json
import stripe
from datetime import datetime
from flask import Flask, request, jsonify, send_file, redirect
from flask_cors import CORS
from dotenv import load_dotenv
import hashlib
import hmac

# Load environment variables
load_dotenv()

# Import our modules
from astro_engine import create_chart, chart_to_json
from report_generator import generate_report

# ============================================
# CONFIGURATION
# ============================================

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'https://yourdomain.com'])

# Stripe configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_YOUR_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_YOUR_SECRET')

# Pricing configuration
PRICES = {
    'essential': {
        'price_id': os.getenv('STRIPE_PRICE_ESSENTIAL', 'price_essential'),
        'amount': 2999,  # $29.99 in cents
        'name': 'Essential Report',
        'includes_print': False
    },
    'premium': {
        'price_id': os.getenv('STRIPE_PRICE_PREMIUM', 'price_premium'),
        'amount': 4999,  # $49.99
        'name': 'Premium Report',
        'includes_print': True
    },
    'ultimate': {
        'price_id': os.getenv('STRIPE_PRICE_ULTIMATE', 'price_ultimate'),
        'amount': 6999,  # $69.99
        'name': 'Ultimate Report',
        'includes_print': True,
        'includes_forecast': True
    }
}

# Storage paths
REPORTS_DIR = os.getenv('REPORTS_DIR', './generated_reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# Domain for redirects
DOMAIN = os.getenv('DOMAIN', 'http://localhost:3000')


# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_order_id(email: str, birth_date: str) -> str:
    """Generate unique order ID."""
    data = f"{email}|{birth_date}|{datetime.now().isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()[:12].upper()


def parse_birth_datetime(date_str: str, time_str: str) -> datetime:
    """Parse birth date and time strings into datetime."""
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")


def send_report_email(email: str, name: str, report_path: str):
    """
    Send report via email using SendGrid.
    Implement your email service here.
    """
    # Example with SendGrid (uncomment and configure)
    # from sendgrid import SendGridAPIClient
    # from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType
    # import base64
    #
    # sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    # 
    # with open(report_path, 'rb') as f:
    #     data = base64.b64encode(f.read()).decode()
    # 
    # attachment = Attachment(
    #     FileContent(data),
    #     FileName(f'celestial_insights_{name.replace(" ", "_")}.pdf'),
    #     FileType('application/pdf')
    # )
    # 
    # message = Mail(
    #     from_email='reports@celestialinsights.com',
    #     to_emails=email,
    #     subject=f'Your Celestial Insights Report is Ready, {name}!',
    #     html_content=f'''
    #     <h1>Your Cosmic Journey Begins</h1>
    #     <p>Dear {name},</p>
    #     <p>Your personalized astrology report is attached to this email.</p>
    #     <p>We hope it brings you insight and guidance.</p>
    #     <p>With cosmic wishes,<br>The Celestial Insights Team</p>
    #     '''
    # )
    # message.attachment = attachment
    # sg.send(message)
    
    print(f"[EMAIL] Would send report to {email}: {report_path}")


# ============================================
# API ROUTES
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """
    Create Stripe Checkout session.
    Expects JSON body with: plan, customerEmail, metadata (birth details)
    """
    try:
        data = request.json
        plan = data.get('plan', 'essential')
        
        if plan not in PRICES:
            return jsonify({'error': 'Invalid plan selected'}), 400
        
        price_config = PRICES[plan]
        metadata = data.get('metadata', {})
        
        # Generate order ID
        order_id = generate_order_id(
            data.get('customerEmail', ''),
            metadata.get('birthDate', '')
        )
        
        # Create Stripe Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': price_config['amount'],
                    'product_data': {
                        'name': f'Celestial Insights - {price_config["name"]}',
                        'description': 'Personalized astrology report',
                        'images': ['https://yourdomain.com/images/report-preview.jpg'],
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{DOMAIN}/cancel',
            customer_email=data.get('customerEmail'),
            metadata={
                'order_id': order_id,
                'plan': plan,
                'full_name': metadata.get('fullName', ''),
                'birth_date': metadata.get('birthDate', ''),
                'birth_time': metadata.get('birthTime', ''),
                'birth_place': metadata.get('birthPlace', ''),
                'latitude': metadata.get('latitude', ''),
                'longitude': metadata.get('longitude', ''),
                'timezone': metadata.get('timezone', 'UTC'),
                'language': metadata.get('language', 'en'),
            }
        )
        
        return jsonify({
            'id': session.id,
            'url': session.url,
            'order_id': order_id
        })
        
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/webhook', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhooks for payment completion.
    This is where report generation is triggered.
    """
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle checkout completion
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
    
    return jsonify({'received': True})


def handle_successful_payment(session):
    """
    Process successful payment:
    1. Extract birth data from metadata
    2. Generate natal chart
    3. Create PDF report
    4. Send email to customer
    """
    metadata = session.get('metadata', {})
    
    try:
        # Parse birth data
        birth_dt = parse_birth_datetime(
            metadata['birth_date'],
            metadata['birth_time']
        )
        
        # Create natal chart
        chart = create_chart(
            name=metadata['full_name'],
            birth_date=birth_dt,
            latitude=float(metadata['latitude']),
            longitude=float(metadata['longitude']),
            timezone_str=metadata.get('timezone', 'UTC')
        )
        
        # Generate report
        order_id = metadata['order_id']
        report_filename = f"report_{order_id}.pdf"
        report_path = os.path.join(REPORTS_DIR, report_filename)
        
        generate_report(
            chart=chart,
            output_path=report_path,
            language=metadata.get('language', 'en')
        )
        
        # Send email
        send_report_email(
            email=session['customer_email'],
            name=metadata['full_name'],
            report_path=report_path
        )
        
        # Store order in database (implement your DB logic)
        store_order({
            'order_id': order_id,
            'email': session['customer_email'],
            'plan': metadata['plan'],
            'chart_hash': chart.chart_hash,
            'report_path': report_path,
            'created_at': datetime.now().isoformat(),
            'status': 'completed'
        })
        
        print(f"[SUCCESS] Report generated for order {order_id}")
        
    except Exception as e:
        print(f"[ERROR] Failed to process order: {str(e)}")
        # Implement error notification/retry logic


def store_order(order_data: dict):
    """
    Store order in database.
    Implement your database logic here (PostgreSQL, MongoDB, etc.)
    """
    # Example: Store in JSON file (use proper DB in production)
    orders_file = os.path.join(REPORTS_DIR, 'orders.json')
    
    try:
        with open(orders_file, 'r') as f:
            orders = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        orders = []
    
    orders.append(order_data)
    
    with open(orders_file, 'w') as f:
        json.dump(orders, f, indent=2)


@app.route('/api/download/<order_id>', methods=['GET'])
def download_report(order_id: str):
    """Download report by order ID."""
    report_path = os.path.join(REPORTS_DIR, f"report_{order_id}.pdf")
    
    if os.path.exists(report_path):
        return send_file(
            report_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'celestial_insights_report_{order_id}.pdf'
        )
    
    return jsonify({'error': 'Report not found'}), 404


@app.route('/api/verify-session/<session_id>', methods=['GET'])
def verify_session(session_id: str):
    """Verify checkout session status."""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        return jsonify({
            'status': session.payment_status,
            'order_id': session.metadata.get('order_id'),
            'customer_email': session.customer_email
        })
        
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/preview-chart', methods=['POST'])
def preview_chart():
    """
    Generate a preview chart (for demo/testing).
    Returns chart data as JSON without generating PDF.
    """
    try:
        data = request.json
        
        birth_dt = parse_birth_datetime(
            data.get('birthDate', '1990-01-01'),
            data.get('birthTime', '12:00')
        )
        
        chart = create_chart(
            name=data.get('name', 'Preview'),
            birth_date=birth_dt,
            latitude=float(data.get('latitude', 0)),
            longitude=float(data.get('longitude', 0)),
            timezone_str=data.get('timezone', 'UTC')
        )
        
        return jsonify({
            'success': True,
            'chart': chart.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================
# SUCCESS/CANCEL PAGES (if not using SPA)
# ============================================

@app.route('/success')
def success_page():
    """Success page after payment."""
    session_id = request.args.get('session_id')
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Successful | Celestial Insights</title>
        <style>
            body {{ font-family: Georgia, serif; background: #0f0f1a; color: #f8f6ff; 
                   display: flex; align-items: center; justify-content: center; 
                   min-height: 100vh; margin: 0; }}
            .container {{ text-align: center; padding: 2rem; }}
            h1 {{ color: #D4AF37; }}
            a {{ color: #D4AF37; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✧ Payment Successful! ✧</h1>
            <p>Thank you for your order.</p>
            <p>Your personalized astrology report is being generated and will be sent to your email shortly.</p>
            <p>Order Reference: {session_id[:8] if session_id else 'N/A'}...</p>
            <p><a href="/">Return to Home</a></p>
        </div>
    </body>
    </html>
    '''


@app.route('/cancel')
def cancel_page():
    """Cancel page if payment is abandoned."""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Cancelled | Celestial Insights</title>
        <style>
            body { font-family: Georgia, serif; background: #0f0f1a; color: #f8f6ff; 
                   display: flex; align-items: center; justify-content: center; 
                   min-height: 100vh; margin: 0; }
            .container { text-align: center; padding: 2rem; }
            h1 { color: #D4AF37; }
            a { color: #D4AF37; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Payment Cancelled</h1>
            <p>Your payment was cancelled. No charges have been made.</p>
            <p><a href="/">Return to Home</a></p>
        </div>
    </body>
    </html>
    '''


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == '__main__':
    print("=" * 50)
    print("Celestial Insights Backend Server")
    print("=" * 50)
    print(f"Reports directory: {REPORTS_DIR}")
    print(f"Domain: {DOMAIN}")
    print("=" * 50)
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    )

# 🚀 Celestial Insights - Complete Deployment Guide

## From Zero to Live Website

This guide will take you from having nothing to a fully operational astrology report business.

---

## 📋 Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Domain & Hosting Setup](#2-domain--hosting-setup)
3. [Stripe Configuration](#3-stripe-configuration)
4. [Backend Deployment](#4-backend-deployment)
5. [Frontend Deployment](#5-frontend-deployment)
6. [Database Setup](#6-database-setup)
7. [Email Configuration](#7-email-configuration)
8. [Testing](#8-testing)
9. [Going Live](#9-going-live)
10. [Maintenance & Scaling](#10-maintenance--scaling)

---

## 1. Prerequisites

### What You Need
- [ ] Computer with internet access
- [ ] Credit card (for domain, hosting, and Stripe)
- [ ] Email address for business
- [ ] Basic command line familiarity

### Accounts to Create (all have free tiers)
- [ ] GitHub account (github.com) - code hosting
- [ ] Stripe account (stripe.com) - payments
- [ ] Vercel account (vercel.com) - frontend hosting
- [ ] Railway account (railway.app) - backend hosting
- [ ] SendGrid account (sendgrid.com) - email delivery
- [ ] Domain registrar (Namecheap, Cloudflare, etc.)

---

## 2. Domain & Hosting Setup

### 2.1 Purchase Domain

**Recommended registrars:**
- Cloudflare Registrar (cheapest, no markup)
- Namecheap
- Google Domains

**Steps:**
1. Go to your chosen registrar
2. Search for your domain (e.g., `celestialinsights.com`)
3. Purchase the domain (~$10-15/year for .com)
4. Keep the confirmation email safe

### 2.2 Set Up DNS (do this later after deployment)

You'll configure DNS to point to:
- `yourdomain.com` → Frontend (Vercel)
- `api.yourdomain.com` → Backend (Railway)

---

## 3. Stripe Configuration

### 3.1 Create Stripe Account

1. Go to [stripe.com](https://stripe.com)
2. Click "Start now" and create account
3. Verify your email
4. Complete business information (can use personal for testing)

### 3.2 Get API Keys

1. In Stripe Dashboard, go to **Developers → API Keys**
2. Copy these keys (keep them secret!):
   - `Publishable key` (starts with `pk_test_...`)
   - `Secret key` (starts with `sk_test_...`)

### 3.3 Create Products and Prices

**Option A: Via Dashboard**
1. Go to **Products → Add Product**
2. Create three products:

   **Essential Report**
   - Name: "Celestial Insights - Essential Report"
   - Price: $29.99 (one-time)
   - Copy the Price ID (starts with `price_...`)

   **Premium Report**
   - Name: "Celestial Insights - Premium Report"
   - Price: $49.99 (one-time)
   - Copy the Price ID

   **Ultimate Report**
   - Name: "Celestial Insights - Ultimate Report"
   - Price: $69.99 (one-time)
   - Copy the Price ID

**Option B: Via API (run in terminal)**
```bash
# Install Stripe CLI first, then:
stripe products create --name="Essential Report" 
stripe prices create --product=prod_xxx --unit-amount=2999 --currency=usd
# Repeat for other products
```

### 3.4 Set Up Webhook

1. Go to **Developers → Webhooks**
2. Click **Add endpoint**
3. URL: `https://api.yourdomain.com/api/webhook` (update after deployment)
4. Select events: `checkout.session.completed`
5. Copy the **Signing secret** (starts with `whsec_...`)

---

## 4. Backend Deployment

### 4.1 Prepare Your Code

1. Create a GitHub repository:
```bash
cd celestial-insights
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/celestial-insights.git
git push -u origin main
```

2. Create `.env.example` file (for reference):
```env
# Stripe
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret
STRIPE_PRICE_ESSENTIAL=price_xxx
STRIPE_PRICE_PREMIUM=price_xxx
STRIPE_PRICE_ULTIMATE=price_xxx

# Email
SENDGRID_API_KEY=your_sendgrid_key

# App
DOMAIN=https://yourdomain.com
FLASK_DEBUG=False
PORT=5000
```

### 4.2 Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Click **New Project → Deploy from GitHub repo**
3. Select your repository
4. Railway auto-detects Python

**Configure Environment Variables:**
1. Go to your project → **Variables**
2. Add all variables from `.env.example` with real values

**Configure Domain:**
1. Go to **Settings → Domains**
2. Add custom domain: `api.yourdomain.com`
3. Copy the CNAME record
4. Add this CNAME to your domain DNS settings

### 4.3 Alternative: Deploy to Heroku

```bash
# Install Heroku CLI, then:
heroku login
heroku create celestial-insights-api
heroku config:set STRIPE_SECRET_KEY=sk_test_xxx
# ... set all other env vars
git push heroku main
```

### 4.4 Alternative: Deploy to DigitalOcean App Platform

1. Connect GitHub repo
2. Select Python environment
3. Set environment variables
4. Deploy

---

## 5. Frontend Deployment

### 5.1 Update Frontend Configuration

Edit `frontend/index.html` and update:

```javascript
const CONFIG = {
    STRIPE_PUBLISHABLE_KEY: 'pk_live_YOUR_LIVE_KEY', // Your real publishable key
    API_BASE_URL: 'https://api.yourdomain.com/api', // Your API URL
    // ... price IDs
};
```

### 5.2 Deploy to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click **Add New → Project**
3. Import your GitHub repository
4. Configure:
   - Framework: Other
   - Root Directory: `frontend`
   - Build Command: (leave empty)
   - Output Directory: (leave empty or `.`)
5. Click **Deploy**

**Configure Domain:**
1. Go to **Project Settings → Domains**
2. Add your domain: `yourdomain.com`
3. Vercel provides DNS records
4. Add these records to your domain registrar

### 5.3 Alternative: Deploy to Netlify

1. Go to [netlify.com](https://netlify.com)
2. Drag & drop your `frontend` folder
3. Or connect GitHub for auto-deploy
4. Configure custom domain

### 5.4 Alternative: Self-host with Nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/celestial-insights/frontend;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 6. Database Setup (Optional but Recommended)

For storing orders and customer data:

### 6.1 PostgreSQL on Railway

1. In Railway, click **New → Database → PostgreSQL**
2. Copy the connection string
3. Add to environment: `DATABASE_URL=postgresql://...`

### 6.2 Update Backend for Database

Install: `pip install psycopg2-binary sqlalchemy`

```python
# In app.py, replace store_order function:
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.getenv('DATABASE_URL'))
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(String, primary_key=True)
    email = Column(String)
    plan = Column(String)
    chart_hash = Column(String)
    created_at = Column(DateTime)
    status = Column(String)

Base.metadata.create_all(engine)

def store_order(order_data):
    session = Session()
    order = Order(**order_data)
    session.add(order)
    session.commit()
    session.close()
```

---

## 7. Email Configuration

### 7.1 SendGrid Setup

1. Create account at [sendgrid.com](https://sendgrid.com)
2. Verify your sender email/domain
3. Create API Key: **Settings → API Keys → Create**
4. Add to Railway environment: `SENDGRID_API_KEY=SG.xxx`

### 7.2 Verify Sender Domain (Important for deliverability)

1. In SendGrid: **Settings → Sender Authentication**
2. Follow DNS verification steps
3. Add CNAME and TXT records to your domain

### 7.3 Enable Email in Backend

Uncomment the SendGrid code in `app.py`:

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType
import base64

def send_report_email(email, name, report_path):
    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    
    with open(report_path, 'rb') as f:
        data = base64.b64encode(f.read()).decode()
    
    attachment = Attachment(
        FileContent(data),
        FileName(f'celestial_insights_{name.replace(" ", "_")}.pdf'),
        FileType('application/pdf')
    )
    
    message = Mail(
        from_email='reports@yourdomain.com',
        to_emails=email,
        subject=f'Your Celestial Insights Report is Ready!',
        html_content=f'<h1>Dear {name},</h1><p>Your report is attached.</p>'
    )
    message.attachment = attachment
    sg.send(message)
```

---

## 8. Testing

### 8.1 Test Payment Flow (Stripe Test Mode)

1. Ensure you're using test API keys (`pk_test_...`, `sk_test_...`)
2. Use Stripe test cards:
   - Success: `4242 4242 4242 4242`
   - Decline: `4000 0000 0000 0002`
   - Any future date, any CVC, any ZIP

### 8.2 Test Webhook Locally

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe  # macOS
# or download from stripe.com/docs/stripe-cli

# Forward webhooks to local server
stripe listen --forward-to localhost:5000/api/webhook

# This gives you a webhook signing secret for local testing
```

### 8.3 Test Report Generation

```bash
cd backend
python -c "
from astro_engine import create_chart
from report_generator import generate_report
from datetime import datetime

chart = create_chart(
    name='Test User',
    birth_date=datetime(1990, 5, 15, 14, 30),
    latitude=40.7128,
    longitude=-74.0060,
    timezone_str='America/New_York'
)
generate_report(chart, 'test_report.pdf')
print('Report generated: test_report.pdf')
"
```

### 8.4 Full Integration Test

1. Open your site
2. Fill in birth details
3. Select a plan
4. Complete payment with test card
5. Check email delivery
6. Verify report PDF

---

## 9. Going Live

### 9.1 Switch to Stripe Live Mode

1. In Stripe Dashboard, toggle from "Test" to "Live" mode
2. Complete account verification (ID, business info)
3. Get live API keys
4. Create live products/prices
5. Update webhook endpoint
6. Update all environment variables with live keys

### 9.2 Update Frontend

```javascript
const CONFIG = {
    STRIPE_PUBLISHABLE_KEY: 'pk_live_YOUR_LIVE_KEY', // LIVE key
    // ...
};
```

### 9.3 Security Checklist

- [ ] All API keys are in environment variables, not in code
- [ ] HTTPS enabled on all domains
- [ ] CORS configured for your domain only
- [ ] Rate limiting implemented
- [ ] Error logging set up (Sentry, LogRocket)
- [ ] Backups configured for database

### 9.4 Legal Requirements

- [ ] Privacy Policy page created
- [ ] Terms of Service page created
- [ ] Refund Policy defined
- [ ] Cookie consent (if required in your region)
- [ ] GDPR compliance (if serving EU customers)

---

## 10. Maintenance & Scaling

### 10.1 Monitoring

Set up monitoring:
- **Uptime**: UptimeRobot (free), Pingdom
- **Errors**: Sentry
- **Analytics**: Google Analytics, Plausible

### 10.2 Scaling

**If traffic increases:**

1. **Backend**: Railway auto-scales; or upgrade plan
2. **Database**: Upgrade PostgreSQL instance
3. **PDF Generation**: Move to background jobs with Celery/Redis
4. **CDN**: Add Cloudflare for static assets

### 10.3 Backups

```bash
# Database backup (Railway)
railway run pg_dump $DATABASE_URL > backup.sql

# Reports backup
railway run tar -czf reports_backup.tar.gz /app/generated_reports
```

### 10.4 Updates

```bash
# Deploy updates
git add .
git commit -m "Update feature X"
git push origin main
# Railway/Vercel auto-deploys from GitHub
```

---

## 🎉 Congratulations!

You now have a fully operational astrology report business!

### Quick Reference

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | yourdomain.com | Customer-facing site |
| Backend | api.yourdomain.com | API server |
| Stripe | dashboard.stripe.com | Payments |
| Railway | railway.app | Backend hosting |
| Vercel | vercel.com | Frontend hosting |
| SendGrid | sendgrid.com | Email delivery |

### Support Resources

- Stripe Docs: stripe.com/docs
- Railway Docs: docs.railway.app
- Vercel Docs: vercel.com/docs
- SendGrid Docs: docs.sendgrid.com

---

## Troubleshooting

### Payment not working
1. Check browser console for errors
2. Verify API URL is correct
3. Check Stripe Dashboard for failed payments
4. Verify webhook is receiving events

### Email not sending
1. Check SendGrid activity log
2. Verify sender domain is authenticated
3. Check spam folder
4. Review SendGrid bounce reports

### Report generation failing
1. Check Railway logs: `railway logs`
2. Verify all Python dependencies installed
3. Test locally first
4. Check disk space for generated reports

---

*Built with ❤️ by Celestial Insights*

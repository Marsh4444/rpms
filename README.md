# RPMS — Rental Property Management System

> A full-stack Django web application for managing rental properties, leases, payments, and maintenance requests — with role-based access control and production-grade security.

![Python](https://img.shields.io/badge/Python-3.14-blue?style=flat-square)
![Django](https://img.shields.io/badge/Django-6.0-green?style=flat-square)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?style=flat-square)
![Security](https://img.shields.io/badge/Security-Production--Ready-success?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Security](#security)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [User Roles](#user-roles)
- [Business Logic Highlights](#business-logic-highlights)
- [Screenshots](#screenshots)
- [Future Improvements](#future-improvements)
- [Author](#author)

---

## Overview

RPMS is a portfolio project built to demonstrate real-world Django backend skills — not just CRUD, but actual business logic paired with production-grade security. It handles overlapping lease prevention, duplicate payment detection, maintenance SLA tracking, and role-gated views — the kinds of problems that show up in production systems.

The security layer was built deliberately: rate limiting, session fixation prevention, CSRF protection, HTTP security headers, and a full password reset flow using email tokens. This isn't a tutorial project with security bolted on at the end — it was designed with it from the start.

Built without Django REST Framework intentionally, to prove mastery of core Django before layering abstractions on top.

---

## Features

### Property & Unit Management
- Create, update, and archive properties with address and description
- Manage multiple units per property (unit number, type, rent amount, occupancy status)
- Automatic occupancy status update when a lease is created or closed

### Lease Management
- Create leases linking a tenant to a specific unit
- **Overlap prevention** — the system rejects any lease that conflicts with an existing active lease on the same unit
- Lease status tracking: Active, Expired, Terminated
- Lease expiry awareness on dashboards

### Payment Management
- Record rent payments against active leases
- **Duplicate payment detection** — prevents the same payment from being recorded twice for the same period
- Payment history per lease and per tenant
- Overdue tracking

### Maintenance Requests
- Tenants submit requests with priority levels: Low, Medium, High, Emergency
- **SLA tracking** — response deadlines calculated from priority at time of submission
- Status workflow: Open → In Progress → Resolved → Closed
- Managers and Landlords can update status and add resolution notes

### Role-Based Access Control
- Three distinct user roles: **Landlord**, **Manager**, **Tenant**
- Each role gets a tailored dashboard showing only what is relevant to them
- View-level permission enforcement — tenants cannot access landlord routes and vice versa
- Custom `@role_required` decorator used across views

### Authentication & Profiles
- Custom `User` model extending `AbstractUser` with role and profile picture fields
- Registration with role selection
- Full password reset flow via email token (3-day expiry)
- Profile view and edit
- Login / Logout with session cycling on authentication

---

## Security

Security was treated as a first-class concern throughout development — not an afterthought. Below is a full breakdown of every security measure implemented.

### Password Security

| Feature | Implementation |
|---|---|
| Strong validation | Minimum 8 characters, rejects common passwords, rejects all-numeric passwords |
| Hashed storage | Django's default bcrypt-based password hashing — passwords are never stored in plain text |
| Password reset | Email-based token system with 3-day expiration via `django.contrib.auth` password reset views |

### Session Security

| Feature | Implementation |
|---|---|
| Automatic timeout | Sessions expire after **30 minutes** of inactivity (`SESSION_COOKIE_AGE = 1800`) |
| Session expiry on close | Browser session cookies expire when the browser is closed (`SESSION_EXPIRE_AT_BROWSER_CLOSE = True`) |
| HttpOnly cookies | JavaScript cannot access session cookies, preventing XSS-based session theft (`SESSION_COOKIE_HTTPONLY = True`) |
| SameSite cookies | Cookies are not sent with cross-site requests, preventing CSRF via cookie (`SESSION_COOKIE_SAMESITE = 'Lax'`) |
| Session key cycling | A new session ID is issued on every login (`request.session.cycle_key()`), preventing session fixation attacks |

### Login Protection

| Feature | Implementation |
|---|---|
| Rate limiting | Maximum **5 login attempts per minute per IP** address using `django-ratelimit` |
| Brute force prevention | Requests exceeding the rate limit are blocked and shown an error — the view returns early before any auth logic runs |
| Credential stuffing mitigation | IP-based rate limiting adds a meaningful barrier to automated credential stuffing attacks |

```python
# Login view — rate limiting in action
@ratelimit(key='ip', rate='5/m', method='POST', block=False)
def login_view(request):
    was_limited = getattr(request, 'limited', False)
    if was_limited:
        messages.error(request, 'Too many login attempts. Please wait a minute.')
        return render(request, 'registration/login.html', {'form_blocked': True})
    ...
```

### HTTP Security Headers

| Header | Value | Protection |
|---|---|---|
| `X-Frame-Options` | `DENY` | Prevents clickjacking — page cannot be embedded in an iframe |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME sniffing — browser respects declared content type |
| `X-XSS-Protection` | Enabled | Browser-level XSS filter activated |
| `Referrer-Policy` | `same-origin` | Limits referrer information sent to external sites |
| `CSRF tokens` | All forms | Every POST form is protected with Django's CSRF middleware |

### Production Security (when deployed)

| Feature | Setting | Description |
|---|---|---|
| HTTPS enforcement | `SECURE_SSL_REDIRECT = True` | All HTTP traffic is redirected to HTTPS |
| HSTS | `SECURE_HSTS_SECONDS = 31536000` | Browsers remember to always use HTTPS for 1 year |
| HSTS subdomains | `SECURE_HSTS_INCLUDE_SUBDOMAINS = True` | HTTPS enforced on all subdomains |
| Secure cookies | `SESSION_COOKIE_SECURE = True` | Session cookies only transmitted over HTTPS |
| Secure CSRF | `CSRF_COOKIE_SECURE = True` | CSRF cookies only transmitted over HTTPS |

### Configuration Security

- **Split settings** — Separate `dev.py` and `prod.py` configurations. Debug mode is only ever `True` in development.
- **Environment variables** — All secrets (SECRET_KEY, database credentials, email passwords) are stored in `.env` files and never committed to version control.
- **`.gitignore`** — `.env` and `local_settings.py` are explicitly ignored in version control.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.14 |
| Framework | Django 6.0 |
| Database | PostgreSQL 15 |
| Frontend | Custom HTML/CSS (DM Mono + Syne via Google Fonts) |
| Auth | Django built-in auth with custom User model |
| Rate Limiting | django-ratelimit |
| Image handling | Pillow |
| Deployment target | PythonAnywhere / Railway |

---

## Project Structure

```
rpms/
├── apps/
│   ├── users/                  # Custom user model, auth views, profile
│   │   ├── models.py           # CustomUser with role field
│   │   ├── views.py            # Register, login, logout, profile, dashboards
│   │   ├── decorators.py       # @role_required decorator
│   │   └── templates/
│   ├── properties/             # Property and Unit models
│   ├── leases/                 # Lease model with overlap prevention
│   ├── payments/               # Payment model with duplicate detection
│   └── maintenance/            # Maintenance requests + SLA tracking
├── config/
│   ├── settings.py             # Project settings with security config
│   └── urls.py
├── static/
│   └── css/
│       ├── base.css            # Global design system
│       └── maintenance.css
├── templates/
│   ├── base.html               # Global layout — navbar, footer, flash messages
│   ├── home.html               # Landing page
│   ├── registration/           # Login, register, password reset templates
│   └── dashboards/             # Role-based dashboard templates
├── .env                        # Environment variables (not committed)
├── .env.example                # Template for environment setup
├── .gitignore
├── requirements.txt
└── manage.py
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL installed and running
- Git

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/Marsh4444/rpms.git
cd rpms

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your database credentials and secret key

# 5. Run migrations
python manage.py migrate

# 6. Create a superuser
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

---

## Environment Variables

Create a `.env` file in the project root. See `.env.example` for the full list.

```env
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DB_NAME=rpms_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# Email (for password reset)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Production only
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

---

## User Roles

| Role | Access |
|---|---|
| **Landlord** | Full access — manage all properties, units, leases, payments, maintenance, and users |
| **Manager** | Manage assigned properties, update maintenance requests, view payments |
| **Tenant** | View own lease, submit maintenance requests, view own payment history |

Roles are enforced at the view level using a custom `@role_required(roles=[...])` decorator.

```python
from apps.users.decorators import role_required

@login_required
@role_required(['LANDLORD', 'MANAGER'])
def property_list(request):
    ...
```

---

## Business Logic Highlights

### Overlapping Lease Prevention
```python
# leases/models.py — clean() method
def clean(self):
    overlapping = Lease.objects.filter(
        unit=self.unit,
        status='active',
        start_date__lt=self.end_date,
        end_date__gt=self.start_date,
    ).exclude(pk=self.pk)

    if overlapping.exists():
        raise ValidationError(
            "This unit already has an active lease during this period."
        )
```

### SLA Deadline Calculation (Maintenance)
```python
# maintenance/models.py
SLA_HOURS = {
    'low': 72,
    'medium': 24,
    'high': 8,
    'emergency': 2,
}

def save(self, *args, **kwargs):
    if not self.pk:  # only on creation
        hours = SLA_HOURS.get(self.priority, 24)
        self.sla_deadline = timezone.now() + timedelta(hours=hours)
    super().save(*args, **kwargs)
```

### Duplicate Payment Detection
```python
# payments/models.py — clean() method
def clean(self):
    duplicate = Payment.objects.filter(
        lease=self.lease,
        payment_month=self.payment_month,
        payment_year=self.payment_year,
    ).exclude(pk=self.pk)

    if duplicate.exists():
        raise ValidationError(
            "A payment for this period has already been recorded."
        )
```

### Session Fixation Prevention
```python
# users/views.py — login_view
if user is not None:
    request.session.cycle_key()  # new session ID on login
    login(request, user)
    ...
```

---

## Screenshots

| Page | Description |
|---|---|
| `screenshots/home.png` | Landing page with estate background |
| `screenshots/dashboard-landlord.png` | Landlord dashboard with revenue stats |
| `screenshots/dashboard-tenant.png` | Tenant dashboard with lease and request status |
| `screenshots/property-list.png` | Property listing with unit counts |
| `screenshots/lease-create.png` | Lease creation form with overlap validation |
| `screenshots/payment-list.png` | Payment history table |
| `screenshots/maintenance-list.png` | Maintenance requests with SLA badges |
| `screenshots/maintenance-detail.png` | Single request with status update |

---

## Future Improvements

- [ ] Email notifications on lease expiry and maintenance status change
- [ ] PDF receipt generation for payments
- [ ] Django REST Framework API layer for mobile/React frontend
- [ ] Occupancy and income analytics charts
- [ ] Multi-tenancy support for property management companies
- [ ] Audit log — track who changed what and when

---

## Author

**Holyfield Nwadike (Marsh)**
Backend Developer | Educator

- GitHub: [@Marsh4444](https://github.com/Marsh4444)
- Twitter/X: [@0xeMarsh](https://x.com/0xeMarsh)

---

*Built with Django as a portfolio project demonstrating production-grade backend patterns — business logic, role-based access control, and a security layer that goes beyond the defaults.*

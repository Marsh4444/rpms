from .base import *
from decouple import config
# Import all base settings
# Then override with production-specific ones

# ============================================================================
# PRODUCTION OVERRIDES
# ============================================================================

DEBUG = False
# MUST be False in production
# Never show detailed errors to users
# Shows generic error pages instead

# ============================================================================
# SECURITY SETTINGS (Production Only)
# ============================================================================

SECURE_SSL_REDIRECT = True
# Force all HTTP requests to redirect to HTTPS
# Example: http://yoursite.com → https://yoursite.com
# Essential for security (protects passwords, data)

SESSION_COOKIE_SECURE = True
# Only send session cookies over HTTPS
# Prevents session hijacking on public WiFi

CSRF_COOKIE_SECURE = True
# Only send CSRF tokens over HTTPS
# Protects against Cross-Site Request Forgery

# ============================================================================
# STATIC FILES WITH WHITENOISE
# ============================================================================

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
# Insert Whitenoise at position 1 in MIDDLEWARE list
# Whitenoise serves static files in production (Render, Heroku)
# Must come right after SecurityMiddleware (position 0)

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# Compress static files (CSS/JS) and add hashes to filenames
# style.css → style.a3f7b.css
# Browser caches files forever, new versions get new names
# Makes your site faster

# Why separate production settings?
# - Security features that aren't needed locally
# - Performance optimizations (compression, caching)
# - Different static file serving strategy

# CACHE CONFIGURATION - PRODUCTION
# ============================================================================
# In production, use Redis for proper distributed rate limiting
# Install: pip install redis django-redis
# ============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# ============================================================================
# EMAIL BACKEND - PRODUCTION (Phase 17)
# ============================================================================
# Real email sending via SMTP (Gmail, SendGrid, etc.)
# ============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='RPMS <noreply@rpms.com>')

# ============================================================================
# SESSION & COOKIE SECURITY - PRODUCTION (Phase 17)
# ============================================================================
# HTTPS-only cookies and session protection
# ============================================================================

SESSION_COOKIE_SECURE = True  # Requires HTTPS
CSRF_COOKIE_SECURE = True     # Requires HTTPS

# ============================================================================
# HTTPS ENFORCEMENT - PRODUCTION (Phase 17)
# ============================================================================
# Redirect all HTTP to HTTPS
# ============================================================================

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

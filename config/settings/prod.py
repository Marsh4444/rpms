from .base import *
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
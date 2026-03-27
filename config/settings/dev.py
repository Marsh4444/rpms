from .base import *
#from pathlib import Path

# Import EVERYTHING from base.py
# The * means "import all variables"
# So all the settings from base.py are now available here
# We can then OVERRIDE specific ones for development

# ============================================================================
# DEVELOPMENT OVERRIDES
# ============================================================================

DEBUG = True
# Force DEBUG on in development
# Even if .env says False, this overrides it
# Shows detailed error pages when things break

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']
# Only respond to localhost requests
# No need for domain names in development

# Database (SQLite for development)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


# ============================================================================
# DEVELOPMENT-ONLY APPS
# ============================================================================

INSTALLED_APPS += [
    # The += means "add to the existing list from base.py"
    # Don't replace INSTALLED_APPS, just add to it
    
    # 'django_extensions',  # Optional: adds management commands
    # You can install this later with: pip install django-extensions
    # Provides commands like: python manage.py shell_plus
]

# Why separate dev settings?
# - Keep development conveniences out of production
# - Easier debugging in development
# - Production stays clean and secure# ============================================================================

# ============================================================================
# CACHE - Dummy cache for development (Phase 17)
# ============================================================================
# For portfolio/development only - production would use Redis
# ============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
# EMAIL BACKEND - DEVELOPMENT (Phase 17)
# ============================================================================
# Prints emails terminal instead of sending them
# Perfect for testing password reset without real email server
# ============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'RPMS <noreply@rpms.local>'

# ============================================================================
# SESSION COOKIE SETTINGS - DEVELOPMENT (Phase 17)
# ============================================================================
# In development, we use HTTP (not HTTPS), so keep this False
# ============================================================================

SESSION_COOKIE_SECURE = False  # Set to True in production


RATELIMIT_USE_CACHE = "default"
SILENCED_SYSTEM_CHECKS = ["django_ratelimit.E003"]
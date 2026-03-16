from .base import *
# Import EVERYTHING from base.py
# The * means "import all variables"
# So all the settings from base.py are now available here
# We can then OVERRIDE specific ones for development

# ============================================================================
# DEVELOPMENT OVERRIDES
# ============================================================================

DEBUG = False
# Force DEBUG on in development
# Even if .env says False, this overrides it
# Shows detailed error pages when things break

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
# Only respond to localhost requests
# No need for domain names in development

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
# - Production stays clean and secure
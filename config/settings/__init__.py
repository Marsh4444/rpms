from decouple import config
# Import the function that reads .env file

# ============================================================================
# ENVIRONMENT DETECTION
# ============================================================================

environment = config('ENVIRONMENT', default='dev')
# Read ENVIRONMENT variable from .env
# If not found, default to 'dev' (development)
#
# In your .env (for development):
# ENVIRONMENT=dev
#
# On Render (production), you'd set:
# ENVIRONMENT=prod

# ============================================================================
# CONDITIONAL IMPORT
# ============================================================================

if environment == 'prod':
    from .prod import *
    # If ENVIRONMENT=prod, load production settings
    # Uses prod.py (DEBUG=False, security on)
else:
    from .dev import *
    # Otherwise, load development settings
    # Uses dev.py (DEBUG=True, easier debugging)

# How it works:
# 1. Django tries to import config.settings (because of manage.py)
# 2. It finds config/settings/__init__.py (this file)
# 3. This file checks ENVIRONMENT
# 4. Loads either dev.py or prod.py
# 5. Which both load base.py first
#
# Result: You get the right settings automatically!

# rpms
## 🔒 Security Features

### Password Security
- **Strong password validation** - Minimum 8 characters, not common passwords, not all numbers
- **Password reset flow** - Email-based token system with 3-day expiration
- **Hashed storage** - Passwords never stored in plain text (bcrypt)

### Session Security
- **Automatic timeout** - 30-minute inactivity logout
- **HttpOnly cookies** - JavaScript cannot access session cookies (XSS protection)
- **SameSite cookies** - CSRF attack prevention
- **Session key cycling** - New session ID on login (session fixation prevention)

### Login Protection
- **Rate limiting** - Maximum 5 login attempts per minute per IP (prevents brute force)
- **django-ratelimit** integration

### HTTP Security Headers
- **X-Frame-Options: DENY** - Prevents clickjacking attacks
- **Content-Type nosniff** - Prevents MIME sniffing attacks
- **XSS Filter** - Browser-level XSS protection enabled

### Production-Ready Features
- **Split settings** - Separate dev/production configurations
- **Environment variables** - Secrets stored in .env files (not in code)
- **HTTPS enforcement** - SSL redirect and HSTS headers in production
- **CSRF tokens** - All forms protected against cross-site request forgery

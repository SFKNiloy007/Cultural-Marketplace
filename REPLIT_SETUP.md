# Replit Deployment Guide

## Quick Setup

### 1. Upload to Replit

- Compress the `Project` folder as ZIP
- Go to replit.com → "+ Create Repl" → "Import from ZIP"
- Upload and name it "Artisan-Marketplace"

### 2. Set Database URL

- Click "Secrets" (lock icon) or use `.env` file
- Add: `DATABASE_URL=your_postgresql_connection_string`

For free PostgreSQL:

- **Option A**: Replit → "Database" icon → Enable PostgreSQL → Copy URL
- **Option B**: Neon.tech (free tier) → Create database → Copy connection string

### 3. Run Database Setup

In Replit Shell:

```bash
# If using external DB with schema file
psql $DATABASE_URL < schema.sql

# Or run your setup scripts
python create_admin.py
```

### 4. Click "Run"

- Replit installs packages from requirements.txt
- Server starts on port 8000
- Webview opens automatically

### 5. Access Your App

- Use the Replit URL shown (e.g., `https://artisan-marketplace.yourname.repl.co`)
- Share this URL for testing

## Troubleshooting

### "Connection error" in login

- ✅ Fixed: API URLs now auto-detect Replit
- ✅ Fixed: CORS allows Replit domains

### Database connection fails

- Check Secrets has `DATABASE_URL`
- Verify connection string format: `postgresql://user:pass@host:port/db`
- Run schema.sql to create tables

### Port/Address errors

- ✅ Fixed: `.replit` uses `--host 0.0.0.0`

### Missing packages

- ✅ Fixed: `requirements.txt` includes all dependencies

## Files Updated for Replit

- `.replit` - Run configuration
- `requirements.txt` - Python dependencies
- `main.py` - CORS updated for Replit domains
- All HTML files - API URL auto-detection

## Test Credentials

Create test users via `/register` endpoint or use your existing admin account.

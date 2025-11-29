# SETUP INSTRUCTIONS - Artisan E-Marketplace

## Quick Start Guide

### Step 1: Setup Database

1. **Create PostgreSQL database:**

```bash
createdb artisan_marketplace
```

2. **Run main schema:**

```bash
psql -U your_username -d artisan_marketplace -f schema.sql
```

3. **Add test users:**

```bash
psql -U your_username -d artisan_marketplace -f test_users.sql
```

### Step 2: Configure Environment

Create `.env` file in the project folder:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/artisan_marketplace
```

### Step 3: Start Backend Server

```bash
uvicorn main:app --reload
```

Server will run at: http://127.0.0.1:8000

### Step 4: Open Frontend

Open `login.html` in your browser or use Live Server in VS Code.

## Test Accounts

All passwords are: `12345`

| Role        | Email                 | Description                         |
| ----------- | --------------------- | ----------------------------------- |
| **Artisan** | test.artisan@uni.edu  | Can list products, manage inventory |
| **Buyer**   | test.buyer@uni.edu    | Can browse and purchase products    |
| **Admin**   | admin@marketplace.com | Platform management                 |

## Troubleshooting

### Login Failed Error

- Make sure you ran `test_users.sql` after `schema.sql`
- Check that backend server is running
- Verify DATABASE_URL in .env file is correct

### Backend Not Starting

- Check Python packages are installed:
  ```bash
  pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv passlib python-jose python-multipart
  ```
- Verify .env file exists and has correct DATABASE_URL

### No Products Showing

- Run test_users.sql which includes sample products
- Or log in as artisan and add products manually

## New Features vs Old System

### What Changed:

- **Cleaner schema** - Uses inheritance pattern for User types
- **Simplified structure** - Removed business_name, uses email
- **Digital Wallet** - 1:1 relationship with artisan
- **No verification_status** - Removed from Artisan table

### Features Temporarily Disabled:

- Complaint system (can be re-added later)
- Artisan verification workflow (schema doesn't support it)

## Project Structure

```
Project/
├── login.html          # New role-based login page
├── buyer.html          # Buyer dashboard
├── artisan.html        # Artisan dashboard
├── admin.html          # Admin dashboard
├── index.html          # Old combined dashboard (backup)
├── main.py             # FastAPI backend
├── database.py         # DB connection
├── schema.sql          # Main database schema
├── test_users.sql      # Test data (RUN THIS!)
└── README.md           # Full documentation
```

## Next Steps

1. Run the SQL files to create users
2. Login with test.artisan@uni.edu / 12345
3. Add some products
4. Switch to buyer account and make purchases
5. Check admin panel for audit logs

## Need Help?

Check the main README.md for full API documentation and feature details.

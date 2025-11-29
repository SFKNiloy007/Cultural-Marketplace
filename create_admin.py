import bcrypt
from database import SessionLocal, engine
from sqlalchemy import text

# Create admin user
email = "admin@marketplace.com"
password = "admin123"

# Hash password
hashed = bcrypt.hashpw(password.encode(
    'utf-8'), bcrypt.gensalt()).decode('utf-8')

# Insert into database
db = SessionLocal()
try:
    # Check if admin already exists
    result = db.execute(text('SELECT user_id FROM "User" WHERE email = :email'), {
                        'email': email}).fetchone()

    if result:
        # Update existing admin password
        db.execute(text('''
            UPDATE "User" SET password_hash = :password_hash, is_active = TRUE
            WHERE email = :email
        '''), {'email': email, 'password_hash': hashed})
        db.commit()
        print(f"Admin password updated successfully!")
        print(f"Email: {email}")
        print(f"Password: {password}")
    else:
        # Insert new admin user
        db.execute(text('''
            INSERT INTO "User" (email, password_hash, is_active, registration_date)
            VALUES (:email, :password_hash, TRUE, CURRENT_TIMESTAMP)
        '''), {'email': email, 'password_hash': hashed})
        db.commit()
        print(f"Admin user created successfully!")
        print(f"Email: {email}")
        print(f"Password: {password}")
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()

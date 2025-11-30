"""
Script to initialize Render database with schema and test data.
Run this after setting DATABASE_URL environment variable to your Render PostgreSQL URL.
"""
import os
import psycopg2
from pathlib import Path

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set!")
    print("\nTo use this script:")
    print("1. Go to Render dashboard → Your web service → Environment")
    print("2. Copy the DATABASE_URL value")
    print("3. Run: $env:DATABASE_URL='<paste-url-here>'; python init_render_db.py")
    exit(1)

print(f"Connecting to: {DATABASE_URL[:50]}...")

try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    print("✓ Connected successfully!")

    # Read and execute schema.sql
    print("\n1. Creating tables from schema.sql...")
    schema_path = Path("schema.sql")
    if schema_path.exists():
        with open(schema_path, 'r', encoding='utf-8') as f:
            cursor.execute(f.read())
        print("✓ Tables created")
    else:
        print("✗ schema.sql not found!")

    # Read and execute test_users.sql
    print("\n2. Adding test users from test_users.sql...")
    test_users_path = Path("test_users.sql")
    if test_users_path.exists():
        with open(test_users_path, 'r', encoding='utf-8') as f:
            cursor.execute(f.read())
        print("✓ Test users added")
    else:
        print("✗ test_users.sql not found!")

    # Read and execute migrations
    print("\n3. Running migrations...")

    migration_files = [
        "add_product_images.sql",
        "add_product_description.sql"
    ]

    for migration in migration_files:
        migration_path = Path(migration)
        if migration_path.exists():
            print(f"   Running {migration}...")
            with open(migration_path, 'r', encoding='utf-8') as f:
                try:
                    cursor.execute(f.read())
                    print(f"   ✓ {migration} applied")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"   ⊘ {migration} already applied")
                    else:
                        print(f"   ✗ {migration} failed: {e}")
        else:
            print(f"   ⊘ {migration} not found")

    # Verify tables exist
    print("\n4. Verifying tables...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    print(f"✓ Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")

    # Check if admin user exists
    print("\n5. Checking admin user...")
    cursor.execute('SELECT email FROM "User" WHERE email = %s',
                   ('admin@marketplace.com',))
    admin = cursor.fetchone()
    if admin:
        print(f"✓ Admin user exists: {admin[0]}")
    else:
        print("✗ Admin user not found!")

    cursor.close()
    conn.close()

    print("\n" + "="*50)
    print("✅ DATABASE INITIALIZATION COMPLETE!")
    print("="*50)
    print("\nYou can now login at:")
    print("https://cultural-marketplace.onrender.com/login.html")
    print("\nAdmin credentials:")
    print("Email: admin@marketplace.com")
    print("Password: admin123")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nMake sure:")
    print("1. DATABASE_URL is correct")
    print("2. You have psycopg2 installed: pip install psycopg2-binary")
    print("3. Your IP is whitelisted if Render requires it")

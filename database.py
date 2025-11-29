import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# --- ROBUST ENV LOADING ---
# Build paths inside the project like this: BASE_DIR / '.env'
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"

# Explicitly load the .env file from the current directory
load_dotenv(dotenv_path=env_path)

# --- Database Connection Details ---
DATABASE_URL = os.getenv("DATABASE_URL")

# Debugging: Print to console so you can see what is happening
print(f"DEBUG: Looking for .env at: {env_path}")
print(f"DEBUG: File exists? {env_path.exists()}")
if DATABASE_URL:
    print("DEBUG: DATABASE_URL found successfully.")
else:
    print("DEBUG: DATABASE_URL is EMPTY or NOT FOUND.")

if not DATABASE_URL:
    raise Exception(
        "DATABASE_URL not found in .env file. Please check file name (is it .env.txt?) and location.")

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

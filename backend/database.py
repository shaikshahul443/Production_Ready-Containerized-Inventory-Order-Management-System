import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError

# Retrieve database URL from environment. Default to SQLite if not specified for easy local run
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///./inventory.db"
)

is_sqlite = DATABASE_URL.startswith("sqlite")

# Connection args for SQLite
engine_args = {}
if is_sqlite:
    engine_args["connect_args"] = {"check_same_thread": False}

# Robust engine creation
engine = None
if is_sqlite:
    engine = create_engine(DATABASE_URL, **engine_args)
else:
    # Postgres connection retries (Docker Compose)
    retries = 5
    while retries > 0:
        try:
            engine = create_engine(DATABASE_URL)
            # Test connection
            with engine.connect() as conn:
                break
        except OperationalError:
            retries -= 1
            print(f"Database connection failed. Retrying in 3 seconds... ({retries} retries left)")
            time.sleep(3)

    if engine is None:
        engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

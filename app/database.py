"""
Database bootstrap for local & production (Supabase).
"""
import os
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings


def ensure_database_exists() -> None:
    """Connects to the maintenance DB and creates POSTGRES_DB if missing (Only for Local)."""
    # Render cloud / Supabase deploy එකකදී මේක Skip කරනු ලැබේ.
    if settings.DATABASE_URL and "supabase.com" in settings.DATABASE_URL:
        print("[db-init] Supabase Cloud Database detected. Skipping local DB creation.")
        return

    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
        )
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s;",
                    (settings.POSTGRES_DB,),
                )
                exists = cur.fetchone()
                if not exists:
                    cur.execute(
                        sql.SQL("CREATE DATABASE {}").format(
                            sql.Identifier(settings.POSTGRES_DB)
                        )
                    )
                    print(f"[db-init] Created database '{settings.POSTGRES_DB}'.")
                else:
                    print(f"[db-init] Database '{settings.POSTGRES_DB}' already exists.")
        finally:
            conn.close()
    except Exception as e:
        print(f"[db-init] Local DB check skipped or failed: {e}")


# Run local check only if needed
ensure_database_exists()

# SQLAlchemy connection setup
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_all_tables() -> None:
    """Import models then create every table that doesn't exist yet."""
    from app import models  # noqa: F401  (import registers models on Base)

    Base.metadata.create_all(bind=engine)
    print("[db-init] Tables verified/created successfully.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
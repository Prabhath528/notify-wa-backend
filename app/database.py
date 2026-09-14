"""
Database bootstrap.

On startup this module:
1. Connects to the default 'postgres' maintenance database using the
   credentials in .env (pgAdmin4 local test setup - user postgres /
   password admin123 by default).
2. Checks whether the target database (POSTGRES_DB, default
   'notify_wa_db') exists. If it does not, it creates it automatically -
   no manual CREATE DATABASE step needed in pgAdmin4.
3. Creates a SQLAlchemy engine + session factory pointed at that database.
4. Exposes create_all_tables() which main.py calls on startup to build
   every table from the models in models.py if they don't already exist.
"""
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings


def ensure_database_exists() -> None:
    """Connects to the maintenance DB and creates POSTGRES_DB if missing."""
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


# Make sure the DB exists before SQLAlchemy tries to connect to it.
ensure_database_exists()

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_all_tables() -> None:
    """Import models then create every table that doesn't exist yet."""
    from app import models  # noqa: F401  (import registers models on Base)

    Base.metadata.create_all(bind=engine)
    print("[db-init] Tables verified/created.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

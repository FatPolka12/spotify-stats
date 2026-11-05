"""Conexión a PostgreSQL y creación del esquema."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/spotify_stats")
SCHEMA_FILE = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def connect() -> psycopg.Connection:
    """Abre una conexión nueva a la base de datos."""
    return psycopg.connect(DATABASE_URL)


def init_db() -> None:
    """Crea las tablas definidas en sql/schema.sql (si no existen)."""
    with connect() as conn:
        conn.execute(SCHEMA_FILE.read_text())
    print("Esquema creado/verificado correctamente.")


if __name__ == "__main__":
    init_db()

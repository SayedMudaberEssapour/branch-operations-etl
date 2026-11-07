
"""PostgreSQL database connection."""
# Establish a secure database connection using SQLAlchemy and environment variables for credentials.
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()


def get_engine():
    """Create a PostgreSQL SQLAlchemy engine."""
    url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME"),
    )

    return create_engine(url, pool_pre_ping=True)


def test_connection():
    """Verify connectivity to PostgreSQL."""
    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database()")
        )
        print("Connected to:", result.scalar())


if __name__ == "__main__":
    test_connection()

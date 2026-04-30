import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# -------------------------------------------------------------------
# Database URL
# -------------------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://embs:embs@localhost:5433/embs",
)

# -------------------------------------------------------------------
# SQLAlchemy base
# -------------------------------------------------------------------

class Base(DeclarativeBase):
    pass

# -------------------------------------------------------------------
# Engine & session
# -------------------------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    echo=False,          # set True only when debugging SQL
    pool_pre_ping=True,  # avoids stale connections
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
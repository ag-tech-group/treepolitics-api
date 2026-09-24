from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    # Check pooled connections before use: a DB restart (e.g. Cloud SQL maintenance)
    # closes them server-side, and reusing one fails the request with a 500.
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """Dependency that provides an async database session."""
    async with async_session_maker() as session:
        yield session

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.core.config.settings import settings

engine = create_async_engine(
    settings.db_url_async,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_size=10,
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
)
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    future=True,
    class_=AsyncSession,
)

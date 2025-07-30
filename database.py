import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings
import logging

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass


# -- Build the asyncpg PostgreSQL URL using provided credentials --
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Remove SSL parameters that cause issues with asyncpg
if "sslmode" in database_url:
    from urllib.parse import urlparse, urlunparse, parse_qs
    parsed = urlparse(database_url)
    # Remove sslmode parameter from query
    query_params = parse_qs(parsed.query)
    query_params.pop('sslmode', None)
    query_params.pop('sslcert', None)
    query_params.pop('sslkey', None)
    query_params.pop('sslrootcert', None)
    
    # Reconstruct URL without SSL parameters
    new_query = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
    new_parsed = parsed._replace(query=new_query)
    database_url = urlunparse(new_parsed)

engine = create_async_engine(
    database_url,
    echo=False,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=300
)

AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db():
    """Database session dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            # Import models to ensure they're registered
            from models import Shop, Brand, Category, Product, ProductVariant
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

async def close_db():
    """Close database connections"""
    await engine.dispose()

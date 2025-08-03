import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings
import logging
import os

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass


# -- Build the asyncpg PostgreSQL URL using provided credentials --
database_url = settings.DATABASE_URL

# Log the original database URL for debugging (without sensitive info)
if database_url:
    # Mask password in logs
    masked_url = database_url
    if "@" in masked_url:
        parts = masked_url.split("@")
        if ":" in parts[0]:
            protocol_user = parts[0].split(":")
            if len(protocol_user) >= 3:  # postgresql://user:pass@host
                masked_url = f"{protocol_user[0]}:{protocol_user[1]}:***@{parts[1]}"
    logger.info(f"Database URL format: {masked_url}")
else:
    logger.warning("DATABASE_URL is not set, using default local database")
    database_url = "postgresql://postgres:123123@0.0.0.0:5432/postgres"

# Convert to asyncpg format
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    logger.info("Converted to asyncpg format")

# Handle SSL parameters for cloud deployments
if "sslmode" in database_url or "ssl=" in database_url:
    from urllib.parse import urlparse, urlunparse, parse_qs
    try:
        parsed = urlparse(database_url)
        # Remove SSL parameters from query
        query_params = parse_qs(parsed.query)
        ssl_params_removed = []
        
        for ssl_param in ['sslmode', 'sslcert', 'sslkey', 'sslrootcert', 'ssl']:
            if ssl_param in query_params:
                ssl_params_removed.append(ssl_param)
                query_params.pop(ssl_param, None)
        
        if ssl_params_removed:
            logger.info(f"Removed SSL parameters: {ssl_params_removed}")
        
        # Reconstruct URL without SSL parameters
        new_query = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
        new_parsed = parsed._replace(query=new_query)
        database_url = urlunparse(new_parsed)
    except Exception as e:
        logger.warning(f"Error processing SSL parameters: {e}")

logger.info("Final database URL prepared")

try:
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=300
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    logger.error(f"Database URL (masked): {masked_url}")
    raise

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

#!/usr/bin/env python3
"""
Database initialization script for Render deployment
"""

import asyncio
import logging
from database import init_db
from config import settings

# Set up logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """Initialize the database"""
    try:
        logger.info("Starting database initialization...")
        logger.info(f"Database URL format: {settings.DATABASE_URL[:20]}...")
        
        await init_db()
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 
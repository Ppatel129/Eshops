#!/usr/bin/env python3
"""
Migration script to fix duplicate categories in the database.
This script should be run before deploying to production to clean up existing duplicate data.
"""

import asyncio
import logging
from sqlalchemy import text
from database import AsyncSessionLocal, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_duplicate_categories():
    """Fix duplicate categories by keeping the first occurrence and removing duplicates"""
    async with AsyncSessionLocal() as db:
        try:
            # Find and remove duplicate categories
            # Keep the first occurrence (lowest ID) and delete the rest
            delete_query = text("""
                DELETE FROM categories 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM categories 
                    GROUP BY normalized_name, path
                )
                AND id IN (
                    SELECT id 
                    FROM categories c1 
                    WHERE EXISTS (
                        SELECT 1 
                        FROM categories c2 
                        WHERE c2.normalized_name = c1.normalized_name 
                        AND c2.path = c1.path 
                        AND c2.id < c1.id
                    )
                )
            """)
            
            result = await db.execute(delete_query)
            deleted_count = result.rowcount
            await db.commit()
            
            logger.info(f"Deleted {deleted_count} duplicate categories")
            
            # Update product references to point to the remaining categories
            update_query = text("""
                UPDATE products 
                SET category_id = (
                    SELECT MIN(c.id) 
                    FROM categories c 
                    WHERE c.normalized_name = (
                        SELECT normalized_name 
                        FROM categories 
                        WHERE id = products.category_id
                    )
                    AND c.path = (
                        SELECT path 
                        FROM categories 
                        WHERE id = products.category_id
                    )
                )
                WHERE category_id IN (
                    SELECT c1.id 
                    FROM categories c1 
                    WHERE EXISTS (
                        SELECT 1 
                        FROM categories c2 
                        WHERE c2.normalized_name = c1.normalized_name 
                        AND c2.path = c1.path 
                        AND c2.id < c1.id
                    )
                )
            """)
            
            result = await db.execute(update_query)
            updated_count = result.rowcount
            await db.commit()
            
            logger.info(f"Updated {updated_count} product category references")
            
        except Exception as e:
            logger.error(f"Error fixing duplicate categories: {e}")
            await db.rollback()
            raise

async def main():
    """Main migration function"""
    logger.info("Starting duplicate category cleanup...")
    
    try:
        await fix_duplicate_categories()
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main()) 
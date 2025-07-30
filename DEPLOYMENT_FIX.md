# Database Error Fix for Render.com Deployment

## Problem
The error `Multiple rows were found when one or none was required` occurs because the database contains duplicate categories with the same `normalized_name`, but the code was using `scalar_one_or_none()` which expects only one result.

## Solution Applied

### 1. Fixed the Code Logic
- **File:** `feed_scheduler.py`
- **Changes:**
  - Modified `get_or_create_category()` to handle multiple results gracefully
  - Modified `process_product_variants()` to handle multiple variants
  - Added fallback logic to use the first existing category if multiple exist

### 2. Added Database Constraint
- **File:** `models.py`
- **Changes:**
  - Added unique constraint on `(normalized_name, path)` for categories
  - This prevents future duplicate categories

### 3. Migration Script
- **File:** `migration_fix_duplicates.py`
- **Purpose:** Clean up existing duplicate data before deployment

## Deployment Steps

### Step 1: Run Migration Script (if deploying to existing database)
```bash
# Connect to your database and run:
python migration_fix_duplicates.py
```

### Step 2: Deploy Updated Code
The updated code will now handle duplicate categories gracefully by:
1. First trying to find a category by both `normalized_name` and `path`
2. If not found, looking for any category with the same `normalized_name` and using the first one
3. Only creating a new category if no matching category exists

### Step 3: Monitor Logs
After deployment, monitor the logs to ensure the error no longer occurs.

## Code Changes Summary

### `feed_scheduler.py` - `get_or_create_category()`
```python
# Before: Used scalar_one_or_none() which failed with multiple results
query = select(Category).where(Category.normalized_name == normalized_name)
result = await db.execute(query)
category = result.scalar_one_or_none()

# After: Handle multiple results gracefully
query = select(Category).where(
    Category.normalized_name == normalized_name,
    Category.path == path
)
result = await db.execute(query)
category = result.scalar_one_or_none()

if not category:
    # Try just by normalized_name and take the first one
    query = select(Category).where(Category.normalized_name == normalized_name)
    result = await db.execute(query)
    categories = result.scalars().all()
    
    if categories:
        category = categories[0]  # Use first existing category
    else:
        # Create new category
```

### `models.py` - Category Model
```python
# Added unique constraint to prevent future duplicates
__table_args__ = (
    Index('idx_categories_name', 'name'),
    Index('idx_categories_path', 'path'),
    Index('idx_categories_normalized', 'normalized_name'),
    Index('idx_categories_unique', 'normalized_name', 'path', unique=True),  # NEW
)
```

## Expected Result
- No more "Multiple rows were found" errors
- Feed processing will continue even with duplicate categories
- Future duplicate categories will be prevented by the unique constraint
- Existing duplicate data will be cleaned up by the migration script

## Rollback Plan
If issues occur:
1. Revert to previous code version
2. Remove the unique constraint from models.py
3. The migration script can be run again if needed 
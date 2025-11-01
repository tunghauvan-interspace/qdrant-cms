"""
Database migration script for comprehensive document features.

This script adds new tables and columns to support:
- Document versioning
- Document sharing with user permissions
- Document analytics tracking
- Document favorites/bookmarks
"""

import asyncio
from database import engine, Base
from app.models.models import (
    Document, DocumentChunk, Tag, User,
    DocumentVersion, DocumentShare, DocumentAnalytics, DocumentFavorite
)
from sqlalchemy import text


async def upgrade():
    """Create new tables and add new columns to existing tables"""
    print("Starting database migration...")
    
    async with engine.begin() as conn:
        # Check if we're using SQLite
        result = await conn.execute(text("SELECT sqlite_version()"))
        sqlite_version = result.scalar()
        print(f"SQLite version: {sqlite_version}")
        
        # Add new columns to documents table if they don't exist
        print("\n1. Checking documents table for new columns...")
        try:
            # Check if last_modified column exists
            result = await conn.execute(
                text("SELECT COUNT(*) FROM pragma_table_info('documents') WHERE name='last_modified'")
            )
            if result.scalar() == 0:
                print("   Adding last_modified column to documents table...")
                await conn.execute(text(
                    "ALTER TABLE documents ADD COLUMN last_modified TIMESTAMP"
                ))
                # Set initial values
                await conn.execute(text(
                    "UPDATE documents SET last_modified = upload_date WHERE last_modified IS NULL"
                ))
            else:
                print("   last_modified column already exists")
            
            # Check if version column exists
            result = await conn.execute(
                text("SELECT COUNT(*) FROM pragma_table_info('documents') WHERE name='version'")
            )
            if result.scalar() == 0:
                print("   Adding version column to documents table...")
                await conn.execute(text(
                    "ALTER TABLE documents ADD COLUMN version INTEGER DEFAULT 1"
                ))
                # Set initial values
                await conn.execute(text(
                    "UPDATE documents SET version = 1 WHERE version IS NULL"
                ))
            else:
                print("   version column already exists")
        except Exception as e:
            print(f"   Error adding columns to documents table: {e}")
            print("   Continuing with table creation...")
        
        # Create new tables
        print("\n2. Creating new tables...")
        
        # Check which tables already exist
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        existing_tables = {row[0] for row in result.fetchall()}
        print(f"   Existing tables: {existing_tables}")
        
        # Create all tables (will skip existing ones)
        print("   Creating/updating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        
        # Verify new tables were created
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        new_tables = {row[0] for row in result.fetchall()}
        created_tables = new_tables - existing_tables
        
        if created_tables:
            print(f"   Created new tables: {created_tables}")
        else:
            print("   All tables already existed")
    
    print("\n✅ Database migration completed successfully!")


async def verify():
    """Verify the migration was successful"""
    print("\nVerifying database schema...")
    
    async with engine.begin() as conn:
        # Check documents table structure
        result = await conn.execute(
            text("PRAGMA table_info(documents)")
        )
        columns = result.fetchall()
        print("\nDocuments table columns:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Check new tables exist
        expected_tables = [
            'document_versions',
            'document_shares',
            'document_analytics',
            'document_favorites'
        ]
        
        print("\nNew tables:")
        for table_name in expected_tables:
            result = await conn.execute(
                text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            )
            exists = result.scalar()
            status = "✅" if exists else "❌"
            print(f"   {status} {table_name}")
    
    print("\n✅ Verification complete!")


async def main():
    """Run the migration and verification"""
    try:
        await upgrade()
        await verify()
        print("\n" + "="*60)
        print("Migration successful! Your database is now up to date.")
        print("="*60)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

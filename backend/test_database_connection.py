#!/usr/bin/env python3
"""
Test database connection and table creation.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test database connection and table creation."""
    try:
        from app.core.database import engine, SessionLocal
        from sqlalchemy import text
        
        print("Testing database connection...")
        
        # Test basic connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✅ Database connection successful: {result.fetchone()}")
        
        # Test table creation
        with engine.connect() as conn:
            # Create table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS rag_query_history (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    sources_count INTEGER NOT NULL DEFAULT 0,
                    processing_time REAL NOT NULL DEFAULT 0.0,
                    token_count INTEGER NOT NULL DEFAULT 0,
                    query_metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✅ Table created successfully")
            
            # Test table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='rag_query_history'"))
            table_exists = result.fetchone()
            if table_exists:
                print("✅ Table exists in database")
            else:
                print("❌ Table not found in database")
            
            # Test insert
            conn.execute(text("""
                INSERT INTO rag_query_history (id, query, mode, answer, sources_count, processing_time, token_count)
                VALUES ('test-id', 'test query', 'hybrid', 'test answer', 0, 0.1, 10)
            """))
            conn.commit()
            print("✅ Test insert successful")
            
            # Test select
            result = conn.execute(text("SELECT COUNT(*) FROM rag_query_history"))
            count = result.fetchone()[0]
            print(f"✅ Table has {count} records")
            
            # Clean up test data
            conn.execute(text("DELETE FROM rag_query_history WHERE id = 'test-id'"))
            conn.commit()
            print("✅ Test cleanup successful")
        
        # Test SQLAlchemy session
        print("\nTesting SQLAlchemy session...")
        db = SessionLocal()
        try:
            # Test with SQLAlchemy
            result = db.execute(text("SELECT COUNT(*) FROM rag_query_history"))
            count = result.fetchone()[0]
            print(f"✅ SQLAlchemy session works: {count} records")
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_connection()
    if success:
        print("\n🎉 All database tests passed!")
    else:
        print("\n⚠️ Database tests failed!")
    sys.exit(0 if success else 1)
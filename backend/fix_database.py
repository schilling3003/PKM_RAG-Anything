#!/usr/bin/env python3
"""
Fix database tables.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

def create_rag_table():
    """Create RAG query history table."""
    with engine.connect() as conn:
        # Create RAG query history table
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
        
        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rag_history_mode 
            ON rag_query_history(mode)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rag_history_created 
            ON rag_query_history(created_at)
        """))
        
        conn.commit()
        print("✅ RAG query history table created successfully")

if __name__ == "__main__":
    create_rag_table()
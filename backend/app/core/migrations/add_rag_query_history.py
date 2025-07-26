"""
Add RAG query history table migration.
"""

from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """Add RAG query history table."""
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
        
        # Create indexes for better query performance
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rag_history_mode 
            ON rag_query_history(mode)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rag_history_created 
            ON rag_query_history(created_at)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rag_history_processing_time 
            ON rag_query_history(processing_time)
        """))
        
        conn.commit()
        print("✅ RAG query history table created successfully")


def downgrade():
    """Remove RAG query history table."""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS rag_query_history"))
        conn.commit()
        print("✅ RAG query history table removed successfully")


def run_migration():
    """Run the migration."""
    upgrade()


if __name__ == "__main__":
    upgrade()
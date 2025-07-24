"""
Database migration utilities.
"""

import os
from typing import List, Dict, Any
from sqlalchemy import text
from app.core.database import engine, DatabaseManager
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MigrationManager:
    """Database migration manager."""
    
    def __init__(self):
        self.migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
        os.makedirs(self.migrations_dir, exist_ok=True)
    
    def run_migrations(self):
        """Run all pending migrations."""
        try:
            # Initialize database first
            DatabaseManager.init_database()
            
            # Create migration tracking table
            self._create_migration_table()
            
            # Get applied migrations
            applied_migrations = self._get_applied_migrations()
            
            # Get available migrations
            available_migrations = self._get_available_migrations()
            
            # Run pending migrations
            pending_migrations = [
                m for m in available_migrations 
                if m not in applied_migrations
            ]
            
            if pending_migrations:
                logger.info(f"Running {len(pending_migrations)} pending migrations")
                
                for migration in pending_migrations:
                    self._run_migration(migration)
                    self._mark_migration_applied(migration)
                    logger.info(f"Applied migration: {migration}")
            else:
                logger.info("No pending migrations")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def _create_migration_table(self):
        """Create migration tracking table."""
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
    
    def _get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations."""
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT version FROM schema_migrations ORDER BY version"
            ))
            return [row[0] for row in result]
    
    def _get_available_migrations(self) -> List[str]:
        """Get list of available migration files."""
        migrations = []
        if os.path.exists(self.migrations_dir):
            for filename in os.listdir(self.migrations_dir):
                if filename.endswith('.sql'):
                    migrations.append(filename[:-4])  # Remove .sql extension
        return sorted(migrations)
    
    def _run_migration(self, migration: str):
        """Run a specific migration."""
        migration_file = os.path.join(self.migrations_dir, f"{migration}.sql")
        
        if not os.path.exists(migration_file):
            raise FileNotFoundError(f"Migration file not found: {migration_file}")
        
        with open(migration_file, 'r') as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        with engine.connect() as conn:
            for statement in statements:
                conn.execute(text(statement))
            conn.commit()
    
    def _mark_migration_applied(self, migration: str):
        """Mark migration as applied."""
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO schema_migrations (version) VALUES (:version)"
            ), {"version": migration})
            conn.commit()
    
    def create_migration(self, name: str, sql_content: str) -> str:
        """Create a new migration file."""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        migration_name = f"{timestamp}_{name}"
        migration_file = os.path.join(self.migrations_dir, f"{migration_name}.sql")
        
        with open(migration_file, 'w') as f:
            f.write(f"-- Migration: {migration_name}\n")
            f.write(f"-- Created: {datetime.now().isoformat()}\n\n")
            f.write(sql_content)
        
        logger.info(f"Created migration: {migration_file}")
        return migration_name


# Create initial migration for indexes and optimizations
INITIAL_MIGRATION_SQL = """
-- Create additional indexes for better performance

-- Notes full-text search indexes (if not created by triggers)
CREATE INDEX IF NOT EXISTS idx_notes_content_search ON notes(content);

-- Document processing optimization indexes
CREATE INDEX IF NOT EXISTS idx_documents_type_status ON documents(file_type, processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_size ON documents(file_size);

-- Knowledge graph optimization indexes
CREATE INDEX IF NOT EXISTS idx_kg_nodes_composite ON kg_nodes(node_type, label);
CREATE INDEX IF NOT EXISTS idx_kg_edges_composite ON kg_edges(relation_type, weight);

-- Search history optimization
CREATE INDEX IF NOT EXISTS idx_search_mode_time ON search_history(search_mode, created_at);

-- Background tasks optimization
CREATE INDEX IF NOT EXISTS idx_tasks_type_status ON background_tasks(task_type, status);
CREATE INDEX IF NOT EXISTS idx_tasks_progress ON background_tasks(progress);

-- Create views for common queries
CREATE VIEW IF NOT EXISTS active_documents AS
SELECT * FROM documents 
WHERE processing_status IN ('queued', 'processing', 'completed');

CREATE VIEW IF NOT EXISTS recent_notes AS
SELECT * FROM notes 
ORDER BY updated_at DESC 
LIMIT 100;

CREATE VIEW IF NOT EXISTS graph_summary AS
SELECT 
    node_type,
    COUNT(*) as node_count
FROM kg_nodes 
GROUP BY node_type;
"""


def initialize_migrations():
    """Initialize migration system with initial migration."""
    migration_manager = MigrationManager()
    
    # Create initial migration if it doesn't exist
    initial_migration_file = os.path.join(
        migration_manager.migrations_dir, 
        "001_initial_indexes.sql"
    )
    
    if not os.path.exists(initial_migration_file):
        with open(initial_migration_file, 'w') as f:
            f.write(INITIAL_MIGRATION_SQL)
        logger.info("Created initial migration file")
    
    return migration_manager
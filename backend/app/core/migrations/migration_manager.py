"""
Database migration manager.
"""

import os
import sqlite3
import structlog
from pathlib import Path
from typing import List, Tuple

from app.core.config import settings

logger = structlog.get_logger(__name__)


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migrations_dir = Path(__file__).parent
        
    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def _create_migrations_table(self) -> None:
        """Create migrations tracking table."""
        with self._get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def _get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations."""
        with self._get_db_connection() as conn:
            cursor = conn.execute("SELECT filename FROM migrations ORDER BY id")
            return [row[0] for row in cursor.fetchall()]
    
    def _mark_migration_applied(self, filename: str) -> None:
        """Mark migration as applied."""
        with self._get_db_connection() as conn:
            conn.execute("INSERT INTO migrations (filename) VALUES (?)", (filename,))
            conn.commit()
    
    def _get_migration_files(self) -> List[Tuple[str, Path]]:
        """Get list of migration files."""
        migrations = []
        
        # SQL migrations
        for sql_file in self.migrations_dir.glob("*.sql"):
            migrations.append((sql_file.name, sql_file))
        
        # Python migrations
        for py_file in self.migrations_dir.glob("*.py"):
            if py_file.name not in ["__init__.py", "migration_manager.py"]:
                migrations.append((py_file.name, py_file))
        
        return sorted(migrations)
    
    def _run_sql_migration(self, file_path: Path) -> bool:
        """Run SQL migration."""
        try:
            with open(file_path, 'r') as f:
                sql_content = f.read()
            
            with self._get_db_connection() as conn:
                conn.executescript(sql_content)
                conn.commit()
            
            logger.info("Applied SQL migration", filename=file_path.name)
            return True
            
        except Exception as e:
            logger.error("Failed to apply SQL migration", filename=file_path.name, error=str(e))
            return False
    
    def _run_python_migration(self, file_path: Path) -> bool:
        """Run Python migration."""
        try:
            # Import and run Python migration
            import importlib.util
            spec = importlib.util.spec_from_file_location("migration", file_path)
            migration_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration_module)
            
            if hasattr(migration_module, 'run_migration'):
                migration_module.run_migration()
                logger.info("Applied Python migration", filename=file_path.name)
                return True
            else:
                logger.error("Python migration missing run_migration function", filename=file_path.name)
                return False
                
        except Exception as e:
            logger.error("Failed to apply Python migration", filename=file_path.name, error=str(e))
            return False
    
    def run_migrations(self) -> bool:
        """Run all pending migrations."""
        try:
            # Ensure database directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Create migrations table
            self._create_migrations_table()
            
            # Get applied migrations
            applied_migrations = self._get_applied_migrations()
            
            # Get all migration files
            migration_files = self._get_migration_files()
            
            success = True
            migrations_applied = 0
            
            for filename, file_path in migration_files:
                if filename not in applied_migrations:
                    logger.info("Running migration", filename=filename)
                    
                    if filename.endswith('.sql'):
                        migration_success = self._run_sql_migration(file_path)
                    elif filename.endswith('.py'):
                        migration_success = self._run_python_migration(file_path)
                    else:
                        logger.warning("Unknown migration file type", filename=filename)
                        continue
                    
                    if migration_success:
                        self._mark_migration_applied(filename)
                        migrations_applied += 1
                    else:
                        success = False
                        break
            
            if success:
                if migrations_applied > 0:
                    logger.info("Migrations completed", applied_count=migrations_applied)
                else:
                    logger.info("No pending migrations")
            
            return success
            
        except Exception as e:
            logger.error("Migration process failed", error=str(e))
            return False


def initialize_migrations() -> MigrationManager:
    """Initialize migration manager."""
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    return MigrationManager(db_path)
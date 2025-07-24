"""
Database connection and session management.
"""

import os
from typing import Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import sqlite3

from app.core.config import settings
from app.models.database import Base


# SQLite optimization for WAL mode and performance
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for optimal performance."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Optimize for read-heavy workloads
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")  # 10MB cache
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory map
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        
        cursor.close()


# Create database engine
def create_database_engine():
    """Create SQLAlchemy engine with optimized settings."""
    
    # Ensure database directory exists
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
            "timeout": 30
        },
        echo=settings.DEBUG,  # Log SQL queries in debug mode
        future=True
    )
    
    return engine


# Create engine and session factory
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseManager:
    """Database management utilities."""
    
    @staticmethod
    def init_database():
        """Initialize database with tables and indexes."""
        create_tables()
        
        # Create additional indexes if needed
        with engine.connect() as conn:
            # Full-text search indexes for SQLite
            try:
                conn.execute(text("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                        id, title, content, content='notes', content_rowid='rowid'
                    )
                """))
                
                conn.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS notes_fts_insert AFTER INSERT ON notes BEGIN
                        INSERT INTO notes_fts(rowid, id, title, content) 
                        VALUES (new.rowid, new.id, new.title, new.content);
                    END
                """))
                
                conn.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS notes_fts_delete AFTER DELETE ON notes BEGIN
                        INSERT INTO notes_fts(notes_fts, rowid, id, title, content) 
                        VALUES('delete', old.rowid, old.id, old.title, old.content);
                    END
                """))
                
                conn.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS notes_fts_update AFTER UPDATE ON notes BEGIN
                        INSERT INTO notes_fts(notes_fts, rowid, id, title, content) 
                        VALUES('delete', old.rowid, old.id, old.title, old.content);
                        INSERT INTO notes_fts(rowid, id, title, content) 
                        VALUES (new.rowid, new.id, new.title, new.content);
                    END
                """))
                
                conn.commit()
                
            except Exception as e:
                print(f"Warning: Could not create FTS indexes: {e}")
    
    @staticmethod
    def get_database_info():
        """Get database information and statistics."""
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA database_list")).fetchall()
            tables = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
            
            return {
                "databases": [dict(row._mapping) for row in result],
                "tables": [row[0] for row in tables],
                "engine": str(engine.url)
            }
    
    @staticmethod
    def vacuum_database():
        """Vacuum database to reclaim space and optimize."""
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("VACUUM"))
            conn.execute(text("PRAGMA optimize"))
    
    @staticmethod
    def backup_database(backup_path: str):
        """Create database backup."""
        import shutil
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        shutil.copy2(db_path, backup_path)
        
        # Also backup WAL and SHM files if they exist
        wal_path = db_path + "-wal"
        shm_path = db_path + "-shm"
        
        if os.path.exists(wal_path):
            shutil.copy2(wal_path, backup_path + "-wal")
        if os.path.exists(shm_path):
            shutil.copy2(shm_path, backup_path + "-shm")
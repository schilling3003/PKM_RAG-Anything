"""
File storage management system for document uploads.
"""

import os
import uuid
import shutil
import hashlib
from typing import Dict, Any, Optional, List
from pathlib import Path
import aiofiles
from fastapi import UploadFile
import logging

from app.core.config import settings
from app.core.exceptions import FileStorageError

logger = logging.getLogger(__name__)


class FileManager:
    """
    File storage management system for handling document uploads and storage.
    """
    
    def __init__(self):
        """Initialize file manager."""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.processed_dir = Path(settings.PROCESSED_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE
        
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Save uploaded file to storage.
        
        Args:
            file: FastAPI UploadFile object
            document_id: Optional document ID, will generate if not provided
            
        Returns:
            Dict containing file information
        """
        try:
            # Generate document ID if not provided
            if not document_id:
                document_id = str(uuid.uuid4())
            
            # Validate file
            validation_result = await self._validate_upload(file)
            if not validation_result["valid"]:
                raise FileStorageError(validation_result["error"])
            
            # Generate safe filename
            safe_filename = self._generate_safe_filename(file.filename, document_id)
            file_path = self.upload_dir / safe_filename
            
            # Save file
            await self._save_file_to_disk(file, file_path)
            
            # Calculate file hash for deduplication
            file_hash = await self._calculate_file_hash(file_path)
            
            # Get file metadata
            file_stats = file_path.stat()
            
            result = {
                "document_id": document_id,
                "original_filename": file.filename,
                "safe_filename": safe_filename,
                "file_path": str(file_path),
                "file_size": file_stats.st_size,
                "file_type": file.content_type,
                "file_hash": file_hash,
                "created_at": file_stats.st_ctime
            }
            
            logger.info(f"File saved successfully: {safe_filename} ({file_stats.st_size} bytes)")
            return result
            
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            raise FileStorageError(f"File save failed: {str(e)}")
    
    async def _validate_upload(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file."""
        try:
            # Check if file is provided
            if not file or not file.filename:
                return {"valid": False, "error": "No file provided"}
            
            # Check file size by reading content
            content = await file.read()
            file_size = len(content)
            
            # Reset file pointer
            await file.seek(0)
            
            if file_size == 0:
                return {"valid": False, "error": "File is empty"}
            
            if file_size > self.max_file_size:
                return {
                    "valid": False,
                    "error": f"File too large: {file_size} bytes (max: {self.max_file_size})"
                }
            
            # Check file extension
            allowed_extensions = {
                '.pdf', '.txt', '.md', '.doc', '.docx',
                '.jpg', '.jpeg', '.png', '.gif', '.bmp',
                '.mp3', '.wav', '.m4a', '.flac',
                '.mp4', '.avi', '.mov', '.mkv'
            }
            
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                logger.warning(f"Potentially unsupported file extension: {file_ext}")
                # Don't reject, just warn
            
            return {
                "valid": True,
                "file_size": file_size,
                "file_extension": file_ext
            }
            
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    def _generate_safe_filename(self, original_filename: str, document_id: str) -> str:
        """Generate safe filename for storage."""
        # Get file extension
        file_ext = Path(original_filename).suffix.lower()
        
        # Create safe filename with document ID
        safe_name = f"{document_id}_{self._sanitize_filename(original_filename)}"
        
        # Ensure it has the correct extension
        if not safe_name.endswith(file_ext):
            safe_name = f"{safe_name}{file_ext}"
        
        return safe_name
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # Remove multiple underscores
        while '__' in filename:
            filename = filename.replace('__', '_')
        
        # Limit length
        name_part = Path(filename).stem
        ext_part = Path(filename).suffix
        
        if len(name_part) > 100:
            name_part = name_part[:100]
        
        return f"{name_part}{ext_part}"
    
    async def _save_file_to_disk(self, file: UploadFile, file_path: Path):
        """Save file to disk asynchronously."""
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                # Read and write in chunks to handle large files
                chunk_size = 8192
                while chunk := await file.read(chunk_size):
                    await f.write(chunk)
                    
        except Exception as e:
            # Clean up partial file if save failed
            if file_path.exists():
                file_path.unlink()
            raise FileStorageError(f"Failed to save file to disk: {str(e)}")
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for deduplication."""
        try:
            hash_sha256 = hashlib.sha256()
            async with aiofiles.open(file_path, 'rb') as f:
                while chunk := await f.read(8192):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
            
        except Exception as e:
            logger.warning(f"Failed to calculate file hash: {e}")
            return ""
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def move_file(self, source_path: str, destination_path: str) -> bool:
        """
        Move file from source to destination.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            True if moved successfully, False otherwise
        """
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source), str(destination))
            logger.info(f"File moved: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move file {source_path} -> {destination_path}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dict containing file information or None if file doesn't exist
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stats = path.stat()
            return {
                "file_path": str(path),
                "file_name": path.name,
                "file_size": stats.st_size,
                "created_at": stats.st_ctime,
                "modified_at": stats.st_mtime,
                "is_file": path.is_file(),
                "is_directory": path.is_dir()
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None
    
    def list_files(self, directory: Optional[str] = None, pattern: str = "*") -> List[Dict[str, Any]]:
        """
        List files in directory.
        
        Args:
            directory: Directory to list (defaults to upload directory)
            pattern: File pattern to match (e.g., "*.pdf")
            
        Returns:
            List of file information dictionaries
        """
        try:
            if directory:
                dir_path = Path(directory)
            else:
                dir_path = self.upload_dir
            
            if not dir_path.exists():
                return []
            
            files = []
            for file_path in dir_path.glob(pattern):
                if file_path.is_file():
                    file_info = self.get_file_info(str(file_path))
                    if file_info:
                        files.append(file_info)
            
            return sorted(files, key=lambda x: x["modified_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            return []
    
    def cleanup_old_files(self, days_old: int = 30) -> Dict[str, Any]:
        """
        Clean up files older than specified days.
        
        Args:
            days_old: Number of days after which files are considered old
            
        Returns:
            Dict containing cleanup results
        """
        try:
            import time
            
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            deleted_count = 0
            total_size_freed = 0
            errors = []
            
            for file_path in self.upload_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        stats = file_path.stat()
                        if stats.st_mtime < cutoff_time:
                            file_size = stats.st_size
                            file_path.unlink()
                            deleted_count += 1
                            total_size_freed += file_size
                            logger.info(f"Deleted old file: {file_path}")
                            
                    except Exception as e:
                        errors.append(f"Failed to delete {file_path}: {str(e)}")
            
            return {
                "deleted_count": deleted_count,
                "total_size_freed": total_size_freed,
                "errors": errors,
                "success": len(errors) == 0
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {
                "deleted_count": 0,
                "total_size_freed": 0,
                "errors": [str(e)],
                "success": False
            }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics."""
        try:
            upload_size = self._get_directory_size(self.upload_dir)
            processed_size = self._get_directory_size(self.processed_dir)
            
            upload_count = len(list(self.upload_dir.rglob("*")))
            processed_count = len(list(self.processed_dir.rglob("*")))
            
            return {
                "upload_directory": {
                    "path": str(self.upload_dir),
                    "size_bytes": upload_size,
                    "file_count": upload_count
                },
                "processed_directory": {
                    "path": str(self.processed_dir),
                    "size_bytes": processed_size,
                    "file_count": processed_count
                },
                "total_size_bytes": upload_size + processed_size,
                "max_file_size": self.max_file_size
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}
    
    def _get_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory."""
        total_size = 0
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.error(f"Error calculating directory size: {e}")
        
        return total_size


# Global instance
file_manager = FileManager()
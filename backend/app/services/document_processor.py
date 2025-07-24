"""
Document processing service with RAG-Anything and MinerU 2.0 integration.
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import mimetypes

from app.core.config import settings
from app.core.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Document processor using RAG-Anything with MinerU 2.0 integration.
    """
    
    def __init__(self):
        """Initialize the document processor."""
        self.rag_anything = None
        self.mineru_config = {
            "parse_method": "auto",  # MinerU auto-detection
            "device": settings.MINERU_DEVICE,
            "backend": settings.MINERU_BACKEND,
            "lang": settings.MINERU_LANG
        }
        self._initialize_rag_anything()
    
    def _initialize_rag_anything(self):
        """Initialize RAG-Anything with user-configurable settings."""
        try:
            from raganything import RAGAnything
            
            # Ensure storage directory exists
            os.makedirs(settings.RAG_STORAGE_DIR, exist_ok=True)
            
            # RAG-Anything initialization - check the actual API
            self.rag_anything = RAGAnything(
                llm_model_func=self._get_llm_function(),
                vision_model_func=self._get_vision_function(),
                embedding_func=self._get_embedding_function()
            )
            
            logger.info("RAG-Anything initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import RAG-Anything: {e}")
            raise DocumentProcessingError("RAG-Anything not available")
        except Exception as e:
            logger.error(f"Failed to initialize RAG-Anything: {e}")
            raise DocumentProcessingError(f"RAG-Anything initialization failed: {e}")
    
    def _get_llm_function(self):
        """Get user-configurable LLM function."""
        def llm_func(prompt: str, **kwargs) -> str:
            """LLM function for RAG-Anything."""
            try:
                # Use OpenAI API if configured
                if settings.OPENAI_API_KEY:
                    import openai
                    
                    client = openai.OpenAI(
                        api_key=settings.OPENAI_API_KEY,
                        base_url=settings.OPENAI_BASE_URL
                    )
                    
                    response = client.chat.completions.create(
                        model=settings.LLM_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=kwargs.get("max_tokens", 1000),
                        temperature=kwargs.get("temperature", 0.1)
                    )
                    
                    return response.choices[0].message.content
                else:
                    # Fallback to local processing or mock response
                    logger.warning("No LLM API configured, using fallback")
                    return f"Processed: {prompt[:100]}..."
                    
            except Exception as e:
                logger.error(f"LLM function error: {e}")
                return f"Error processing: {str(e)}"
        
        return llm_func
    
    def _get_vision_function(self):
        """Get user-configurable vision model function."""
        def vision_func(image_path: str, prompt: str = "Describe this image", **kwargs) -> str:
            """Vision model function for image processing."""
            try:
                if settings.OPENAI_API_KEY:
                    import openai
                    import base64
                    
                    # Read and encode image
                    with open(image_path, "rb") as image_file:
                        image_data = base64.b64encode(image_file.read()).decode()
                    
                    client = openai.OpenAI(
                        api_key=settings.OPENAI_API_KEY,
                        base_url=settings.OPENAI_BASE_URL
                    )
                    
                    response = client.chat.completions.create(
                        model=settings.VISION_MODEL,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_data}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=kwargs.get("max_tokens", 500)
                    )
                    
                    return response.choices[0].message.content
                else:
                    logger.warning("No vision model API configured, using fallback")
                    return f"Image description for: {os.path.basename(image_path)}"
                    
            except Exception as e:
                logger.error(f"Vision function error: {e}")
                return f"Error processing image: {str(e)}"
        
        return vision_func
    
    def _get_embedding_function(self):
        """Get user-configurable embedding function."""
        def embedding_func(text: str, **kwargs) -> List[float]:
            """Embedding function for semantic search."""
            try:
                if settings.OPENAI_API_KEY:
                    import openai
                    
                    client = openai.OpenAI(
                        api_key=settings.OPENAI_API_KEY,
                        base_url=settings.OPENAI_BASE_URL
                    )
                    
                    response = client.embeddings.create(
                        model=settings.EMBEDDING_MODEL,
                        input=text
                    )
                    
                    return response.data[0].embedding
                else:
                    # Fallback to simple hash-based embedding (for development)
                    import hashlib
                    hash_obj = hashlib.md5(text.encode())
                    # Create a simple embedding from hash
                    embedding = []
                    for i in range(0, len(hash_obj.hexdigest()), 2):
                        embedding.append(float(int(hash_obj.hexdigest()[i:i+2], 16)) / 255.0)
                    
                    # Pad or truncate to desired dimension
                    while len(embedding) < settings.EMBEDDING_DIM:
                        embedding.extend(embedding[:min(len(embedding), settings.EMBEDDING_DIM - len(embedding))])
                    
                    return embedding[:settings.EMBEDDING_DIM]
                    
            except Exception as e:
                logger.error(f"Embedding function error: {e}")
                # Return zero vector as fallback
                return [0.0] * settings.EMBEDDING_DIM
        
        return embedding_func
    
    async def process_document(self, file_path: str, document_id: str) -> Dict[str, Any]:
        """
        Process a document using RAG-Anything with MinerU 2.0.
        
        Args:
            file_path: Path to the document file
            document_id: Unique identifier for the document
            
        Returns:
            Dict containing processing results
        """
        try:
            if not os.path.exists(file_path):
                raise DocumentProcessingError(f"File not found: {file_path}")
            
            # Determine file type
            file_type = self._get_file_type(file_path)
            file_size = os.path.getsize(file_path)
            
            logger.info(f"Processing {file_type} document: {file_path}")
            
            # Create output directory for this document
            output_dir = os.path.join(settings.PROCESSED_DIR, document_id)
            os.makedirs(output_dir, exist_ok=True)
            
            # Process document with RAG-Anything + MinerU
            result = await self._process_with_rag_anything(
                file_path=file_path,
                output_dir=output_dir,
                file_type=file_type
            )
            
            # Add metadata
            result.update({
                "document_id": document_id,
                "file_path": file_path,
                "file_type": file_type,
                "file_size": file_size,
                "output_dir": output_dir
            })
            
            logger.info(f"Document processing completed for {document_id}")
            return result
            
        except Exception as e:
            logger.error(f"Document processing failed for {document_id}: {e}")
            raise DocumentProcessingError(f"Processing failed: {str(e)}")
    
    async def _process_with_rag_anything(self, file_path: str, output_dir: str, file_type: str) -> Dict[str, Any]:
        """Process document using RAG-Anything with MinerU 2.0."""
        try:
            # Run RAG-Anything processing in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def _sync_process():
                return self.rag_anything.process_document_complete(
                    file_path=file_path,
                    output_dir=output_dir,
                    parse_method=self.mineru_config["parse_method"],
                    device=self.mineru_config["device"],
                    backend=self.mineru_config["backend"],
                    lang=self.mineru_config["lang"]
                )
            
            # Execute in thread pool
            result = await loop.run_in_executor(None, _sync_process)
            
            # Process the result
            processed_result = {
                "extracted_text": result.get("text", ""),
                "images": result.get("images", []),
                "tables": result.get("tables", []),
                "metadata": result.get("metadata", {}),
                "processing_time": result.get("processing_time", 0),
                "success": True
            }
            
            # Handle multimodal content if present
            if result.get("images"):
                processed_result["image_descriptions"] = await self._process_images(
                    result["images"], output_dir
                )
            
            if result.get("tables"):
                processed_result["table_descriptions"] = await self._process_tables(
                    result["tables"], output_dir
                )
            
            # Process audio/video files
            if self._is_audio_video_file(file_path):
                processed_result["audio_transcription"] = await self._process_audio_video(
                    file_path, output_dir
                )
            
            # Enhanced PDF processing
            if file_type == "application/pdf":
                processed_result["pdf_analysis"] = await self._process_pdf_enhanced(
                    file_path, output_dir
                )
            
            return processed_result
            
        except Exception as e:
            logger.error(f"RAG-Anything processing error: {e}")
            return {
                "extracted_text": "",
                "images": [],
                "tables": [],
                "metadata": {},
                "processing_time": 0,
                "success": False,
                "error": str(e)
            }
    
    async def _process_images(self, images: List[Dict], output_dir: str) -> List[Dict]:
        """Process extracted images using specialized image processor."""
        try:
            from app.services.multimodal_processors import MultimodalProcessorFactory
            
            # Create image processor
            image_processor = MultimodalProcessorFactory.create_image_processor(
                self._get_vision_function()
            )
            
            # Extract image paths
            image_paths = []
            for img_data in images:
                img_path = img_data.get("path", "")
                if img_path and os.path.exists(img_path):
                    image_paths.append(img_path)
            
            if not image_paths:
                return []
            
            # Process images in batch
            context = f"Document processing context: Images extracted from document in {output_dir}"
            processed_images = await image_processor.process_image_batch(image_paths, context)
            
            # Combine with original metadata
            image_descriptions = []
            for i, img_data in enumerate(images):
                if i < len(processed_images):
                    processed = processed_images[i]
                    image_descriptions.append({
                        "path": img_data.get("path", ""),
                        "description": processed.get("description", ""),
                        "ocr_text": processed.get("ocr_text", ""),
                        "visual_analysis": processed.get("visual_analysis", ""),
                        "caption": img_data.get("caption", ""),
                        "footnote": img_data.get("footnote", ""),
                        "metadata": processed.get("metadata", {}),
                        "processing_success": processed.get("processing_success", False)
                    })
                else:
                    image_descriptions.append({
                        "path": img_data.get("path", ""),
                        "description": "Image processing failed",
                        "caption": img_data.get("caption", ""),
                        "footnote": img_data.get("footnote", ""),
                        "processing_success": False
                    })
            
            return image_descriptions
            
        except Exception as e:
            logger.error(f"Batch image processing failed: {e}")
            return []
    
    async def _process_tables(self, tables: List[Dict], output_dir: str) -> List[Dict]:
        """Process extracted tables using specialized table processor."""
        try:
            from app.services.multimodal_processors import MultimodalProcessorFactory
            
            # Create table processor
            table_processor = MultimodalProcessorFactory.create_table_processor(
                self._get_llm_function()
            )
            
            # Process tables in batch
            context = f"Document processing context: Tables extracted from document in {output_dir}"
            processed_tables = await table_processor.process_table_batch(tables, context)
            
            # Format results
            table_descriptions = []
            for i, processed in enumerate(processed_tables):
                table_descriptions.append({
                    "html": processed.get("original_html", ""),
                    "csv": processed.get("original_csv", ""),
                    "description": processed.get("analysis", ""),
                    "summary": processed.get("summary", ""),
                    "insights": processed.get("insights", []),
                    "caption": processed.get("caption", ""),
                    "processing_success": processed.get("processing_success", False)
                })
            
            return table_descriptions
            
        except Exception as e:
            logger.error(f"Batch table processing failed: {e}")
            return []
    
    async def batch_process_folder(self, folder_path: str, file_extensions: List[str] = None) -> Dict[str, Any]:
        """
        Process multiple documents in a folder using MinerU 2.0.
        
        Args:
            folder_path: Path to folder containing documents
            file_extensions: List of file extensions to process (e.g., ['.pdf', '.docx'])
            
        Returns:
            Dict containing batch processing results
        """
        try:
            if not os.path.exists(folder_path):
                raise DocumentProcessingError(f"Folder not found: {folder_path}")
            
            # Default file extensions if not specified
            if file_extensions is None:
                file_extensions = ['.pdf', '.docx', '.doc', '.txt', '.md', '.jpg', '.jpeg', '.png']
            
            # Create output directory
            output_dir = os.path.join(settings.PROCESSED_DIR, "batch_" + str(int(asyncio.get_event_loop().time())))
            os.makedirs(output_dir, exist_ok=True)
            
            # Run batch processing in thread pool
            loop = asyncio.get_event_loop()
            
            def _sync_batch_process():
                return self.rag_anything.process_folder_complete(
                    folder_path=folder_path,
                    output_dir=output_dir,
                    file_extensions=file_extensions,
                    recursive=True,
                    max_workers=4  # Parallel processing
                )
            
            result = await loop.run_in_executor(None, _sync_batch_process)
            
            return {
                "success": True,
                "folder_path": folder_path,
                "output_dir": output_dir,
                "processed_files": result.get("processed_files", []),
                "failed_files": result.get("failed_files", []),
                "total_files": result.get("total_files", 0),
                "processing_time": result.get("processing_time", 0)
            }
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "folder_path": folder_path
            }
    
    def _get_file_type(self, file_path: str) -> str:
        """Determine file MIME type."""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"
    
    def _is_audio_video_file(self, file_path: str) -> bool:
        """Check if file is audio or video."""
        file_type = self._get_file_type(file_path)
        return file_type.startswith(('audio/', 'video/'))
    
    async def _process_audio_video(self, file_path: str, output_dir: str) -> Dict[str, Any]:
        """Process audio/video files for transcription."""
        try:
            from app.services.multimodal_processors import MultimodalProcessorFactory
            
            # Create audio processor
            audio_processor = MultimodalProcessorFactory.create_audio_processor()
            
            # Process audio/video file
            context = f"Audio/video file from document processing in {output_dir}"
            result = await audio_processor.process_audio(file_path, context)
            
            return result
            
        except Exception as e:
            logger.error(f"Audio/video processing failed for {file_path}: {e}")
            return {
                "audio_path": file_path,
                "transcription": f"Audio processing failed: {str(e)}",
                "processing_success": False,
                "error": str(e)
            }
    
    async def _process_pdf_enhanced(self, file_path: str, output_dir: str) -> Dict[str, Any]:
        """Enhanced PDF processing with detailed analysis."""
        try:
            from app.services.multimodal_processors import MultimodalProcessorFactory
            
            # Create PDF processor
            pdf_processor = MultimodalProcessorFactory.create_pdf_processor()
            
            # Process PDF file
            context = f"PDF document processing in {output_dir}"
            result = await pdf_processor.process_pdf(file_path, context)
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced PDF processing failed for {file_path}: {e}")
            return {
                "pdf_path": file_path,
                "text_content": f"PDF processing failed: {str(e)}",
                "processing_success": False,
                "error": str(e)
            }
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate uploaded file before processing.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Dict containing validation results
        """
        try:
            if not os.path.exists(file_path):
                return {"valid": False, "error": "File not found"}
            
            file_size = os.path.getsize(file_path)
            if file_size > settings.MAX_FILE_SIZE:
                return {
                    "valid": False, 
                    "error": f"File too large: {file_size} bytes (max: {settings.MAX_FILE_SIZE})"
                }
            
            if file_size == 0:
                return {"valid": False, "error": "File is empty"}
            
            file_type = self._get_file_type(file_path)
            
            # Check if file type is supported
            supported_types = [
                "application/pdf",
                "text/plain",
                "text/markdown",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "image/jpeg",
                "image/png",
                "image/gif",
                "audio/mpeg",
                "audio/wav",
                "video/mp4",
                "video/avi"
            ]
            
            if file_type not in supported_types:
                logger.warning(f"Unsupported file type: {file_type}")
                # Don't reject, but warn - MinerU might still handle it
            
            return {
                "valid": True,
                "file_type": file_type,
                "file_size": file_size,
                "supported": file_type in supported_types
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}


# Global instance
document_processor = DocumentProcessor()
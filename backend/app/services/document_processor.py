"""
Document processing service with RAG-Anything and MinerU 2.0 integration.
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import mimetypes
import structlog

from app.core.config import settings
from app.core.exceptions import DocumentProcessingError, ExternalServiceError
from app.core.service_health import service_health_monitor
from app.core.retry_utils import (
    retry_with_backoff, 
    RetryConfig, 
    with_graceful_degradation,
    retry_openai_operation,
    retry_file_operation
)

logger = structlog.get_logger(__name__)


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
            # Check service availability first
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    service_health_monitor.ensure_service_available("raganything", "initialization")
                )
            except ExternalServiceError:
                logger.warning("RAG-Anything service not available, using fallback mode")
                self.rag_anything = None
                return
            finally:
                loop.close()
            
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
            logger.warning(f"RAG-Anything not available: {e}")
            self.rag_anything = None
        except Exception as e:
            logger.error(f"Failed to initialize RAG-Anything: {e}")
            self.rag_anything = None
    
    def _get_llm_function(self):
        """Get user-configurable LLM function with retry logic."""
        @retry_openai_operation("llm_processing")
        @with_graceful_degradation(
            fallback_value="[LLM processing unavailable]",
            service_name="openai"
        )
        async def llm_func(prompt: str, **kwargs) -> str:
            """LLM function for RAG-Anything with error handling."""
            # Check OpenAI service availability
            await service_health_monitor.ensure_service_available("openai", "LLM processing")
            
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
        
        def sync_llm_func(prompt: str, **kwargs) -> str:
            """Synchronous wrapper for LLM function."""
            try:
                # Check if OpenAI is configured
                if not settings.OPENAI_API_KEY:
                    logger.warning("No OpenAI API key configured, using fallback")
                    return f"[Text analysis]: {prompt[:100]}..."
                
                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(llm_func(prompt, **kwargs))
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"LLM function error: {e}")
                return f"[Processing error]: {str(e)}"
        
        return sync_llm_func
    
    def _get_vision_function(self):
        """Get user-configurable vision model function with retry logic."""
        @retry_openai_operation("vision_processing")
        @with_graceful_degradation(
            fallback_value="[Vision processing unavailable]",
            service_name="openai"
        )
        async def vision_func(image_path: str, prompt: str = "Describe this image", **kwargs) -> str:
            """Vision model function for image processing with error handling."""
            # Check OpenAI service availability
            await service_health_monitor.ensure_service_available("openai", "vision processing")
            
            import openai
            import base64
            
            # Read and encode image with file operation retry
            @retry_file_operation("image_read")
            def read_image():
                with open(image_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode()
            
            image_data = read_image()
            
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
        
        def sync_vision_func(image_path: str, prompt: str = "Describe this image", **kwargs) -> str:
            """Synchronous wrapper for vision function."""
            try:
                # Check if OpenAI is configured
                if not settings.OPENAI_API_KEY:
                    logger.warning("No OpenAI API key configured, using fallback")
                    return f"[Image analysis]: {os.path.basename(image_path)}"
                
                # Check if image file exists
                if not os.path.exists(image_path):
                    logger.error(f"Image file not found: {image_path}")
                    return f"[Image not found]: {os.path.basename(image_path)}"
                
                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(vision_func(image_path, prompt, **kwargs))
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"Vision function error: {e}")
                return f"[Vision processing error]: {str(e)}"
        
        return sync_vision_func
    
    def _get_embedding_function(self):
        """Get user-configurable embedding function with retry logic."""
        @retry_openai_operation("embedding_generation")
        @with_graceful_degradation(
            fallback_value=None,
            service_name="openai"
        )
        async def embedding_func(text: str, **kwargs) -> List[float]:
            """Embedding function for semantic search with error handling."""
            # Check OpenAI service availability
            await service_health_monitor.ensure_service_available("openai", "embedding generation")
            
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
        
        def sync_embedding_func(text: str, **kwargs) -> List[float]:
            """Synchronous wrapper for embedding function."""
            try:
                # Check if OpenAI is configured
                if not settings.OPENAI_API_KEY:
                    logger.warning("No OpenAI API key configured, using fallback embedding")
                    return self._generate_fallback_embedding(text)
                
                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(embedding_func(text, **kwargs))
                    if result is None:  # Graceful degradation triggered
                        return self._generate_fallback_embedding(text)
                    return result
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"Embedding function error: {e}")
                return self._generate_fallback_embedding(text)
        
        return sync_embedding_func
    
    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate fallback embedding when OpenAI is unavailable."""
        try:
            import hashlib
            import numpy as np
            
            # Create a more sophisticated fallback embedding
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert hash bytes to float values
            embedding = []
            for i in range(0, len(hash_bytes), 4):
                chunk = hash_bytes[i:i+4]
                if len(chunk) == 4:
                    # Convert 4 bytes to float
                    value = int.from_bytes(chunk, byteorder='big') / (2**32 - 1)
                    embedding.append(value)
            
            # Pad or truncate to desired dimension
            target_dim = min(settings.EMBEDDING_DIM, 1536)  # Common embedding dimension
            while len(embedding) < target_dim:
                embedding.extend(embedding[:min(len(embedding), target_dim - len(embedding))])
            
            return embedding[:target_dim]
            
        except Exception as e:
            logger.error(f"Fallback embedding generation failed: {e}")
            # Return zero vector as last resort
            return [0.0] * min(settings.EMBEDDING_DIM, 1536)
    
    @retry_with_backoff(
        config=RetryConfig(max_retries=2, backoff_factor=1.5),
        service_name="raganything",
        operation_name="document_processing"
    )
    async def process_document(self, file_path: str, document_id: str) -> Dict[str, Any]:
        """
        Process a document using RAG-Anything with MinerU 2.0.
        
        Args:
            file_path: Path to the document file
            document_id: Unique identifier for the document
            
        Returns:
            Dict containing processing results
        """
        processing_context = {
            "document_id": document_id,
            "file_path": file_path,
            "operation": "document_processing"
        }
        
        try:
            logger.info("Starting document processing", **processing_context)
            
            # Check file existence with retry
            @retry_file_operation("file_validation")
            def validate_file():
                if not os.path.exists(file_path):
                    raise DocumentProcessingError(
                        f"File not found: {file_path}",
                        details=processing_context,
                        user_message="The uploaded file could not be found. Please try uploading again.",
                        recovery_suggestions=[
                            "Try uploading the file again",
                            "Check if the file was corrupted during upload",
                            "Ensure the file is not being used by another application"
                        ]
                    )
                return True
            
            validate_file()
            
            # Determine file type and size
            file_type = self._get_file_type(file_path)
            file_size = os.path.getsize(file_path)
            
            processing_context.update({
                "file_type": file_type,
                "file_size": file_size
            })
            
            logger.info("File validated successfully", **processing_context)
            
            # Create output directory with retry
            @retry_file_operation("directory_creation")
            def create_output_dir():
                output_dir = os.path.join(settings.PROCESSED_DIR, document_id)
                os.makedirs(output_dir, exist_ok=True)
                return output_dir
            
            output_dir = create_output_dir()
            processing_context["output_dir"] = output_dir
            
            # Check service availability before processing
            if self.rag_anything is None:
                logger.warning("RAG-Anything not available, using fallback processing", **processing_context)
                result = await self._process_with_fallback(file_path, output_dir, file_type)
            else:
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
                "output_dir": output_dir,
                "processing_mode": "raganything" if self.rag_anything else "fallback"
            })
            
            logger.info("Document processing completed successfully", **processing_context)
            return result
            
        except DocumentProcessingError:
            # Re-raise DocumentProcessingError with context
            raise
        except Exception as e:
            logger.error("Document processing failed", error=str(e), **processing_context)
            raise DocumentProcessingError(
                f"Processing failed: {str(e)}",
                details=processing_context,
                user_message="Document processing failed due to an internal error. Please try again.",
                recovery_suggestions=[
                    "Wait a moment and try processing the document again",
                    "Check if the document format is supported",
                    "Try processing a smaller or simpler document first",
                    "Contact support if the issue persists"
                ]
            )
    
    async def _process_with_rag_anything(self, file_path: str, output_dir: str, file_type: str) -> Dict[str, Any]:
        """Process document using RAG-Anything with MinerU 2.0."""
        processing_context = {
            "file_path": file_path,
            "output_dir": output_dir,
            "file_type": file_type,
            "method": "raganything"
        }
        
        try:
            logger.info("Starting RAG-Anything processing", **processing_context)
            
            # Check RAG-Anything service availability
            await service_health_monitor.ensure_service_available("raganything", "document processing")
            
            # Run RAG-Anything processing in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            @retry_with_backoff(
                config=RetryConfig(max_retries=2, backoff_factor=1.5),
                service_name="raganything",
                operation_name="document_processing"
            )
            def _sync_process():
                return self.rag_anything.process_document_complete(
                    file_path=file_path,
                    output_dir=output_dir,
                    parse_method=self.mineru_config["parse_method"],
                    device=self.mineru_config["device"],
                    backend=self.mineru_config["backend"],
                    lang=self.mineru_config["lang"]
                )
            
            # Execute in thread pool with timeout
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, _sync_process),
                    timeout=300  # 5 minute timeout
                )
            except asyncio.TimeoutError:
                raise DocumentProcessingError(
                    "Document processing timed out",
                    details=processing_context,
                    user_message="Document processing is taking too long. Please try with a smaller file.",
                    recovery_suggestions=[
                        "Try processing a smaller document",
                        "Split large documents into smaller parts",
                        "Contact support for assistance with large files"
                    ]
                )
            
            # Process the result
            processed_result = {
                "extracted_text": result.get("text", ""),
                "images": result.get("images", []),
                "tables": result.get("tables", []),
                "metadata": result.get("metadata", {}),
                "processing_time": result.get("processing_time", 0),
                "success": True
            }
            
            logger.info("RAG-Anything processing completed", 
                       extracted_text_length=len(processed_result["extracted_text"]),
                       images_count=len(processed_result["images"]),
                       tables_count=len(processed_result["tables"]),
                       **processing_context)
            
            # Handle multimodal content if present
            if result.get("images"):
                try:
                    processed_result["image_descriptions"] = await self._process_images(
                        result["images"], output_dir
                    )
                except Exception as e:
                    logger.warning("Image processing failed", error=str(e), **processing_context)
                    processed_result["image_descriptions"] = []
            
            if result.get("tables"):
                try:
                    processed_result["table_descriptions"] = await self._process_tables(
                        result["tables"], output_dir
                    )
                except Exception as e:
                    logger.warning("Table processing failed", error=str(e), **processing_context)
                    processed_result["table_descriptions"] = []
            
            # Process audio/video files
            if self._is_audio_video_file(file_path):
                try:
                    processed_result["audio_transcription"] = await self._process_audio_video(
                        file_path, output_dir
                    )
                except Exception as e:
                    logger.warning("Audio/video processing failed", error=str(e), **processing_context)
                    processed_result["audio_transcription"] = {}
            
            # Enhanced PDF processing
            if file_type == "application/pdf":
                try:
                    processed_result["pdf_analysis"] = await self._process_pdf_enhanced(
                        file_path, output_dir
                    )
                except Exception as e:
                    logger.warning("Enhanced PDF processing failed", error=str(e), **processing_context)
                    processed_result["pdf_analysis"] = {}
            
            return processed_result
            
        except DocumentProcessingError:
            # Re-raise DocumentProcessingError
            raise
        except Exception as e:
            logger.error("RAG-Anything processing failed", error=str(e), **processing_context)
            raise DocumentProcessingError(
                f"RAG-Anything processing failed: {str(e)}",
                details=processing_context,
                user_message="Advanced document processing failed. Trying fallback method.",
                recovery_suggestions=[
                    "The system will attempt basic text extraction",
                    "Some advanced features may not be available",
                    "Contact support if basic processing also fails"
                ]
            )
    
    async def _process_with_fallback(self, file_path: str, output_dir: str, file_type: str) -> Dict[str, Any]:
        """Fallback document processing when RAG-Anything is unavailable."""
        processing_context = {
            "file_path": file_path,
            "output_dir": output_dir,
            "file_type": file_type,
            "method": "fallback"
        }
        
        try:
            logger.info("Starting fallback document processing", **processing_context)
            
            extracted_text = ""
            
            # Basic text extraction based on file type
            if file_type == "text/plain":
                @retry_file_operation("text_file_read")
                def read_text_file():
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                
                extracted_text = read_text_file()
                
            elif file_type == "application/pdf":
                try:
                    import PyPDF2
                    
                    @retry_file_operation("pdf_read")
                    def read_pdf():
                        text = ""
                        with open(file_path, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            for page in reader.pages:
                                text += page.extract_text() + "\n"
                        return text
                    
                    extracted_text = read_pdf()
                    
                except ImportError:
                    logger.warning("PyPDF2 not available for PDF processing", **processing_context)
                    extracted_text = f"[PDF file: {os.path.basename(file_path)} - text extraction not available]"
                except Exception as e:
                    logger.warning("PDF text extraction failed", error=str(e), **processing_context)
                    extracted_text = f"[PDF file: {os.path.basename(file_path)} - text extraction failed]"
            
            else:
                # For other file types, provide basic metadata
                extracted_text = f"[{file_type} file: {os.path.basename(file_path)} - processed with basic extraction]"
            
            result = {
                "extracted_text": extracted_text,
                "images": [],
                "tables": [],
                "image_descriptions": [],
                "table_descriptions": [],
                "audio_transcription": {},
                "pdf_analysis": {},
                "metadata": {
                    "processing_method": "fallback",
                    "file_type": file_type,
                    "file_name": os.path.basename(file_path)
                },
                "processing_time": 0,
                "success": True
            }
            
            logger.info("Fallback processing completed", 
                       extracted_text_length=len(extracted_text),
                       **processing_context)
            
            return result
            
        except Exception as e:
            logger.error("Fallback processing failed", error=str(e), **processing_context)
            raise DocumentProcessingError(
                f"Fallback processing failed: {str(e)}",
                details=processing_context,
                user_message="Document processing failed completely. Please check the file format.",
                recovery_suggestions=[
                    "Ensure the file is not corrupted",
                    "Try converting the file to a supported format (PDF, TXT)",
                    "Contact support for assistance"
                ]
            )
    
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
"""
Multimodal content processors for images, tables, audio, and PDFs.
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import tempfile
import json

from app.core.config import settings
from app.core.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Image processing pipeline with vision model integration.
    """
    
    def __init__(self, vision_model_func):
        """Initialize image processor with vision model function."""
        self.vision_model_func = vision_model_func
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    async def process_image(self, image_path: str, context: str = "") -> Dict[str, Any]:
        """
        Process a single image with vision model.
        
        Args:
            image_path: Path to the image file
            context: Additional context for image analysis
            
        Returns:
            Dict containing image analysis results
        """
        try:
            if not os.path.exists(image_path):
                raise DocumentProcessingError(f"Image file not found: {image_path}")
            
            # Check if format is supported
            file_ext = Path(image_path).suffix.lower()
            if file_ext not in self.supported_formats:
                logger.warning(f"Potentially unsupported image format: {file_ext}")
            
            # Generate comprehensive description
            description_prompt = self._build_description_prompt(context)
            description = await self._run_vision_model(image_path, description_prompt)
            
            # Extract text content if present
            ocr_prompt = "Extract any text content from this image. If no text is present, respond with 'No text detected'."
            ocr_result = await self._run_vision_model(image_path, ocr_prompt)
            
            # Analyze visual elements
            analysis_prompt = "Analyze the visual elements in this image: colors, composition, objects, people, and overall theme."
            visual_analysis = await self._run_vision_model(image_path, analysis_prompt)
            
            # Get image metadata
            metadata = self._get_image_metadata(image_path)
            
            return {
                "image_path": image_path,
                "description": description,
                "ocr_text": ocr_result if "no text detected" not in ocr_result.lower() else "",
                "visual_analysis": visual_analysis,
                "metadata": metadata,
                "processing_success": True
            }
            
        except Exception as e:
            logger.error(f"Image processing failed for {image_path}: {e}")
            return {
                "image_path": image_path,
                "description": f"Error processing image: {str(e)}",
                "ocr_text": "",
                "visual_analysis": "",
                "metadata": {},
                "processing_success": False,
                "error": str(e)
            }
    
    async def process_image_batch(self, image_paths: List[str], context: str = "") -> List[Dict[str, Any]]:
        """Process multiple images concurrently."""
        tasks = [self.process_image(path, context) for path in image_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    "processing_success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _build_description_prompt(self, context: str) -> str:
        """Build comprehensive description prompt."""
        base_prompt = """Provide a detailed description of this image including:
1. Main subjects and objects
2. Setting and environment
3. Actions or activities depicted
4. Text content (if any)
5. Visual style and composition
6. Any notable details or context"""
        
        if context:
            base_prompt += f"\n\nAdditional context: {context}"
        
        return base_prompt
    
    async def _run_vision_model(self, image_path: str, prompt: str) -> str:
        """Run vision model with error handling."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self.vision_model_func, 
                image_path, 
                prompt
            )
            return result
        except Exception as e:
            logger.error(f"Vision model error for {image_path}: {e}")
            return f"Vision model processing failed: {str(e)}"
    
    def _get_image_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extract image metadata."""
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            with Image.open(image_path) as img:
                metadata = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height
                }
                
                # Extract EXIF data if available
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif_data[tag] = str(value)
                
                metadata["exif"] = exif_data
                return metadata
                
        except Exception as e:
            logger.warning(f"Failed to extract image metadata: {e}")
            return {"error": str(e)}


class TableProcessor:
    """
    Table extraction and processing capabilities.
    """
    
    def __init__(self, llm_model_func):
        """Initialize table processor with LLM function."""
        self.llm_model_func = llm_model_func
    
    async def process_table(self, table_data: Dict[str, Any], context: str = "") -> Dict[str, Any]:
        """
        Process extracted table data.
        
        Args:
            table_data: Table data from MinerU (HTML, CSV, or structured data)
            context: Additional context for table analysis
            
        Returns:
            Dict containing table analysis results
        """
        try:
            table_html = table_data.get("html", "")
            table_csv = table_data.get("csv", "")
            table_caption = table_data.get("caption", "")
            
            if not table_html and not table_csv:
                raise DocumentProcessingError("No table data provided")
            
            # Use HTML if available, otherwise CSV
            table_content = table_html if table_html else table_csv
            
            # Generate comprehensive table analysis
            analysis = await self._analyze_table_content(table_content, context, table_caption)
            
            # Extract key insights
            insights = await self._extract_table_insights(table_content, context)
            
            # Generate summary
            summary = await self._generate_table_summary(table_content, analysis, insights)
            
            return {
                "original_html": table_html,
                "original_csv": table_csv,
                "caption": table_caption,
                "analysis": analysis,
                "insights": insights,
                "summary": summary,
                "processing_success": True
            }
            
        except Exception as e:
            logger.error(f"Table processing failed: {e}")
            return {
                "original_html": table_data.get("html", ""),
                "original_csv": table_data.get("csv", ""),
                "caption": table_data.get("caption", ""),
                "analysis": f"Error processing table: {str(e)}",
                "insights": [],
                "summary": f"Table processing failed: {str(e)}",
                "processing_success": False,
                "error": str(e)
            }
    
    async def process_table_batch(self, tables: List[Dict[str, Any]], context: str = "") -> List[Dict[str, Any]]:
        """Process multiple tables concurrently."""
        tasks = [self.process_table(table, context) for table in tables]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    "processing_success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _analyze_table_content(self, table_content: str, context: str, caption: str) -> str:
        """Analyze table structure and content."""
        prompt = f"""Analyze this table and provide a detailed description:

Table Content:
{table_content}

Caption: {caption}
Context: {context}

Please describe:
1. Table structure (rows, columns, headers)
2. Data types and patterns
3. Key relationships between columns
4. Notable trends or patterns
5. Data quality and completeness"""

        return await self._run_llm_model(prompt)
    
    async def _extract_table_insights(self, table_content: str, context: str) -> List[str]:
        """Extract key insights from table data."""
        prompt = f"""Extract key insights from this table data:

{table_content}

Context: {context}

Provide 3-5 key insights as a JSON list of strings. Focus on:
- Important trends or patterns
- Notable data points or outliers
- Relationships between variables
- Business or analytical implications

Return only the JSON list, no additional text."""

        try:
            result = await self._run_llm_model(prompt)
            # Try to parse as JSON
            insights = json.loads(result)
            if isinstance(insights, list):
                return insights
            else:
                return [str(insights)]
        except:
            # Fallback to simple text processing
            return [line.strip() for line in result.split('\n') if line.strip()]
    
    async def _generate_table_summary(self, table_content: str, analysis: str, insights: List[str]) -> str:
        """Generate concise table summary."""
        insights_text = "\n".join([f"- {insight}" for insight in insights])
        
        prompt = f"""Create a concise summary of this table based on the analysis:

Analysis: {analysis}

Key Insights:
{insights_text}

Provide a 2-3 sentence summary that captures the essence of the table's content and significance."""

        return await self._run_llm_model(prompt)
    
    async def _run_llm_model(self, prompt: str) -> str:
        """Run LLM model with error handling."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self.llm_model_func, 
                prompt
            )
            return result
        except Exception as e:
            logger.error(f"LLM model error: {e}")
            return f"LLM processing failed: {str(e)}"


class AudioProcessor:
    """
    Audio transcription for audio/video files.
    """
    
    def __init__(self):
        """Initialize audio processor."""
        self.supported_formats = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'}
        self.video_formats = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
    
    async def process_audio(self, audio_path: str, context: str = "") -> Dict[str, Any]:
        """
        Process audio file for transcription.
        
        Args:
            audio_path: Path to audio file
            context: Additional context for transcription
            
        Returns:
            Dict containing transcription results
        """
        try:
            if not os.path.exists(audio_path):
                raise DocumentProcessingError(f"Audio file not found: {audio_path}")
            
            file_ext = Path(audio_path).suffix.lower()
            is_video = file_ext in self.video_formats
            
            # Extract audio from video if needed
            if is_video:
                audio_path = await self._extract_audio_from_video(audio_path)
            
            # Transcribe audio
            transcription = await self._transcribe_audio(audio_path, context)
            
            # Generate summary if transcription is long
            summary = ""
            if len(transcription) > 500:
                summary = await self._summarize_transcription(transcription, context)
            
            # Extract key topics
            topics = await self._extract_topics(transcription)
            
            # Get audio metadata
            metadata = self._get_audio_metadata(audio_path)
            
            result = {
                "audio_path": audio_path,
                "transcription": transcription,
                "summary": summary,
                "topics": topics,
                "metadata": metadata,
                "is_video_source": is_video,
                "processing_success": True
            }
            
            # Clean up temporary audio file if extracted from video
            if is_video and audio_path != audio_path:
                try:
                    os.unlink(audio_path)
                except:
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"Audio processing failed for {audio_path}: {e}")
            return {
                "audio_path": audio_path,
                "transcription": f"Error processing audio: {str(e)}",
                "summary": "",
                "topics": [],
                "metadata": {},
                "is_video_source": False,
                "processing_success": False,
                "error": str(e)
            }
    
    async def _extract_audio_from_video(self, video_path: str) -> str:
        """Extract audio track from video file."""
        try:
            import subprocess
            
            # Create temporary audio file
            temp_audio = tempfile.mktemp(suffix='.wav')
            
            # Use ffmpeg to extract audio
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                temp_audio, '-y'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise DocumentProcessingError(f"FFmpeg failed: {stderr.decode()}")
            
            return temp_audio
            
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            raise DocumentProcessingError(f"Failed to extract audio from video: {str(e)}")
    
    async def _transcribe_audio(self, audio_path: str, context: str) -> str:
        """Transcribe audio using OpenAI Whisper API or local processing."""
        try:
            # Try OpenAI Whisper API if configured
            if settings.OPENAI_API_KEY:
                return await self._transcribe_with_openai(audio_path)
            else:
                # Fallback to local processing (placeholder)
                return await self._transcribe_local(audio_path)
                
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return f"Transcription failed: {str(e)}"
    
    async def _transcribe_with_openai(self, audio_path: str) -> str:
        """Transcribe using OpenAI Whisper API."""
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
            
            with open(audio_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            return transcript
            
        except Exception as e:
            logger.error(f"OpenAI transcription failed: {e}")
            raise
    
    async def _transcribe_local(self, audio_path: str) -> str:
        """Local transcription fallback (placeholder)."""
        # This would integrate with local Whisper or other transcription models
        logger.warning("Local transcription not implemented, using placeholder")
        return f"[Audio transcription placeholder for: {os.path.basename(audio_path)}]"
    
    async def _summarize_transcription(self, transcription: str, context: str) -> str:
        """Generate summary of long transcription."""
        # This would use the LLM to summarize
        if len(transcription) > 100:
            return f"Summary: {transcription[:100]}..."
        return transcription
    
    async def _extract_topics(self, transcription: str) -> List[str]:
        """Extract key topics from transcription."""
        # Placeholder for topic extraction
        words = transcription.split()
        if len(words) > 10:
            return ["audio_content", "transcribed_speech"]
        return []
    
    def _get_audio_metadata(self, audio_path: str) -> Dict[str, Any]:
        """Extract audio file metadata."""
        try:
            import mutagen
            
            audio_file = mutagen.File(audio_path)
            if audio_file:
                return {
                    "duration": getattr(audio_file.info, 'length', 0),
                    "bitrate": getattr(audio_file.info, 'bitrate', 0),
                    "sample_rate": getattr(audio_file.info, 'sample_rate', 0),
                    "channels": getattr(audio_file.info, 'channels', 0)
                }
        except:
            pass
        
        # Fallback to basic file info
        stats = os.stat(audio_path)
        return {
            "file_size": stats.st_size,
            "created_at": stats.st_ctime
        }


class PDFProcessor:
    """
    PDF text extraction and viewing capabilities.
    """
    
    def __init__(self):
        """Initialize PDF processor."""
        pass
    
    async def process_pdf(self, pdf_path: str, context: str = "") -> Dict[str, Any]:
        """
        Process PDF file for text extraction and analysis.
        
        Args:
            pdf_path: Path to PDF file
            context: Additional context for processing
            
        Returns:
            Dict containing PDF processing results
        """
        try:
            if not os.path.exists(pdf_path):
                raise DocumentProcessingError(f"PDF file not found: {pdf_path}")
            
            # Extract text content
            text_content = await self._extract_pdf_text(pdf_path)
            
            # Extract metadata
            metadata = await self._extract_pdf_metadata(pdf_path)
            
            # Generate structure analysis
            structure = await self._analyze_pdf_structure(text_content)
            
            return {
                "pdf_path": pdf_path,
                "text_content": text_content,
                "metadata": metadata,
                "structure": structure,
                "page_count": metadata.get("page_count", 0),
                "processing_success": True
            }
            
        except Exception as e:
            logger.error(f"PDF processing failed for {pdf_path}: {e}")
            return {
                "pdf_path": pdf_path,
                "text_content": f"Error processing PDF: {str(e)}",
                "metadata": {},
                "structure": {},
                "page_count": 0,
                "processing_success": False,
                "error": str(e)
            }
    
    async def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF using multiple methods."""
        try:
            # Try PyMuPDF first (most reliable)
            try:
                import fitz  # PyMuPDF
                
                doc = fitz.open(pdf_path)
                text_content = ""
                
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    text_content += f"\n--- Page {page_num + 1} ---\n"
                    text_content += page.get_text()
                
                doc.close()
                return text_content
                
            except ImportError:
                logger.warning("PyMuPDF not available, trying pdfplumber")
                
                # Fallback to pdfplumber
                import pdfplumber
                
                text_content = ""
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        text_content += f"\n--- Page {page_num + 1} ---\n"
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text
                
                return text_content
                
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return f"PDF text extraction failed: {str(e)}"
    
    async def _extract_pdf_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract PDF metadata."""
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            
            result = {
                "page_count": doc.page_count,
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", "")
            }
            
            doc.close()
            return result
            
        except Exception as e:
            logger.warning(f"PDF metadata extraction failed: {e}")
            return {"error": str(e)}
    
    async def _analyze_pdf_structure(self, text_content: str) -> Dict[str, Any]:
        """Analyze PDF structure and content organization."""
        try:
            lines = text_content.split('\n')
            
            # Count pages
            page_markers = [line for line in lines if line.startswith('--- Page')]
            page_count = len(page_markers)
            
            # Estimate sections (lines that might be headers)
            potential_headers = []
            for line in lines:
                line = line.strip()
                if line and len(line) < 100 and not line.startswith('---'):
                    # Simple heuristic for headers
                    if line.isupper() or (line[0].isupper() and line.count(' ') < 5):
                        potential_headers.append(line)
            
            return {
                "page_count": page_count,
                "total_lines": len(lines),
                "potential_headers": potential_headers[:10],  # First 10
                "estimated_sections": len(potential_headers),
                "text_length": len(text_content)
            }
            
        except Exception as e:
            logger.error(f"PDF structure analysis failed: {e}")
            return {"error": str(e)}


# Factory class to create processors
class MultimodalProcessorFactory:
    """Factory for creating multimodal processors."""
    
    @staticmethod
    def create_image_processor(vision_model_func) -> ImageProcessor:
        """Create image processor with vision model."""
        return ImageProcessor(vision_model_func)
    
    @staticmethod
    def create_table_processor(llm_model_func) -> TableProcessor:
        """Create table processor with LLM model."""
        return TableProcessor(llm_model_func)
    
    @staticmethod
    def create_audio_processor() -> AudioProcessor:
        """Create audio processor."""
        return AudioProcessor()
    
    @staticmethod
    def create_pdf_processor() -> PDFProcessor:
        """Create PDF processor."""
        return PDFProcessor()
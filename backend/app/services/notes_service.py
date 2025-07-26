"""
Notes service for managing note operations.
"""

import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from sqlalchemy.exc import SQLAlchemyError

from app.models.database import Note
from app.models.schemas import NoteCreate, NoteUpdate, NoteResponse
from app.core.database import SessionLocal
from app.core.exceptions import (
    NotFoundError, 
    ValidationError, 
    DatabaseError,
    ConflictError,
    ErrorCategory,
    ErrorSeverity
)
from app.core.error_utils import handle_errors, retry_on_failure, ErrorContext


class NotesService:
    """Service for managing notes operations."""
    
    def __init__(self):
        self.db_session = SessionLocal
    
    def _count_words(self, content: str) -> int:
        """Count words in markdown content."""
        # Remove markdown syntax for accurate word count
        text = re.sub(r'[#*_`\[\]()]+', '', content)
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)  # Remove images
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)   # Remove links
        words = text.split()
        return len([word for word in words if word.strip()])
    
    def _extract_wiki_links(self, content: str) -> List[str]:
        """Extract wiki-style links [[note-name]] from content."""
        pattern = r'\[\[([^\]]+)\]\]'
        matches = re.findall(pattern, content)
        return [match.strip() for match in matches]
    
    def _validate_markdown(self, content: str) -> bool:
        """Basic markdown validation."""
        # Check for balanced brackets and parentheses
        brackets = content.count('[') - content.count(']')
        parens = content.count('(') - content.count(')')
        
        if brackets != 0 or parens != 0:
            return False
        
        return True
    
    @handle_errors(
        operation="create_note",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.MEDIUM,
        user_message="Failed to create note. Please try again.",
        recovery_suggestions=[
            "Check if a note with this title already exists",
            "Verify the note content is valid markdown",
            "Try with a shorter title or content",
            "Contact support if the issue persists"
        ]
    )
    async def create_note(self, note_data: NoteCreate) -> NoteResponse:
        """Create a new note."""
        db = self.db_session()
        try:
            # Validate markdown content
            if not self._validate_markdown(note_data.content):
                raise ValidationError("Invalid markdown syntax")
            
            # Count words
            word_count = self._count_words(note_data.content)
            
            # Create note
            note = Note(
                title=note_data.title,
                content=note_data.content,
                tags=note_data.tags,
                word_count=word_count
            )
            
            db.add(note)
            db.commit()
            db.refresh(note)
            
            return NoteResponse.model_validate(note)
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    @handle_errors(
        operation="get_note",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.LOW,
        user_message="Failed to retrieve note.",
        recovery_suggestions=[
            "Check if the note ID is correct",
            "Verify the note hasn't been deleted",
            "Try refreshing the page",
            "Search for the note using the search function"
        ]
    )
    async def get_note(self, note_id: str) -> NoteResponse:
        """Get a note by ID."""
        with ErrorContext("get_note") as ctx:
            ctx.add_context("note_id", note_id)
            
            db = self.db_session()
            try:
                note = db.query(Note).filter(Note.id == note_id).first()
                if not note:
                    raise NotFoundError(
                        f"Note with ID {note_id} not found",
                        details={"note_id": note_id},
                        user_message="The requested note could not be found.",
                        recovery_suggestions=[
                            "Check if the note ID is correct",
                            "Verify the note hasn't been deleted",
                            "Try searching for the note by title",
                            "Check your recent notes list"
                        ]
                    )
                
                return NoteResponse.model_validate(note)
                
            except SQLAlchemyError as e:
                raise DatabaseError(
                    f"Database error while retrieving note {note_id}",
                    details={"note_id": note_id, "db_error": str(e)}
                ) from e
            finally:
                db.close()
    
    @handle_errors(
        operation="update_note",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.MEDIUM,
        user_message="Failed to update note. Please try again.",
        recovery_suggestions=[
            "Check if the note still exists",
            "Verify the markdown content is valid",
            "Try saving with a shorter title or content",
            "Refresh the page and try again"
        ]
    )
    @retry_on_failure(max_attempts=2, base_delay=0.5)
    async def update_note(self, note_id: str, note_data: NoteUpdate) -> NoteResponse:
        """Update an existing note."""
        with ErrorContext("update_note") as ctx:
            ctx.add_context("note_id", note_id)
            ctx.add_context("has_title_update", note_data.title is not None)
            ctx.add_context("has_content_update", note_data.content is not None)
            
            db = self.db_session()
            try:
                note = db.query(Note).filter(Note.id == note_id).first()
                if not note:
                    raise NotFoundError(
                        f"Note with ID {note_id} not found",
                        details={"note_id": note_id},
                        user_message="The note you're trying to update could not be found.",
                        recovery_suggestions=[
                            "Check if the note was deleted by another user",
                            "Verify the note ID is correct",
                            "Try refreshing the page",
                            "Create a new note with this content"
                        ]
                    )
                
                # Validate content if provided
                if note_data.content is not None:
                    if not self._validate_markdown(note_data.content):
                        raise ValidationError(
                            "Invalid markdown syntax in note content",
                            details={"note_id": note_id, "content_length": len(note_data.content)},
                            user_message="The note content contains invalid markdown syntax.",
                            recovery_suggestions=[
                                "Check for unmatched brackets [ ] or parentheses ( )",
                                "Verify link syntax is correct",
                                "Use the preview pane to identify syntax errors",
                                "Try saving without complex markdown formatting"
                            ]
                        )
                
                # Check for title conflicts if title is being updated
                if note_data.title is not None and note_data.title != note.title:
                    existing_note = db.query(Note).filter(
                        and_(Note.title == note_data.title, Note.id != note_id)
                    ).first()
                    if existing_note:
                        raise ConflictError(
                            f"A note with title '{note_data.title}' already exists",
                            conflicting_resource=existing_note.id,
                            details={"existing_note_id": existing_note.id, "title": note_data.title}
                        )
                
                # Update fields if provided
                if note_data.title is not None:
                    note.title = note_data.title
                
                if note_data.content is not None:
                    note.content = note_data.content
                    note.word_count = self._count_words(note_data.content)
                
                if note_data.tags is not None:
                    note.tags = note_data.tags
                
                note.updated_at = datetime.utcnow()
                
                db.commit()
                db.refresh(note)
                
                return NoteResponse.model_validate(note)
                
            except SQLAlchemyError as e:
                db.rollback()
                raise DatabaseError(
                    f"Database error while updating note {note_id}",
                    details={"note_id": note_id, "db_error": str(e)}
                ) from e
            except (NotFoundError, ValidationError, ConflictError):
                db.rollback()
                raise
            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()
    
    async def delete_note(self, note_id: str) -> bool:
        """Delete a note."""
        db = self.db_session()
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                raise NotFoundError(f"Note with ID {note_id} not found")
            
            db.delete(note)
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def list_notes(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """List notes with filtering and pagination."""
        db = self.db_session()
        try:
            query = db.query(Note)
            
            # Apply search filter
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Note.title.ilike(search_term),
                        Note.content.ilike(search_term)
                    )
                )
            
            # Apply tags filter
            if tags:
                for tag in tags:
                    query = query.filter(Note.tags.contains([tag]))
            
            # Apply sorting
            if sort_by == "title":
                order_column = Note.title
            elif sort_by == "created_at":
                order_column = Note.created_at
            elif sort_by == "word_count":
                order_column = Note.word_count
            else:
                order_column = Note.updated_at
            
            if sort_order == "asc":
                query = query.order_by(order_column.asc())
            else:
                query = query.order_by(order_column.desc())
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            notes = query.offset(skip).limit(limit).all()
            
            return {
                "notes": [NoteResponse.model_validate(note) for note in notes],
                "total": total,
                "skip": skip,
                "limit": limit
            }
            
        finally:
            db.close()
    
    async def search_notes(
        self, 
        query: str, 
        limit: int = 10,
        fuzzy: bool = True
    ) -> List[NoteResponse]:
        """Search notes with fuzzy matching."""
        db = self.db_session()
        try:
            if fuzzy:
                # Fuzzy search using LIKE with wildcards
                search_terms = query.split()
                conditions = []
                
                for term in search_terms:
                    term_pattern = f"%{term}%"
                    conditions.append(
                        or_(
                            Note.title.ilike(term_pattern),
                            Note.content.ilike(term_pattern)
                        )
                    )
                
                # Combine conditions with AND
                if conditions:
                    search_condition = and_(*conditions)
                else:
                    search_condition = Note.title.ilike(f"%{query}%")
            else:
                # Exact search
                search_condition = or_(
                    Note.title.ilike(f"%{query}%"),
                    Note.content.ilike(f"%{query}%")
                )
            
            notes = (
                db.query(Note)
                .filter(search_condition)
                .order_by(Note.updated_at.desc())
                .limit(limit)
                .all()
            )
            
            return [NoteResponse.model_validate(note) for note in notes]
            
        finally:
            db.close()
    
    async def get_notes_by_tag(self, tag: str, limit: int = 50) -> List[NoteResponse]:
        """Get notes by specific tag."""
        db = self.db_session()
        try:
            notes = (
                db.query(Note)
                .filter(Note.tags.contains([tag]))
                .order_by(Note.updated_at.desc())
                .limit(limit)
                .all()
            )
            
            return [NoteResponse.model_validate(note) for note in notes]
            
        finally:
            db.close()
    
    async def get_all_tags(self) -> List[str]:
        """Get all unique tags from all notes."""
        db = self.db_session()
        try:
            # Get all notes with tags
            notes = db.query(Note).filter(Note.tags != []).all()
            
            # Collect all unique tags
            all_tags = set()
            for note in notes:
                if note.tags:
                    all_tags.update(note.tags)
            
            return sorted(list(all_tags))
            
        finally:
            db.close()
    
    async def get_wiki_links(self, note_id: str) -> Dict[str, List[str]]:
        """Get wiki links from a note and find linked notes."""
        db = self.db_session()
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                raise NotFoundError(f"Note with ID {note_id} not found")
            
            # Extract wiki links from content
            wiki_links = self._extract_wiki_links(note.content)
            
            # Find existing notes that match the links
            linked_notes = []
            broken_links = []
            
            for link in wiki_links:
                # Try to find note by title
                linked_note = db.query(Note).filter(
                    Note.title.ilike(f"%{link}%")
                ).first()
                
                if linked_note:
                    linked_notes.append({
                        "id": linked_note.id,
                        "title": linked_note.title,
                        "link_text": link
                    })
                else:
                    broken_links.append(link)
            
            return {
                "outgoing_links": linked_notes,
                "broken_links": broken_links
            }
            
        finally:
            db.close()
    
    async def get_backlinks(self, note_id: str) -> List[Dict[str, Any]]:
        """Get notes that link to this note."""
        db = self.db_session()
        try:
            target_note = db.query(Note).filter(Note.id == note_id).first()
            if not target_note:
                raise NotFoundError(f"Note with ID {note_id} not found")
            
            # Find notes that contain links to this note's title
            backlinks = []
            all_notes = db.query(Note).filter(Note.id != note_id).all()
            
            for note in all_notes:
                wiki_links = self._extract_wiki_links(note.content)
                for link in wiki_links:
                    if target_note.title.lower() in link.lower():
                        backlinks.append({
                            "id": note.id,
                            "title": note.title,
                            "link_text": link,
                            "updated_at": note.updated_at
                        })
                        break  # Only add each note once
            
            return backlinks
            
        finally:
            db.close()
    
    async def create_bidirectional_links(self, note_id: str) -> Dict[str, Any]:
        """Create bidirectional links by automatically creating notes for broken links."""
        db = self.db_session()
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                raise NotFoundError(f"Note with ID {note_id} not found")
            
            # Get current wiki links
            wiki_links = self._extract_wiki_links(note.content)
            created_notes = []
            linked_notes = []
            
            for link_text in wiki_links:
                # Try to find existing note by title
                existing_note = db.query(Note).filter(
                    Note.title.ilike(f"%{link_text}%")
                ).first()
                
                if existing_note:
                    linked_notes.append({
                        "id": existing_note.id,
                        "title": existing_note.title,
                        "link_text": link_text,
                        "action": "linked_existing"
                    })
                else:
                    # Create new note for broken link
                    new_note = Note(
                        title=link_text,
                        content=f"# {link_text}\n\n_This note was automatically created from a link in [[{note.title}]]._\n\n",
                        tags=["auto-created"],
                        word_count=self._count_words(f"# {link_text}\n\n_This note was automatically created from a link in [[{note.title}]]._\n\n")
                    )
                    
                    db.add(new_note)
                    db.commit()
                    db.refresh(new_note)
                    
                    created_notes.append({
                        "id": new_note.id,
                        "title": new_note.title,
                        "link_text": link_text,
                        "action": "created_new"
                    })
            
            return {
                "source_note_id": note_id,
                "source_note_title": note.title,
                "created_notes": created_notes,
                "linked_notes": linked_notes,
                "total_links_processed": len(wiki_links)
            }
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def suggest_links(self, note_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Suggest potential links based on content similarity."""
        db = self.db_session()
        try:
            source_note = db.query(Note).filter(Note.id == note_id).first()
            if not source_note:
                raise NotFoundError(f"Note with ID {note_id} not found")
            
            # Get all other notes
            other_notes = db.query(Note).filter(Note.id != note_id).all()
            
            suggestions = []
            source_words = set(source_note.content.lower().split())
            source_title_words = set(source_note.title.lower().split())
            
            for note in other_notes:
                # Calculate content similarity
                note_words = set(note.content.lower().split())
                note_title_words = set(note.title.lower().split())
                
                # Calculate Jaccard similarity for content
                content_intersection = len(source_words.intersection(note_words))
                content_union = len(source_words.union(note_words))
                content_similarity = content_intersection / content_union if content_union > 0 else 0
                
                # Calculate title similarity (higher weight)
                title_intersection = len(source_title_words.intersection(note_title_words))
                title_union = len(source_title_words.union(note_title_words))
                title_similarity = title_intersection / title_union if title_union > 0 else 0
                
                # Combined similarity score (title weighted more heavily)
                combined_similarity = (content_similarity * 0.3) + (title_similarity * 0.7)
                
                # Check if already linked
                existing_links = self._extract_wiki_links(source_note.content)
                already_linked = any(note.title.lower() in link.lower() for link in existing_links)
                
                if combined_similarity > 0.1 and not already_linked:  # Minimum threshold
                    suggestions.append({
                        "id": note.id,
                        "title": note.title,
                        "similarity_score": round(combined_similarity, 3),
                        "content_similarity": round(content_similarity, 3),
                        "title_similarity": round(title_similarity, 3),
                        "suggested_link_text": note.title,
                        "reason": self._get_similarity_reason(content_similarity, title_similarity)
                    })
            
            # Sort by similarity score and return top suggestions
            suggestions.sort(key=lambda x: x["similarity_score"], reverse=True)
            return suggestions[:limit]
            
        finally:
            db.close()
    
    def _get_similarity_reason(self, content_sim: float, title_sim: float) -> str:
        """Get human-readable reason for link suggestion."""
        if title_sim > 0.5:
            return "Similar titles"
        elif content_sim > 0.3:
            return "Similar content"
        elif title_sim > 0.2:
            return "Related titles"
        else:
            return "Related content"
    
    async def validate_all_links(self, note_id: str) -> Dict[str, Any]:
        """Comprehensive link validation for a note."""
        db = self.db_session()
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                raise NotFoundError(f"Note with ID {note_id} not found")
            
            # Extract all wiki links
            wiki_links = self._extract_wiki_links(note.content)
            
            valid_links = []
            broken_links = []
            ambiguous_links = []
            
            for link_text in wiki_links:
                # Find matching notes
                matching_notes = db.query(Note).filter(
                    Note.title.ilike(f"%{link_text}%")
                ).all()
                
                if len(matching_notes) == 1:
                    valid_links.append({
                        "link_text": link_text,
                        "target_note_id": matching_notes[0].id,
                        "target_note_title": matching_notes[0].title,
                        "match_type": "exact" if matching_notes[0].title.lower() == link_text.lower() else "partial"
                    })
                elif len(matching_notes) > 1:
                    ambiguous_links.append({
                        "link_text": link_text,
                        "possible_matches": [
                            {
                                "id": match.id,
                                "title": match.title,
                                "similarity": self._calculate_string_similarity(link_text, match.title)
                            }
                            for match in matching_notes
                        ]
                    })
                else:
                    broken_links.append({
                        "link_text": link_text,
                        "suggestions": await self._suggest_similar_notes(link_text, db)
                    })
            
            return {
                "note_id": note_id,
                "note_title": note.title,
                "total_links": len(wiki_links),
                "valid_links": valid_links,
                "broken_links": broken_links,
                "ambiguous_links": ambiguous_links,
                "validation_summary": {
                    "valid_count": len(valid_links),
                    "broken_count": len(broken_links),
                    "ambiguous_count": len(ambiguous_links),
                    "health_score": len(valid_links) / len(wiki_links) if wiki_links else 1.0
                }
            }
            
        finally:
            db.close()
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using Levenshtein distance."""
        str1, str2 = str1.lower(), str2.lower()
        
        if str1 == str2:
            return 1.0
        
        # Simple character-based similarity
        longer = str1 if len(str1) > len(str2) else str2
        shorter = str2 if len(str1) > len(str2) else str1
        
        if len(longer) == 0:
            return 1.0
        
        # Count matching characters
        matches = sum(1 for a, b in zip(shorter, longer) if a == b)
        return matches / len(longer)
    
    async def _suggest_similar_notes(self, link_text: str, db) -> List[Dict[str, Any]]:
        """Suggest similar notes for a broken link."""
        all_notes = db.query(Note).all()
        suggestions = []
        
        for note in all_notes:
            similarity = self._calculate_string_similarity(link_text, note.title)
            if similarity > 0.3:  # Minimum similarity threshold
                suggestions.append({
                    "id": note.id,
                    "title": note.title,
                    "similarity": round(similarity, 3)
                })
        
        suggestions.sort(key=lambda x: x["similarity"], reverse=True)
        return suggestions[:3]  # Top 3 suggestions
    
    async def auto_link_content(self, note_id: str, min_similarity: float = 0.8) -> Dict[str, Any]:
        """Automatically add links to content based on existing note titles."""
        db = self.db_session()
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                raise NotFoundError(f"Note with ID {note_id} not found")
            
            # Get all other notes
            other_notes = db.query(Note).filter(Note.id != note_id).all()
            
            updated_content = note.content
            added_links = []
            
            for other_note in other_notes:
                # Check if the note title appears in the content (case-insensitive)
                title_lower = other_note.title.lower()
                content_lower = updated_content.lower()
                
                # Find occurrences of the title in content
                if title_lower in content_lower:
                    # Check if it's not already a wiki link
                    existing_links = self._extract_wiki_links(updated_content)
                    already_linked = any(title_lower in link.lower() for link in existing_links)
                    
                    if not already_linked:
                        # Replace first occurrence with wiki link
                        # Use case-preserving replacement
                        import re
                        pattern = re.compile(re.escape(other_note.title), re.IGNORECASE)
                        match = pattern.search(updated_content)
                        
                        if match:
                            original_text = match.group()
                            wiki_link = f"[[{original_text}]]"
                            updated_content = updated_content[:match.start()] + wiki_link + updated_content[match.end():]
                            
                            added_links.append({
                                "original_text": original_text,
                                "target_note_id": other_note.id,
                                "target_note_title": other_note.title,
                                "position": match.start()
                            })
            
            # Update the note if links were added
            if added_links:
                note.content = updated_content
                note.word_count = self._count_words(updated_content)
                note.updated_at = datetime.utcnow()
                
                db.commit()
                db.refresh(note)
            
            return {
                "note_id": note_id,
                "note_title": note.title,
                "added_links": added_links,
                "total_links_added": len(added_links),
                "updated_content": updated_content if added_links else None
            }
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()


# Create service instance
notes_service = NotesService()
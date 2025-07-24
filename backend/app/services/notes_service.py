"""
Notes service for managing note operations.
"""

import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.database import Note
from app.models.schemas import NoteCreate, NoteUpdate, NoteResponse
from app.core.database import SessionLocal
from app.core.exceptions import NotFoundError, ValidationError


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
    
    async def get_note(self, note_id: str) -> NoteResponse:
        """Get a note by ID."""
        db = self.db_session()
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                raise NotFoundError(f"Note with ID {note_id} not found")
            
            return NoteResponse.model_validate(note)
            
        finally:
            db.close()
    
    async def update_note(self, note_id: str, note_data: NoteUpdate) -> NoteResponse:
        """Update an existing note."""
        db = self.db_session()
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                raise NotFoundError(f"Note with ID {note_id} not found")
            
            # Update fields if provided
            if note_data.title is not None:
                note.title = note_data.title
            
            if note_data.content is not None:
                # Validate markdown content
                if not self._validate_markdown(note_data.content):
                    raise ValidationError("Invalid markdown syntax")
                
                note.content = note_data.content
                note.word_count = self._count_words(note_data.content)
            
            if note_data.tags is not None:
                note.tags = note_data.tags
            
            note.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(note)
            
            return NoteResponse.model_validate(note)
            
        except Exception as e:
            db.rollback()
            raise e
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


# Create service instance
notes_service = NotesService()
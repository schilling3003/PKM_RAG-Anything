"""
Notes API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from app.models.schemas import (
    NoteCreate, NoteUpdate, NoteResponse, NotesListResponse,
    BaseResponse, ErrorResponse
)
from app.services.notes_service import notes_service
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()


@router.post("/", response_model=NoteResponse, status_code=201)
async def create_note(note_data: NoteCreate):
    """Create a new note."""
    try:
        note = await notes_service.create_note(note_data)
        return note
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create note: {str(e)}")


@router.get("/", response_model=NotesListResponse)
async def list_notes(
    skip: int = Query(0, ge=0, description="Number of notes to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of notes to return"),
    search: Optional[str] = Query(None, description="Search term for title and content"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter by"),
    sort_by: str = Query("updated_at", regex="^(title|created_at|updated_at|word_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    """List notes with filtering, searching, and pagination."""
    try:
        # Parse tags if provided
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        result = await notes_service.list_notes(
            skip=skip,
            limit=limit,
            search=search,
            tags=tag_list,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return NotesListResponse(
            notes=result["notes"],
            total=result["total"],
            message=f"Retrieved {len(result['notes'])} notes"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list notes: {str(e)}")


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str = Path(..., description="Note ID")):
    """Get a specific note by ID."""
    try:
        note = await notes_service.get_note(note_id)
        return note
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get note: {str(e)}")


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_data: NoteUpdate,
    note_id: str = Path(..., description="Note ID")
):
    """Update an existing note."""
    try:
        note = await notes_service.update_note(note_id, note_data)
        return note
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update note: {str(e)}")


@router.delete("/{note_id}", response_model=BaseResponse)
async def delete_note(note_id: str = Path(..., description="Note ID")):
    """Delete a note."""
    try:
        success = await notes_service.delete_note(note_id)
        if success:
            return BaseResponse(message=f"Note {note_id} deleted successfully")
        else:
            raise HTTPException(status_code=500, detail="Failed to delete note")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {str(e)}")


@router.get("/search/query")
async def search_notes(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    fuzzy: bool = Query(True, description="Enable fuzzy search")
):
    """Search notes with fuzzy matching."""
    try:
        notes = await notes_service.search_notes(q, limit=limit, fuzzy=fuzzy)
        return {
            "query": q,
            "results": notes,
            "total": len(notes),
            "fuzzy": fuzzy
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/tags/all")
async def get_all_tags():
    """Get all unique tags from all notes."""
    try:
        tags = await notes_service.get_all_tags()
        return {
            "tags": tags,
            "total": len(tags)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tags: {str(e)}")


@router.get("/tags/{tag}")
async def get_notes_by_tag(
    tag: str = Path(..., description="Tag name"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of notes")
):
    """Get notes by specific tag."""
    try:
        notes = await notes_service.get_notes_by_tag(tag, limit=limit)
        return {
            "tag": tag,
            "notes": notes,
            "total": len(notes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notes by tag: {str(e)}")


@router.get("/{note_id}/links")
async def get_note_links(note_id: str = Path(..., description="Note ID")):
    """Get wiki links from a note and find linked notes."""
    try:
        links = await notes_service.get_wiki_links(note_id)
        return links
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get note links: {str(e)}")


@router.get("/{note_id}/backlinks")
async def get_note_backlinks(note_id: str = Path(..., description="Note ID")):
    """Get notes that link to this note."""
    try:
        backlinks = await notes_service.get_backlinks(note_id)
        return {
            "note_id": note_id,
            "backlinks": backlinks,
            "total": len(backlinks)
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get backlinks: {str(e)}")


@router.post("/{note_id}/validate")
async def validate_note_content(note_id: str = Path(..., description="Note ID")):
    """Validate note content and check for broken links."""
    try:
        note = await notes_service.get_note(note_id)
        links = await notes_service.get_wiki_links(note_id)
        
        validation_result = {
            "note_id": note_id,
            "title": note.title,
            "word_count": note.word_count,
            "has_broken_links": len(links["broken_links"]) > 0,
            "broken_links": links["broken_links"],
            "valid_links": len(links["outgoing_links"]),
            "validation_status": "valid" if len(links["broken_links"]) == 0 else "has_issues"
        }
        
        return validation_result
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/{note_id}/links/create-bidirectional")
async def create_bidirectional_links(note_id: str = Path(..., description="Note ID")):
    """Create bidirectional links by automatically creating notes for broken links."""
    try:
        result = await notes_service.create_bidirectional_links(note_id)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bidirectional links: {str(e)}")


@router.get("/{note_id}/links/suggestions")
async def get_link_suggestions(
    note_id: str = Path(..., description="Note ID"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of suggestions")
):
    """Get link suggestions based on content similarity."""
    try:
        suggestions = await notes_service.suggest_links(note_id, limit=limit)
        return {
            "note_id": note_id,
            "suggestions": suggestions,
            "total": len(suggestions)
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get link suggestions: {str(e)}")


@router.post("/{note_id}/links/validate-all")
async def validate_all_links(note_id: str = Path(..., description="Note ID")):
    """Comprehensive link validation for a note."""
    try:
        validation = await notes_service.validate_all_links(note_id)
        return validation
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Link validation failed: {str(e)}")


@router.post("/{note_id}/links/auto-link")
async def auto_link_content(
    note_id: str = Path(..., description="Note ID"),
    min_similarity: float = Query(0.8, ge=0.1, le=1.0, description="Minimum similarity threshold")
):
    """Automatically add links to content based on existing note titles."""
    try:
        result = await notes_service.auto_link_content(note_id, min_similarity=min_similarity)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-linking failed: {str(e)}")
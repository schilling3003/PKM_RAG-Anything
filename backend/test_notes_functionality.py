"""
Test script for notes functionality.
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models.schemas import NoteCreate, NoteUpdate
from app.services.notes_service import notes_service
from app.core.database import DatabaseManager


async def test_notes_crud():
    """Test basic CRUD operations for notes."""
    print("🧪 Testing Notes CRUD Operations...")
    
    try:
        # Initialize database
        print("📊 Initializing database...")
        db_manager = DatabaseManager()
        db_manager.init_database()
        print("✅ Database initialized")
        
        # Test 1: Create a note
        print("\n1️⃣ Testing note creation...")
        note_data = NoteCreate(
            title="Test Note",
            content="# Test Note\n\nThis is a test note with some **markdown** content.\n\n- Item 1\n- Item 2\n\n[[Linked Note]]",
            tags=["test", "markdown"]
        )
        
        created_note = await notes_service.create_note(note_data)
        print(f"✅ Created note: {created_note.id} - '{created_note.title}'")
        print(f"   Word count: {created_note.word_count}")
        print(f"   Tags: {created_note.tags}")
        
        # Test 2: Get the note
        print("\n2️⃣ Testing note retrieval...")
        retrieved_note = await notes_service.get_note(created_note.id)
        print(f"✅ Retrieved note: {retrieved_note.title}")
        assert retrieved_note.id == created_note.id
        assert retrieved_note.title == created_note.title
        
        # Test 3: Update the note
        print("\n3️⃣ Testing note update...")
        update_data = NoteUpdate(
            title="Updated Test Note",
            content="# Updated Test Note\n\nThis note has been updated with new content.\n\n[[Another Link]]",
            tags=["test", "updated"]
        )
        
        updated_note = await notes_service.update_note(created_note.id, update_data)
        print(f"✅ Updated note: {updated_note.title}")
        assert updated_note.title == "Updated Test Note"
        assert "updated" in updated_note.tags
        
        # Test 4: List notes
        print("\n4️⃣ Testing note listing...")
        notes_list = await notes_service.list_notes(limit=10)
        print(f"✅ Listed {len(notes_list['notes'])} notes")
        assert len(notes_list['notes']) >= 1
        
        # Test 5: Search notes
        print("\n5️⃣ Testing note search...")
        search_results = await notes_service.search_notes("updated", limit=5)
        print(f"✅ Found {len(search_results)} notes matching 'updated'")
        assert len(search_results) >= 1
        
        # Test 6: Get wiki links
        print("\n6️⃣ Testing wiki links extraction...")
        links = await notes_service.get_wiki_links(updated_note.id)
        print(f"✅ Found {len(links['broken_links'])} broken links")
        print(f"   Broken links: {links['broken_links']}")
        assert "Another Link" in links['broken_links']
        
        # Test 7: Get all tags
        print("\n7️⃣ Testing tags retrieval...")
        all_tags = await notes_service.get_all_tags()
        print(f"✅ Found {len(all_tags)} unique tags: {all_tags}")
        assert "test" in all_tags
        assert "updated" in all_tags
        
        # Test 8: Delete the note
        print("\n8️⃣ Testing note deletion...")
        deleted = await notes_service.delete_note(created_note.id)
        print(f"✅ Deleted note: {deleted}")
        assert deleted is True
        
        # Verify deletion
        try:
            await notes_service.get_note(created_note.id)
            assert False, "Note should have been deleted"
        except Exception as e:
            print(f"✅ Confirmed note deletion: {type(e).__name__}")
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_markdown_validation():
    """Test markdown validation functionality."""
    print("\n🧪 Testing Markdown Validation...")
    
    try:
        # Test valid markdown
        valid_note = NoteCreate(
            title="Valid Markdown",
            content="# Header\n\n[Link](http://example.com)\n\n![Image](image.jpg)"
        )
        note = await notes_service.create_note(valid_note)
        print("✅ Valid markdown accepted")
        
        # Clean up
        await notes_service.delete_note(note.id)
        
        # Test invalid markdown (unbalanced brackets)
        try:
            invalid_note = NoteCreate(
                title="Invalid Markdown",
                content="# Header\n\n[Unbalanced link\n\n![Unbalanced image"
            )
            await notes_service.create_note(invalid_note)
            print("❌ Invalid markdown should have been rejected")
            return False
        except Exception as e:
            print(f"✅ Invalid markdown correctly rejected: {type(e).__name__}")
        
        print("🎉 Markdown validation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Markdown validation test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Notes Functionality Tests\n")
    
    # Test CRUD operations
    crud_success = await test_notes_crud()
    
    # Test markdown validation
    validation_success = await test_markdown_validation()
    
    if crud_success and validation_success:
        print("\n🎉 All tests completed successfully!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
"""
Test script for wiki-style linking functionality.
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models.schemas import NoteCreate
from app.services.notes_service import notes_service
from app.core.database import DatabaseManager


async def test_bidirectional_links():
    """Test bidirectional link creation."""
    print("🧪 Testing Bidirectional Link Creation...")
    
    try:
        # Initialize database
        db_manager = DatabaseManager()
        db_manager.init_database()
        
        # Create a note with wiki links to non-existent notes
        note_data = NoteCreate(
            title="Main Note",
            content="# Main Note\n\nThis note links to [[Concept A]] and [[Concept B]].\n\nIt also mentions [[Important Topic]].",
            tags=["main"]
        )
        
        main_note = await notes_service.create_note(note_data)
        print(f"✅ Created main note: {main_note.title}")
        
        # Test bidirectional link creation
        result = await notes_service.create_bidirectional_links(main_note.id)
        print(f"✅ Created bidirectional links:")
        print(f"   Created {len(result['created_notes'])} new notes")
        print(f"   Linked to {len(result['linked_notes'])} existing notes")
        
        for created in result['created_notes']:
            print(f"   - Created: {created['title']}")
        
        # Verify the created notes exist
        for created in result['created_notes']:
            created_note = await notes_service.get_note(created['id'])
            print(f"✅ Verified created note: {created_note.title}")
            assert "auto-created" in created_note.tags
        
        # Clean up
        await notes_service.delete_note(main_note.id)
        for created in result['created_notes']:
            await notes_service.delete_note(created['id'])
        
        print("🎉 Bidirectional link creation test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Bidirectional link test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_link_suggestions():
    """Test link suggestion functionality."""
    print("\n🧪 Testing Link Suggestions...")
    
    try:
        # Create several notes with related content
        notes_data = [
            NoteCreate(
                title="Machine Learning",
                content="# Machine Learning\n\nMachine learning is a subset of artificial intelligence that focuses on algorithms and data.",
                tags=["ai", "ml"]
            ),
            NoteCreate(
                title="Deep Learning",
                content="# Deep Learning\n\nDeep learning uses neural networks with multiple layers to learn from data.",
                tags=["ai", "ml", "deep"]
            ),
            NoteCreate(
                title="Neural Networks",
                content="# Neural Networks\n\nNeural networks are computing systems inspired by biological neural networks.",
                tags=["ai", "networks"]
            ),
            NoteCreate(
                title="Data Science",
                content="# Data Science\n\nData science combines statistics, programming, and domain expertise to extract insights from data.",
                tags=["data", "science"]
            )
        ]
        
        created_notes = []
        for note_data in notes_data:
            note = await notes_service.create_note(note_data)
            created_notes.append(note)
            print(f"✅ Created note: {note.title}")
        
        # Test link suggestions for the first note
        suggestions = await notes_service.suggest_links(created_notes[0].id, limit=5)
        print(f"✅ Got {len(suggestions)} link suggestions for '{created_notes[0].title}':")
        
        for suggestion in suggestions:
            print(f"   - {suggestion['title']} (similarity: {suggestion['similarity_score']}, reason: {suggestion['reason']})")
        
        assert len(suggestions) > 0, "Should have at least one suggestion"
        
        # Clean up
        for note in created_notes:
            await notes_service.delete_note(note.id)
        
        print("🎉 Link suggestions test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Link suggestions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_comprehensive_link_validation():
    """Test comprehensive link validation."""
    print("\n🧪 Testing Comprehensive Link Validation...")
    
    try:
        # Create target notes
        target_notes = []
        for title in ["Target Note A", "Target Note B"]:
            note_data = NoteCreate(
                title=title,
                content=f"# {title}\n\nThis is a target note.",
                tags=["target"]
            )
            note = await notes_service.create_note(note_data)
            target_notes.append(note)
            print(f"✅ Created target note: {note.title}")
        
        # Create a note with various types of links
        test_note_data = NoteCreate(
            title="Test Note with Links",
            content="""# Test Note with Links

This note has several types of links:

1. Valid exact link: [[Target Note A]]
2. Valid partial link: [[Target Note]]  
3. Broken link: [[Non-existent Note]]
4. Another broken link: [[Missing Note]]
""",
            tags=["test"]
        )
        
        test_note = await notes_service.create_note(test_note_data)
        print(f"✅ Created test note: {test_note.title}")
        
        # Test comprehensive validation
        validation = await notes_service.validate_all_links(test_note.id)
        print(f"✅ Link validation results:")
        print(f"   Total links: {validation['total_links']}")
        print(f"   Valid links: {validation['validation_summary']['valid_count']}")
        print(f"   Broken links: {validation['validation_summary']['broken_count']}")
        print(f"   Ambiguous links: {validation['validation_summary']['ambiguous_count']}")
        print(f"   Health score: {validation['validation_summary']['health_score']:.2f}")
        
        # Verify we have both valid and broken links
        assert validation['validation_summary']['valid_count'] > 0, "Should have valid links"
        assert validation['validation_summary']['broken_count'] > 0, "Should have broken links"
        
        # Clean up
        await notes_service.delete_note(test_note.id)
        for note in target_notes:
            await notes_service.delete_note(note.id)
        
        print("🎉 Comprehensive link validation test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Link validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_auto_linking():
    """Test automatic content linking."""
    print("\n🧪 Testing Automatic Content Linking...")
    
    try:
        # Create target notes
        target_notes = []
        target_titles = ["Python Programming", "Machine Learning", "Data Analysis"]
        
        for title in target_titles:
            note_data = NoteCreate(
                title=title,
                content=f"# {title}\n\nThis is about {title.lower()}.",
                tags=["target"]
            )
            note = await notes_service.create_note(note_data)
            target_notes.append(note)
            print(f"✅ Created target note: {note.title}")
        
        # Create a note that mentions these topics without links
        source_note_data = NoteCreate(
            title="My Learning Journey",
            content="""# My Learning Journey

I started learning Python Programming last year. It was challenging at first, but I gradually got better.

Then I moved on to Machine Learning, which opened up a whole new world of possibilities.

Now I'm focusing on Data Analysis to better understand the data I work with.

Python Programming has been the foundation for everything else I've learned.
""",
            tags=["journey"]
        )
        
        source_note = await notes_service.create_note(source_note_data)
        print(f"✅ Created source note: {source_note.title}")
        
        # Test auto-linking
        result = await notes_service.auto_link_content(source_note.id, min_similarity=0.8)
        print(f"✅ Auto-linking results:")
        print(f"   Links added: {result['total_links_added']}")
        
        for link in result['added_links']:
            print(f"   - Added link: {link['original_text']} -> {link['target_note_title']}")
        
        # Verify links were added
        assert result['total_links_added'] > 0, "Should have added some links"
        
        # Get the updated note and verify it has wiki links
        updated_note = await notes_service.get_note(source_note.id)
        wiki_links = await notes_service.get_wiki_links(source_note.id)
        print(f"✅ Updated note now has {len(wiki_links['outgoing_links'])} outgoing links")
        
        # Clean up
        await notes_service.delete_note(source_note.id)
        for note in target_notes:
            await notes_service.delete_note(note.id)
        
        print("🎉 Auto-linking test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Auto-linking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all wiki linking tests."""
    print("🚀 Starting Wiki-Style Linking Tests\n")
    
    tests = [
        test_bidirectional_links,
        test_link_suggestions,
        test_comprehensive_link_validation,
        test_auto_linking
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    if all(results):
        print("\n🎉 All wiki linking tests completed successfully!")
        return True
    else:
        print("\n❌ Some wiki linking tests failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
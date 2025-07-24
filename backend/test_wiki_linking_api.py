"""
Test script for wiki-style linking API endpoints.
"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import DatabaseManager


def test_wiki_linking_api():
    """Test wiki linking API endpoints."""
    print("🧪 Testing Wiki Linking API Endpoints...")
    
    try:
        # Initialize database
        print("📊 Initializing database...")
        db_manager = DatabaseManager()
        db_manager.init_database()
        print("✅ Database initialized")
        
        # Create test client
        client = TestClient(app)
        
        # Test 1: Create notes with wiki links
        print("\n1️⃣ Creating notes with wiki links...")
        main_note_data = {
            "title": "Main Note",
            "content": "# Main Note\n\nThis note links to [[Concept A]] and [[Concept B]].\n\nIt also mentions [[Important Topic]].",
            "tags": ["main"]
        }
        
        response = client.post("/api/v1/notes/", json=main_note_data)
        assert response.status_code == 201
        main_note = response.json()
        main_note_id = main_note["id"]
        print(f"✅ Created main note: {main_note_id}")
        
        # Test 2: Create bidirectional links
        print("\n2️⃣ Testing bidirectional link creation...")
        response = client.post(f"/api/v1/notes/{main_note_id}/links/create-bidirectional")
        assert response.status_code == 200
        bidirectional_result = response.json()
        print(f"✅ Created {len(bidirectional_result['created_notes'])} bidirectional links")
        
        created_note_ids = [note['id'] for note in bidirectional_result['created_notes']]
        
        # Test 3: Get link suggestions
        print("\n3️⃣ Testing link suggestions...")
        response = client.get(f"/api/v1/notes/{main_note_id}/links/suggestions?limit=5")
        assert response.status_code == 200
        suggestions = response.json()
        print(f"✅ Got {len(suggestions['suggestions'])} link suggestions")
        
        # Test 4: Comprehensive link validation
        print("\n4️⃣ Testing comprehensive link validation...")
        response = client.post(f"/api/v1/notes/{main_note_id}/links/validate-all")
        assert response.status_code == 200
        validation = response.json()
        print(f"✅ Link validation completed:")
        print(f"   Total links: {validation['total_links']}")
        print(f"   Valid links: {validation['validation_summary']['valid_count']}")
        print(f"   Health score: {validation['validation_summary']['health_score']:.2f}")
        
        # Test 5: Create a note for auto-linking test
        print("\n5️⃣ Testing auto-linking...")
        source_note_data = {
            "title": "Learning Journey",
            "content": "# Learning Journey\n\nI've been studying Concept A and Concept B extensively.\n\nThe Important Topic is also very relevant to my work.",
            "tags": ["journey"]
        }
        
        response = client.post("/api/v1/notes/", json=source_note_data)
        assert response.status_code == 201
        source_note = response.json()
        source_note_id = source_note["id"]
        print(f"✅ Created source note: {source_note_id}")
        
        # Test auto-linking
        response = client.post(f"/api/v1/notes/{source_note_id}/links/auto-link?min_similarity=0.8")
        assert response.status_code == 200
        auto_link_result = response.json()
        print(f"✅ Auto-linking added {auto_link_result['total_links_added']} links")
        
        # Test 6: Get backlinks
        print("\n6️⃣ Testing backlinks...")
        if created_note_ids:
            response = client.get(f"/api/v1/notes/{created_note_ids[0]}/backlinks")
            assert response.status_code == 200
            backlinks = response.json()
            print(f"✅ Found {len(backlinks['backlinks'])} backlinks")
        
        # Clean up
        print("\n🧹 Cleaning up...")
        client.delete(f"/api/v1/notes/{main_note_id}")
        client.delete(f"/api/v1/notes/{source_note_id}")
        for note_id in created_note_ids:
            client.delete(f"/api/v1/notes/{note_id}")
        print("✅ Cleanup completed")
        
        print("\n🎉 All wiki linking API tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Wiki linking API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling for wiki linking endpoints."""
    print("\n🧪 Testing Wiki Linking API Error Handling...")
    
    try:
        client = TestClient(app)
        
        # Test 1: Non-existent note
        print("\n1️⃣ Testing 404 errors...")
        response = client.post("/api/v1/notes/non-existent-id/links/create-bidirectional")
        assert response.status_code == 404
        print("✅ 404 error handled correctly for bidirectional links")
        
        response = client.get("/api/v1/notes/non-existent-id/links/suggestions")
        assert response.status_code == 404
        print("✅ 404 error handled correctly for link suggestions")
        
        response = client.post("/api/v1/notes/non-existent-id/links/validate-all")
        assert response.status_code == 404
        print("✅ 404 error handled correctly for link validation")
        
        response = client.post("/api/v1/notes/non-existent-id/links/auto-link")
        assert response.status_code == 404
        print("✅ 404 error handled correctly for auto-linking")
        
        # Test 2: Invalid parameters
        print("\n2️⃣ Testing invalid parameters...")
        # Create a test note first
        note_data = {
            "title": "Test Note",
            "content": "Test content",
            "tags": []
        }
        response = client.post("/api/v1/notes/", json=note_data)
        assert response.status_code == 201
        note_id = response.json()["id"]
        
        # Test invalid limit parameter
        response = client.get(f"/api/v1/notes/{note_id}/links/suggestions?limit=0")
        assert response.status_code == 422
        print("✅ Validation error handled correctly for invalid limit")
        
        # Test invalid similarity parameter
        response = client.post(f"/api/v1/notes/{note_id}/links/auto-link?min_similarity=2.0")
        assert response.status_code == 422
        print("✅ Validation error handled correctly for invalid similarity")
        
        # Clean up
        client.delete(f"/api/v1/notes/{note_id}")
        
        print("\n🎉 Error handling tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error handling test failed: {e}")
        return False


def main():
    """Run all wiki linking API tests."""
    print("🚀 Starting Wiki Linking API Tests\n")
    
    # Test main functionality
    api_success = test_wiki_linking_api()
    
    # Test error handling
    error_success = test_error_handling()
    
    if api_success and error_success:
        print("\n🎉 All wiki linking API tests completed successfully!")
        return True
    else:
        print("\n❌ Some wiki linking API tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""
Test script for notes API endpoints.
"""

import asyncio
import sys
import os
import json
from typing import Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import DatabaseManager


def test_notes_api():
    """Test notes API endpoints using TestClient."""
    print("🧪 Testing Notes API Endpoints...")
    
    try:
        # Initialize database
        print("📊 Initializing database...")
        db_manager = DatabaseManager()
        db_manager.init_database()
        print("✅ Database initialized")
        
        # Create test client
        client = TestClient(app)
        
        # Test 1: Health check
        print("\n1️⃣ Testing API health check...")
        response = client.get("/health")
        assert response.status_code == 200
        health_data = response.json()
        print(f"✅ API health: {health_data['status']}")
        
        # Test 2: Create a note
        print("\n2️⃣ Testing note creation...")
        note_data = {
            "title": "API Test Note",
            "content": "# API Test Note\n\nThis note was created via API.\n\n- Feature 1\n- Feature 2\n\n[[Linked Note]]",
            "tags": ["api", "test"]
        }
        
        response = client.post("/api/v1/notes/", json=note_data)
        assert response.status_code == 201
        created_note = response.json()
        note_id = created_note["id"]
        print(f"✅ Created note via API: {note_id}")
        print(f"   Title: {created_note['title']}")
        print(f"   Word count: {created_note['word_count']}")
        
        # Test 3: Get the note
        print("\n3️⃣ Testing note retrieval...")
        response = client.get(f"/api/v1/notes/{note_id}")
        assert response.status_code == 200
        retrieved_note = response.json()
        print(f"✅ Retrieved note: {retrieved_note['title']}")
        assert retrieved_note["id"] == note_id
        
        # Test 4: Update the note
        print("\n4️⃣ Testing note update...")
        update_data = {
            "title": "Updated API Test Note",
            "content": "# Updated API Test Note\n\nThis note has been updated via API.\n\n[[Another Link]]",
            "tags": ["api", "test", "updated"]
        }
        
        response = client.put(f"/api/v1/notes/{note_id}", json=update_data)
        assert response.status_code == 200
        updated_note = response.json()
        print(f"✅ Updated note: {updated_note['title']}")
        assert "updated" in updated_note["tags"]
        
        # Test 5: List notes
        print("\n5️⃣ Testing note listing...")
        response = client.get("/api/v1/notes/")
        assert response.status_code == 200
        notes_list = response.json()
        print(f"✅ Listed {len(notes_list['notes'])} notes")
        assert notes_list["total"] >= 1
        
        # Test 6: Search notes
        print("\n6️⃣ Testing note search...")
        response = client.get("/api/v1/notes/search/query?q=updated&limit=5")
        assert response.status_code == 200
        search_results = response.json()
        print(f"✅ Found {len(search_results['results'])} notes matching 'updated'")
        assert len(search_results["results"]) >= 1
        
        # Test 7: Get note links
        print("\n7️⃣ Testing wiki links...")
        response = client.get(f"/api/v1/notes/{note_id}/links")
        assert response.status_code == 200
        links = response.json()
        print(f"✅ Found {len(links['broken_links'])} broken links")
        assert "Another Link" in links["broken_links"]
        
        # Test 8: Get all tags
        print("\n8️⃣ Testing tags retrieval...")
        response = client.get("/api/v1/notes/tags/all")
        assert response.status_code == 200
        tags_data = response.json()
        print(f"✅ Found {len(tags_data['tags'])} unique tags: {tags_data['tags']}")
        assert "api" in tags_data["tags"]
        assert "test" in tags_data["tags"]
        
        # Test 9: Validate note content
        print("\n9️⃣ Testing note validation...")
        response = client.post(f"/api/v1/notes/{note_id}/validate")
        assert response.status_code == 200
        validation = response.json()
        print(f"✅ Validation status: {validation['validation_status']}")
        print(f"   Broken links: {validation['broken_links']}")
        
        # Test 10: Delete the note
        print("\n🔟 Testing note deletion...")
        response = client.delete(f"/api/v1/notes/{note_id}")
        assert response.status_code == 200
        delete_result = response.json()
        print(f"✅ Deleted note: {delete_result['success']}")
        
        # Verify deletion
        response = client.get(f"/api/v1/notes/{note_id}")
        assert response.status_code == 404
        print("✅ Confirmed note deletion")
        
        print("\n🎉 All API tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test API error handling."""
    print("\n🧪 Testing API Error Handling...")
    
    try:
        client = TestClient(app)
        
        # Test 1: Get non-existent note
        print("\n1️⃣ Testing 404 error...")
        response = client.get("/api/v1/notes/non-existent-id")
        assert response.status_code == 404
        error_data = response.json()
        print(f"✅ 404 error handled correctly: {error_data}")
        
        # Test 2: Invalid note data
        print("\n2️⃣ Testing validation error...")
        invalid_data = {
            "title": "",  # Empty title should fail
            "content": "Some content"
        }
        response = client.post("/api/v1/notes/", json=invalid_data)
        assert response.status_code == 422
        print("✅ Validation error handled correctly")
        
        # Test 3: Invalid search parameters
        print("\n3️⃣ Testing invalid search...")
        response = client.get("/api/v1/notes/search/query?q=&limit=0")
        assert response.status_code == 422
        print("✅ Invalid search parameters handled correctly")
        
        print("\n🎉 Error handling tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error handling test failed: {e}")
        return False


def main():
    """Run all API tests."""
    print("🚀 Starting Notes API Tests\n")
    
    # Test main API functionality
    api_success = test_notes_api()
    
    # Test error handling
    error_success = test_error_handling()
    
    if api_success and error_success:
        print("\n🎉 All API tests completed successfully!")
        return True
    else:
        print("\n❌ Some API tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
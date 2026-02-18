"""Tests for Mergington High School API endpoints"""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_activities_contains_expected_activities(self, client):
        """Test that GET /activities contains expected activities"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Soccer Team", "Swimming Club", "Drama Club", 
            "Art Studio", "Science Club", "Debate Team",
            "Chess Club", "Programming Class", "Gym Class"
        ]
        
        for activity in expected_activities:
            assert activity in data
    
    def test_get_activities_structure(self, client):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_existing_activity(self, client):
        """Test signing up for an existing activity"""
        response = client.post(
            "/activities/Soccer Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Soccer Team" in data["message"]
    
    def test_signup_adds_student_to_participants(self, client):
        """Test that signup actually adds the student to participants list"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Soccer Team/signup?email={email}")
        
        # Verify student was added
        response = client.get("/activities")
        data = response.json()
        assert email in data["Soccer Team"]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_student(self, client):
        """Test that signing up the same student twice returns 400"""
        email = "alex@mergington.edu"  # Already in Soccer Team
        response = client.post(f"/activities/Soccer Team/signup?email={email}")
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_students(self, client):
        """Test signing up multiple different students"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(f"/activities/Drama Club/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all students were added
        response = client.get("/activities")
        data = response.json()
        for email in emails:
            assert email in data["Drama Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_from_activity(self, client):
        """Test unregistering from an activity"""
        email = "alex@mergington.edu"  # Already in Soccer Team
        response = client.delete(f"/activities/Soccer Team/unregister?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Soccer Team" in data["message"]
    
    def test_unregister_removes_student_from_participants(self, client):
        """Test that unregister actually removes the student from participants list"""
        email = "alex@mergington.edu"  # Already in Soccer Team
        client.delete(f"/activities/Soccer Team/unregister?email={email}")
        
        # Verify student was removed
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Soccer Team"]["participants"]
    
    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregistering from a non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_student_not_signed_up(self, client):
        """Test unregistering a student who is not signed up returns 400"""
        email = "notsignedup@mergington.edu"
        response = client.delete(f"/activities/Soccer Team/unregister?email={email}")
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_signup_then_unregister(self, client):
        """Test the full flow of signing up and then unregistering"""
        email = "newstudent@mergington.edu"
        
        # Signup
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
        
        # Unregister
        response = client.delete(f"/activities/Chess Club/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify unregistered
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]


class TestActivityIsolation:
    """Tests to ensure activity data isolation between tests"""
    
    def test_activities_reset_between_tests_1(self, client):
        """First test - modify activities"""
        client.post("/activities/Soccer Team/signup?email=test1@mergington.edu")
        response = client.get("/activities")
        data = response.json()
        assert "test1@mergington.edu" in data["Soccer Team"]["participants"]
    
    def test_activities_reset_between_tests_2(self, client):
        """Second test - verify activities were reset"""
        response = client.get("/activities")
        data = response.json()
        # This email should not exist if reset worked properly
        assert "test1@mergington.edu" not in data["Soccer Team"]["participants"]

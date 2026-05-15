import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Arrange: Initialize test client"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_state = {
        k: {"participants": v["participants"].copy()} 
        for k, v in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for activity_name, data in original_state.items():
        activities[activity_name]["participants"] = data["participants"].copy()


class TestGetActivities:
    def test_get_all_activities(self, client):
        """Test: GET /activities returns all activities"""
        # Arrange: client ready
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activities_have_required_fields(self, client):
        """Test: Each activity has required fields"""
        # Arrange: client ready
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignup:
    def test_signup_successful(self, client, reset_activities):
        """Test: Student can successfully sign up for an activity"""
        # Arrange
        activity_name = "Basketball Team"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert activity_name in response.json()["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]

    def test_signup_multiple_students(self, client, reset_activities):
        """Test: Multiple students can sign up for the same activity"""
        # Arrange
        activity_name = "Soccer Club"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Act
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both were added
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants

    def test_signup_duplicate_email(self, client, reset_activities):
        """Test: Student cannot sign up twice for the same activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test: Cannot sign up for an activity that doesn't exist"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestUnregister:
    def test_unregister_successful(self, client, reset_activities):
        """Test: Student can successfully unregister from an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert activity_name in response.json()["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]

    def test_unregister_not_signed_up(self, client):
        """Test: Cannot unregister if not currently signed up"""
        # Arrange
        activity_name = "Basketball Team"
        email = "test@mergington.edu"  # Not signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_nonexistent_activity(self, client):
        """Test: Cannot unregister from an activity that doesn't exist"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_signup_then_unregister(self, client, reset_activities):
        """Test: Student can sign up and then unregister"""
        # Arrange
        activity_name = "Art Studio"
        email = "test@mergington.edu"
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert signup
        assert signup_response.status_code == 200
        
        # Act - Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert unregister
        assert unregister_response.status_code == 200
        
        # Verify not in participants
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]

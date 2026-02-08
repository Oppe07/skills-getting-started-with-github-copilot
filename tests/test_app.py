"""Tests for Mergington High School API"""

import pytest


def test_root_redirect(client):
    """Test that root redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    activities = response.json()
    assert isinstance(activities, dict)
    assert "Basketball" in activities
    assert "Soccer" in activities
    assert "Programming Class" in activities
    
    # Check structure of an activity
    basketball = activities["Basketball"]
    assert "description" in basketball
    assert "schedule" in basketball
    assert "max_participants" in basketball
    assert "participants" in basketball
    assert isinstance(basketball["participants"], list)


def test_get_activities_contains_participants(client):
    """Test that activities contain initial participants"""
    response = client.get("/activities")
    activities = response.json()
    
    # Check that some activities have participants
    assert len(activities["Basketball"]["participants"]) > 0
    assert "alex@mergington.edu" in activities["Basketball"]["participants"]
    assert len(activities["Soccer"]["participants"]) > 0


def test_signup_for_activity(client, reset_activities):
    """Test signing up a new participant for an activity"""
    response = client.post(
        "/activities/Basketball/signup",
        params={"email": "newstudent@mergington.edu"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert "newstudent@mergington.edu" in result["message"]
    assert "Basketball" in result["message"]
    
    # Verify the participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "newstudent@mergington.edu" in activities["Basketball"]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signing up for an activity that doesn't exist"""
    response = client.post(
        "/activities/NonexistentActivity/signup",
        params={"email": "student@mergington.edu"}
    )
    
    assert response.status_code == 404
    result = response.json()
    assert "Activity not found" in result["detail"]


def test_signup_same_participant_multiple_times(client, reset_activities):
    """Test that the same participant can be added multiple times (duplicate)"""
    # Sign up first time
    response1 = client.post(
        "/activities/Basketball/signup",
        params={"email": "duplicate@mergington.edu"}
    )
    assert response1.status_code == 200
    
    # Sign up the same person again
    response2 = client.post(
        "/activities/Basketball/signup",
        params={"email": "duplicate@mergington.edu"}
    )
    assert response2.status_code == 200
    
    # Check that they appear twice in the list
    activities_response = client.get("/activities")
    activities = activities_response.json()
    basketball_participants = activities["Basketball"]["participants"]
    assert basketball_participants.count("duplicate@mergington.edu") == 2


def test_unregister_participant(client, reset_activities):
    """Test unregistering a participant from an activity"""
    # First, add a participant
    client.post(
        "/activities/Basketball/signup",
        params={"email": "toremove@mergington.edu"}
    )
    
    # Verify they are there
    activities_response = client.get("/activities")
    assert "toremove@mergington.edu" in activities_response.json()["Basketball"]["participants"]
    
    # Now unregister them
    response = client.delete(
        "/activities/Basketball/unregister",
        params={"email": "toremove@mergington.edu"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "toremove@mergington.edu" in result["message"]
    assert "Unregistered" in result["message"]
    
    # Verify they are removed
    activities_response = client.get("/activities")
    assert "toremove@mergington.edu" not in activities_response.json()["Basketball"]["participants"]


def test_unregister_nonexistent_participant(client, reset_activities):
    """Test unregistering a participant that doesn't exist in an activity"""
    response = client.delete(
        "/activities/Basketball/unregister",
        params={"email": "nonexistent@mergington.edu"}
    )
    
    assert response.status_code == 404
    result = response.json()
    assert "Student not found in this activity" in result["detail"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregistering from an activity that doesn't exist"""
    response = client.delete(
        "/activities/NonexistentActivity/unregister",
        params={"email": "student@mergington.edu"}
    )
    
    assert response.status_code == 404
    result = response.json()
    assert "Activity not found" in result["detail"]


def test_unregister_existing_participant(client, reset_activities):
    """Test unregistering an initially registered participant"""
    # Basketball has alex@mergington.edu as a participant
    response = client.delete(
        "/activities/Basketball/unregister",
        params={"email": "alex@mergington.edu"}
    )
    
    assert response.status_code == 200
    
    # Verify removal
    activities_response = client.get("/activities")
    assert "alex@mergington.edu" not in activities_response.json()["Basketball"]["participants"]


def test_signup_and_unregister_multiple_participants(client, reset_activities):
    """Test signing up and unregistering multiple participants"""
    emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
    
    # Sign up all students
    for email in emails:
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Verify all are signed up
    activities_response = client.get("/activities")
    for email in emails:
        assert email in activities_response.json()["Chess Club"]["participants"]
    
    # Unregister the middle student
    response = client.delete(
        "/activities/Chess Club/unregister",
        params={"email": emails[1]}
    )
    assert response.status_code == 200
    
    # Verify only middle student is removed
    activities_response = client.get("/activities")
    participants = activities_response.json()["Chess Club"]["participants"]
    assert emails[0] in participants
    assert emails[1] not in participants
    assert emails[2] in participants

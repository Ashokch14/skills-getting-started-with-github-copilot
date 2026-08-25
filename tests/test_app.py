import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original))


def test_root_redirects_to_static_index():
    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data():
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["participants"]


def test_signup_adds_student_and_avoids_duplicates():
    # Arrange
    activity_name = "Soccer Team"
    email = "newstudent@mergington.edu"

    # Act - successful signup
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert - first signup succeeds
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]

    # Act - duplicate signup
    duplicate_response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert - duplicate rejected
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Student is already signed up for this activity"

    activities[activity_name]["participants"].remove(email)


def test_signup_rejects_full_activity():
    # Arrange
    activity_name = "Basketball Club"
    activity = activities[activity_name]
    activity["participants"] = [
        "student1@mergington.edu",
        "student2@mergington.edu",
        "student3@mergington.edu",
        "student4@mergington.edu",
        "student5@mergington.edu",
        "student6@mergington.edu",
        "student7@mergington.edu",
        "student8@mergington.edu",
        "student9@mergington.edu",
        "student10@mergington.edu",
        "student11@mergington.edu",
        "student12@mergington.edu",
        "student13@mergington.edu",
        "student14@mergington.edu",
        "student15@mergington.edu",
    ]
    activity["max_participants"] = 15

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email=last@mergington.edu")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_remove_participant_unregisters_student():
    # Arrange
    activity_name = "Chess Club"
    email = "teststudent@mergington.edu"
    activities[activity_name]["participants"].append(email)

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    assert email not in activities[activity_name]["participants"]


def test_signup_404s_for_unknown_activity():
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_404s_for_unknown_activity():
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_404s_for_missing_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "nonexistent@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"

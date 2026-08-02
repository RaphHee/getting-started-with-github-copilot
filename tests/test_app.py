import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app, follow_redirects=False)

INITIAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_ACTIVITIES))
    yield
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_ACTIVITIES))


# --- GET / ---

def test_root_redirects_to_index():
    response = client.get("/")
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"].endswith("/static/index.html")


# --- GET /activities ---

def test_get_activities_returns_all():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 9


def test_get_activities_contain_required_fields():
    response = client.get("/activities")
    data = response.json()
    for name, activity in data.items():
        assert "description" in activity, f"{name} missing 'description'"
        assert "schedule" in activity, f"{name} missing 'schedule'"
        assert "max_participants" in activity, f"{name} missing 'max_participants'"
        assert "participants" in activity, f"{name} missing 'participants'"


# --- POST /activities/{name}/signup ---

def test_signup_success():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 200
    assert "message" in response.json()
    assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_already_registered_returns_400():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_unknown_activity_returns_404():
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


# --- DELETE /activities/{name}/participants ---

def test_unregister_success():
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 200
    assert "message" in response.json()
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_unregister_not_signed_up_returns_404():
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "nobody@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not signed up for this activity"


def test_unregister_unknown_activity_returns_404():
    response = client.delete(
        "/activities/Unknown Activity/participants",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"

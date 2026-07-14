import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.database.session import Base, get_db
from app.auth.security import get_password_hash, verify_password, create_access_token
from app.models.user import User

# Test SQLite Engine for unit tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_password_hashing():
    password = "secret_password"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)

def test_token_creation():
    email = "test@example.com"
    role = "member"
    token = create_access_token(email, role)
    assert token is not None
    assert isinstance(token, str)

def test_user_registration(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "full_name": "New User", "role": "member", "password": "newpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert data["role"] == "member"
    assert "id" in data
    assert data["is_active"] is True

def test_duplicate_registration_fails(client):
    # Register once
    client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "full_name": "First User", "role": "member", "password": "password"}
    )
    # Register again with same email
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "full_name": "Second User", "role": "member", "password": "password"}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_json(client):
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "full_name": "Login User", "role": "member", "password": "correct_password"}
    )
    # Login
    response = client.post(
        "/api/v1/auth/login-json",
        data={"username": "login@example.com", "password": "correct_password"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_unauthorized_member_access(client):
    response = client.get("/member")
    # Redirects because client accepts HTML by default or falls back
    # Let's check when asking specifically for JSON, we get 401
    response = client.get("/member", headers={"accept": "application/json"})
    assert response.status_code == 401


def test_member_profile_update_endpoint(client):
    user_payload = {
        "email": "profile@example.com",
        "full_name": "Profile User",
        "role": "member",
        "password": "password123"
    }
    client.post("/api/v1/auth/register", json=user_payload)
    login_response = client.post(
        "/api/v1/auth/login-json",
        data={"username": user_payload["email"], "password": user_payload["password"]}
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/members/me/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"height": 180.0, "weight": 78.5, "fitness_goal": "muscle_gain"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["height"] == 180.0
    assert data["weight"] == 78.5
    assert data["fitness_goal"] == "muscle_gain"


def test_admin_stats_and_user_listing(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "admin_test@example.com", "full_name": "Admin Test", "role": "admin", "password": "password123"}
    )
    client.post(
        "/api/v1/auth/register",
        json={"email": "trainer_test@example.com", "full_name": "Trainer Test", "role": "trainer", "password": "password123"}
    )
    client.post(
        "/api/v1/auth/register",
        json={"email": "member_test@example.com", "full_name": "Member Test", "role": "member", "password": "password123"}
    )
    login_response = client.post(
        "/api/v1/auth/login-json",
        data={"username": "admin_test@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]

    stats_response = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["total_members"] >= 1
    assert stats["total_trainers"] >= 1

    users_response = client.get("/api/v1/admin/users?role=trainer", headers={"Authorization": f"Bearer {token}"})
    assert users_response.status_code == 200
    users = users_response.json()["users"]
    assert any(u["email"] == "trainer_test@example.com" for u in users)


def test_member_summary_and_ai_coach(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "ai_member@example.com", "full_name": "AI Member", "role": "member", "password": "password123"}
    )
    login_response = client.post(
        "/api/v1/auth/login-json",
        data={"username": "ai_member@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]

    profile_response = client.get("/api/v1/members/me", headers={"Authorization": f"Bearer {token}"})
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["email"] == "ai_member@example.com"
    assert profile_data["profile"] is not None

    coach_response = client.post(
        "/api/v1/members/me/coach",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"message": "How much protein do I need?"}
    )
    assert coach_response.status_code == 200
    assert "protein" in coach_response.json()["message"].lower()


def test_trainer_plan_templates(client):
    # login as admin for access to trainer-plan creation endpoints
    client.post(
        "/api/v1/auth/register",
        json={"email": "plan_admin@example.com", "full_name": "Plan Admin", "role": "admin", "password": "password123"}
    )
    login_response = client.post(
        "/api/v1/auth/login-json",
        data={"username": "plan_admin@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]

    workout_resp = client.post(
        "/api/v1/admin/trainer-plans/workouts",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"plan_name": "Test Plan", "difficulty": "beginner", "duration_min": 45, "exercises": "Squat\nBench\nRow"}
    )
    assert workout_resp.status_code == 201
    assert workout_resp.json()["template"]["plan_name"] == "Test Plan"

    diet_resp = client.post(
        "/api/v1/admin/trainer-plans/diets",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"plan_name": "Cut Diet", "calories": 1800, "protein_g": 150, "carbs_g": 180, "fat_g": 60, "meals": "Meal1\nMeal2"}
    )
    assert diet_resp.status_code == 201
    assert diet_resp.json()["template"]["calories"] == 1800

    list_resp = client.get("/api/v1/admin/trainer-plans", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200
    assert any(plan["plan_name"] == "Test Plan" for plan in list_resp.json()["workout_templates"])
    assert any(plan["plan_name"] == "Cut Diet" for plan in list_resp.json()["diet_templates"])

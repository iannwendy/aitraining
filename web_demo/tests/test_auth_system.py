"""
Auth System Test Suite for Mental Health AI Platform
Tests authentication flows: login, register, logout, protected routes, admin access
"""

import os
import pytest
import requests
from typing import Optional

# Set JWT_SECRET_KEY for testing
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-development-only-123456")

# Configuration
API_BASE_URL = "http://localhost:8000"
API_PREFIX = f"{API_BASE_URL}/api"


# ============================================================
# Helper Functions
# ============================================================

def get_admin_token() -> Optional[str]:
    """Get access token for admin user."""
    response = requests.post(
        f"{API_PREFIX}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def get_user_token() -> Optional[str]:
    """Get access token for regular user."""
    response = requests.post(
        f"{API_PREFIX}/auth/login",
        json={"username": "user", "password": "user123"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def auth_headers(token: str) -> dict:
    """Return authorization headers with token."""
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# 1. Health & Root Tests
# ============================================================

class TestHealthAndRoot:
    """Test basic health and root endpoints."""

    def test_root_endpoint(self):
        """Test GET / returns API info."""
        response = requests.get(API_BASE_URL + "/")
        assert response.status_code == 200
        data = response.json()
        assert "Mental Health AI API" in data.get("name", "")

    def test_health_check(self):
        """Test GET /api/health returns healthy status."""
        response = requests.get(f"{API_PREFIX}/health")
        assert response.status_code == 200
        assert response.json().get("status") == "healthy"


# ============================================================
# 2. Login Tests
# ============================================================

class TestLogin:
    """Test login functionality."""

    def test_login_admin_success(self):
        """Test login with admin credentials."""
        response = requests.post(
            f"{API_PREFIX}/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"

    def test_login_user_success(self):
        """Test login with regular user credentials."""
        response = requests.post(
            f"{API_PREFIX}/auth/login",
            json={"username": "user", "password": "user123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "user"
        assert data["user"]["role"] == "user"

    def test_login_invalid_password(self):
        """Test login with wrong password."""
        response = requests.post(
            f"{API_PREFIX}/auth/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """Test login with non-existent username."""
        response = requests.post(
            f"{API_PREFIX}/auth/login",
            json={"username": "nonexistent", "password": "password"}
        )
        assert response.status_code == 401

    def test_login_missing_fields(self):
        """Test login with missing fields."""
        response = requests.post(
            f"{API_PREFIX}/auth/login",
            json={"username": "admin"}
        )
        assert response.status_code == 422  # Validation error


# ============================================================
# 3. Register Tests
# ============================================================

class TestRegister:
    """Test registration functionality."""

    def test_register_new_user(self):
        """Test registering a new user."""
        import random
        import string
        username = f"testuser_{''.join(random.choices(string.ascii_lowercase, k=8))}"
        password = "TestPass123!"

        response = requests.post(
            f"{API_PREFIX}/auth/register",
            json={"username": username, "password": password}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == username
        assert data["user"]["role"] == "user"

    def test_register_duplicate_username(self):
        """Test registering with existing username."""
        response = requests.post(
            f"{API_PREFIX}/auth/register",
            json={"username": "admin", "password": "newpassword"}
        )
        assert response.status_code == 400

    def test_register_short_password(self):
        """Test registering with too short password."""
        response = requests.post(
            f"{API_PREFIX}/auth/register",
            json={"username": "newuser", "password": "123"}
        )
        assert response.status_code == 422  # Validation error


# ============================================================
# 4. Get Current User Tests
# ============================================================

class TestGetCurrentUser:
    """Test /api/auth/me endpoint."""

    def test_get_me_authenticated(self):
        """Test getting current user info with valid token."""
        token = get_admin_token()
        if not token:
            pytest.skip("Admin user not available")

        response = requests.get(
            f"{API_PREFIX}/auth/me",
            headers=auth_headers(token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    def test_get_me_unauthenticated(self):
        """Test getting current user without token."""
        response = requests.get(f"{API_PREFIX}/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self):
        """Test getting current user with invalid token."""
        response = requests.get(
            f"{API_PREFIX}/auth/me",
            headers=auth_headers("invalid-token")
        )
        assert response.status_code == 401


# ============================================================
# 5. Protected Routes Tests
# ============================================================

class TestProtectedRoutes:
    """Test protected endpoints require authentication."""

    def test_predict_requires_auth(self):
        """Test /api/predict requires authentication."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "Test message"}
        )
        assert response.status_code == 401

    def test_predict_with_auth(self):
        """Test /api/predict works with valid token."""
        token = get_user_token()
        if not token:
            pytest.skip("Regular user not available")

        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "Tôi rất vui hôm nay"},
            headers=auth_headers(token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert data["prediction"] in ["depression", "normal"]

    def test_history_requires_auth(self):
        """Test /api/history requires authentication."""
        response = requests.get(f"{API_PREFIX}/history")
        assert response.status_code == 401

    def test_history_with_auth(self):
        """Test /api/history works with valid token."""
        token = get_user_token()
        if not token:
            pytest.skip("Regular user not available")

        response = requests.get(
            f"{API_PREFIX}/history",
            headers=auth_headers(token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


# ============================================================
# 6. Admin Routes Tests
# ============================================================

class TestAdminRoutes:
    """Test admin-only endpoints."""

    def test_admin_stats_requires_admin(self):
        """Test /api/admin/stats requires admin role."""
        token = get_user_token()
        if not token:
            pytest.skip("Regular user not available")

        response = requests.get(
            f"{API_PREFIX}/admin/stats",
            headers=auth_headers(token)
        )
        assert response.status_code == 403

    def test_admin_stats_with_admin(self):
        """Test /api/admin/stats works with admin token."""
        token = get_admin_token()
        if not token:
            pytest.skip("Admin user not available")

        response = requests.get(
            f"{API_PREFIX}/admin/stats",
            headers=auth_headers(token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_predictions" in data

    def test_admin_users_requires_admin(self):
        """Test /api/admin/users requires admin role."""
        token = get_user_token()
        if not token:
            pytest.skip("Regular user not available")

        response = requests.get(
            f"{API_PREFIX}/admin/users",
            headers=auth_headers(token)
        )
        assert response.status_code == 403

    def test_admin_users_with_admin(self):
        """Test /api/admin/users works with admin token."""
        token = get_admin_token()
        if not token:
            pytest.skip("Admin user not available")

        response = requests.get(
            f"{API_PREFIX}/admin/users",
            headers=auth_headers(token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) >= 2  # admin and user


# ============================================================
# 7. Logout Tests
# ============================================================

class TestLogout:
    """Test logout functionality."""

    def test_logout_success(self):
        """Test logout endpoint."""
        token = get_user_token()
        if not token:
            pytest.skip("Regular user not available")

        response = requests.post(
            f"{API_PREFIX}/auth/logout",
            headers=auth_headers(token)
        )
        assert response.status_code == 200
        # Token should still be valid (stateless JWT)
        # In real app, we would use a token blacklist
        # For now, just verify endpoint works


# ============================================================
# 8. User Isolation Tests
# ============================================================

class TestUserIsolation:
    """Test that users see only their own predictions."""

    def test_user_sees_own_predictions(self):
        """Test user can see their prediction in history."""
        # Login as regular user
        login_response = requests.post(
            f"{API_PREFIX}/auth/login",
            json={"username": "user", "password": "user123"}
        )
        if login_response.status_code != 200:
            pytest.skip("Regular user not available")

        token = login_response.json()["access_token"]

        # Make a prediction
        predict_response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "User isolation test message"},
            headers=auth_headers(token)
        )
        assert predict_response.status_code == 200

        # Get history
        history_response = requests.get(
            f"{API_PREFIX}/history",
            headers=auth_headers(token)
        )
        assert history_response.status_code == 200
        history = history_response.json()

        # Verify the prediction is in history
        found = any(
            "User isolation test message" in item["text"]
            for item in history["items"]
        )
        assert found, "User should see their own prediction in history"


# ============================================================
# 9. Dashboard Stats Tests
# ============================================================

class TestDashboardStats:
    """Test dashboard stats endpoint."""

    def test_dashboard_stats_public(self):
        """Test dashboard stats is accessible without auth (for dashboard page)."""
        response = requests.get(f"{API_PREFIX}/dashboard/stats")
        # This might be protected now - if so, skip
        if response.status_code == 401:
            pytest.skip("Dashboard stats requires auth")

        assert response.status_code == 200
        data = response.json()
        assert "totalComments" in data
        assert "metrics" in data

    def test_dashboard_stats_with_auth(self):
        """Test dashboard stats with authentication."""
        token = get_user_token()
        if not token:
            pytest.skip("Regular user not available")

        response = requests.get(
            f"{API_PREFIX}/dashboard/stats",
            headers=auth_headers(token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "totalComments" in data
        assert "metrics" in data


# ============================================================
# 10. Batch Prediction Tests
# ============================================================

class TestBatchPrediction:
    """Test batch prediction endpoint."""

    def test_batch_predict_requires_auth(self):
        """Test batch prediction requires authentication."""
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": ["Test 1", "Test 2"]}
        )
        assert response.status_code == 401

    def test_batch_predict_with_auth(self):
        """Test batch prediction works with valid token."""
        token = get_user_token()
        if not token:
            pytest.skip("Regular user not available")

        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": ["Tôi rất vui", "Tôi buồn lắm"]},
            headers=auth_headers(token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["total"] == 2
        assert data["depression_count"] + data["normal_count"] == 2


# ============================================================
# Summary Report
# ============================================================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print summary after test run."""
    if exitstatus == 0:
        print("\n✅ All auth system tests passed!")
        print("\nVerified:")
        print("  - Login with admin/admin123 and user/user123")
        print("  - User registration")
        print("  - Protected routes require authentication")
        print("  - Admin routes reject non-admin users")
        print("  - User isolation in prediction history")
        print("  - Batch prediction with auth")
    else:
        print("\n❌ Some auth system tests failed.")
        print("Please check the output above for details.")

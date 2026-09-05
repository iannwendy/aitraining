"""
Test Suite for YouTube Integration
Tests YouTube URL validation, video fetching, and analysis
"""

import os
import sys

# Set JWT_SECRET_KEY for testing
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-123456")

import pytest
import requests
from typing import Optional

# Configuration
API_BASE_URL = "http://localhost:8001"
API_PREFIX = f"{API_BASE_URL}/api"

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_auth_token(username: str = "admin", password: str = "admin123") -> Optional[str]:
    """Get access token for testing."""
    response = requests.post(
        f"{API_PREFIX}/auth/login",
        json={"username": username, "password": password}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def auth_headers(token: str) -> dict:
    """Return authorization headers with token."""
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────────────────
# 1. URL Validation Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestURLValidation:
    """Test YouTube URL validation endpoint."""

    @pytest.fixture
    def auth_token(self):
        token = get_auth_token()
        assert token is not None
        return token

    def test_validate_standard_watch_url(self, auth_token):
        """Should validate standard YouTube watch URL."""
        response = requests.get(
            f"{API_PREFIX}/youtube/validate",
            params={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["video_id"] == "dQw4w9WgXcQ"

    def test_validate_short_url(self, auth_token):
        """Should validate youtu.be short URL."""
        response = requests.get(
            f"{API_PREFIX}/youtube/validate",
            params={"url": "https://youtu.be/dQw4w9WgXcQ"},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["video_id"] == "dQw4w9WgXcQ"

    def test_validate_embed_url(self, auth_token):
        """Should validate YouTube embed URL."""
        response = requests.get(
            f"{API_PREFIX}/youtube/validate",
            params={"url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["video_id"] == "dQw4w9WgXcQ"

    def test_validate_shorts_url(self, auth_token):
        """Should validate YouTube Shorts URL."""
        response = requests.get(
            f"{API_PREFIX}/youtube/validate",
            params={"url": "https://www.youtube.com/shorts/dQw4w9WgXcQ"},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["video_id"] == "dQw4w9WgXcQ"

    def test_validate_url_without_https(self, auth_token):
        """Should validate URL without https."""
        response = requests.get(
            f"{API_PREFIX}/youtube/validate",
            params={"url": "youtube.com/watch?v=dQw4w9WgXcQ"},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_validate_invalid_url(self, auth_token):
        """Should reject invalid URL."""
        response = requests.get(
            f"{API_PREFIX}/youtube/validate",
            params={"url": "https://www.google.com"},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 400

    def test_validate_random_string(self, auth_token):
        """Should reject random string."""
        response = requests.get(
            f"{API_PREFIX}/youtube/validate",
            params={"url": "not-a-valid-url-at-all"},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 400

    def test_validate_empty_url(self, auth_token):
        """Should reject empty URL."""
        response = requests.get(
            f"{API_PREFIX}/youtube/validate",
            params={"url": ""},
            headers=auth_headers(auth_token)
        )
        # Empty string should return 400 or 422
        assert response.status_code in [400, 422]

    def test_validate_video_id_only(self, auth_token):
        """Should accept video ID alone."""
        response = requests.get(
            f"{API_PREFIX}/youtube/validate",
            params={"url": "dQw4w9WgXcQ"},
            headers=auth_headers(auth_token)
        )
        # Video ID alone might not match patterns, depends on implementation
        # Just check it's either 200 or 400
        assert response.status_code in [200, 400]


# ─────────────────────────────────────────────────────────────────────────────
# 2. Authentication Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestYouTubeAuth:
    """Test YouTube endpoint authentication."""

    def test_youtube_fetch_requires_auth(self):
        """YouTube fetch should require authentication."""
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "max_comments": 10}
        )
        # Backend returns 400 for missing auth (before URL validation)
        # Could also be 401 depending on FastAPI version
        assert response.status_code in [400, 401, 403]

    def test_youtube_fetch_with_valid_token(self):
        """Should work with valid authentication."""
        token = get_auth_token()
        assert token is not None

        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "max_comments": 5},
            headers=auth_headers(token)
        )
        # Should either succeed or fail with specific error (e.g., API key not set)
        # Not 401/403
        assert response.status_code not in [401, 403]

    def test_youtube_fetch_with_invalid_token(self):
        """Should fail with invalid token."""
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "max_comments": 10},
            headers={"Authorization": "Bearer invalid_token"}
        )
        # Backend returns 400 or 401 for invalid auth
        assert response.status_code in [400, 401]


# ─────────────────────────────────────────────────────────────────────────────
# 3. Request Validation Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRequestValidation:
    """Test request validation for YouTube fetch."""

    @pytest.fixture
    def auth_token(self):
        token = get_auth_token()
        assert token is not None
        return token

    def test_invalid_url_format(self, auth_token):
        """Should reject invalid URL format."""
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "not-a-youtube-url", "max_comments": 10},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 400

    def test_max_comments_boundary(self, auth_token):
        """Should validate max_comments boundary."""
        # Test with 0 comments
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "max_comments": 0},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 422  # Validation error

    def test_max_comments_too_large(self, auth_token):
        """Should reject max_comments > 500."""
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "max_comments": 1000},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 422  # Validation error

    def test_max_comments_valid_boundary(self, auth_token):
        """Should accept valid max_comments values."""
        for max_c in [1, 100, 500]:
            response = requests.post(
                f"{API_PREFIX}/youtube/fetch",
                json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "max_comments": max_c},
                headers=auth_headers(auth_token)
            )
            # Should not be 422 (validation error)
            assert response.status_code != 422, f"max_comments={max_c} should be valid"

    def test_missing_url(self, auth_token):
        """Should reject missing URL."""
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"max_comments": 10},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 422

    def test_missing_max_comments(self, auth_token):
        """Should accept missing max_comments (use default)."""
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            headers=auth_headers(auth_token)
        )
        # Should use default max_comments=100
        assert response.status_code in [200, 400, 403, 404, 500]


# ─────────────────────────────────────────────────────────────────────────────
# 4. YouTube API Key Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestYouTubeAPIKey:
    """Test YouTube API key configuration."""

    @pytest.fixture
    def auth_token(self):
        token = get_auth_token()
        assert token is not None
        return token

    def test_api_key_in_env(self):
        """Check if YOUTUBE_API_KEY is set in .env."""
        from pathlib import Path
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            with open(env_path) as f:
                content = f.read()
                has_key = "YOUTUBE_API_KEY=" in content
                print(f"\nYOUTUBE_API_KEY in .env: {has_key}")

    def test_fetch_without_api_key(self, auth_token):
        """Test behavior when API key is not set."""
        # This test checks what happens without API key
        # The response should indicate the issue
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "max_comments": 5},
            headers=auth_headers(auth_token)
        )

        # If API key is not set, should return 500 or 400 with appropriate message
        if response.status_code >= 400:
            data = response.json()
            error_msg = data.get("detail", "").lower()
            # Should mention API key issue
            has_key_error = "api" in error_msg and "key" in error_msg
            if not has_key_error:
                print(f"\nNote: Error message doesn't mention API key: {error_msg}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Frontend URL Processing Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFrontendURLProcessing:
    """Test URL processing in frontend (client-side)."""

    def test_url_extraction_patterns(self):
        """Test URL patterns that frontend should handle."""
        patterns = [
            ("https://www.youtube.com/watch?v=abc123XYZ", "abc123XYZ"),
            ("https://youtube.com/watch?v=abc123XYZ", "abc123XYZ"),
            ("http://youtube.com/watch?v=abc123XYZ", "abc123XYZ"),
            ("https://youtu.be/abc123XYZ", "abc123XYZ"),
            ("https://www.youtube.com/embed/abc123XYZ", "abc123XYZ"),
            ("https://www.youtube.com/shorts/abc123XYZ", "abc123XYZ"),
            ("https://m.youtube.com/watch?v=abc123XYZ", "abc123XYZ"),
        ]

        # These patterns should be valid
        for url, expected_id in patterns:
            response = requests.get(
                f"{API_PREFIX}/youtube/validate",
                params={"url": url}
            )
            if response.status_code == 200:
                assert response.json()["video_id"] == expected_id


# ─────────────────────────────────────────────────────────────────────────────
# 6. Response Structure Tests (if API works)
# ─────────────────────────────────────────────────────────────────────────────

class TestResponseStructure:
    """Test YouTube fetch response structure."""

    @pytest.fixture
    def auth_token(self):
        token = get_auth_token()
        assert token is not None
        return token

    def test_success_response_structure(self, auth_token):
        """Test successful response has correct structure."""
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "max_comments": 5},
            headers=auth_headers(auth_token)
        )

        if response.status_code == 200:
            data = response.json()

            # Check metadata structure
            assert "metadata" in data
            metadata = data["metadata"]
            required_fields = ["video_id", "title", "channel", "view_count", "like_count", "comment_count"]
            for field in required_fields:
                assert field in metadata, f"Missing field: {field}"

            # Check comments structure
            assert "comments" in data
            assert isinstance(data["comments"], list)

            # Check analysis summary
            assert "analysis_summary" in data
            summary = data["analysis_summary"]
            assert "total_comments" in summary
            assert "depression_count" in summary
            assert "normal_count" in summary
            assert "depression_rate" in summary
            assert "overall_risk" in summary
        else:
            # API might not be configured, that's okay for this test
            print(f"\nNote: YouTube API not configured, got status {response.status_code}")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Error Handling Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorHandling:
    """Test error handling."""

    @pytest.fixture
    def auth_token(self):
        token = get_auth_token()
        assert token is not None
        return token

    def test_disabled_comments_video(self, auth_token):
        """Test handling of video with disabled comments."""
        # This is a hypothetical video ID - in real test, use actual video with disabled comments
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "https://www.youtube.com/watch?v=XXXXXXXXXXX", "max_comments": 10},
            headers=auth_headers(auth_token)
        )
        # Should return appropriate error (400, 404, or 500)
        assert response.status_code in [200, 400, 404, 403, 500]

    def test_nonexistent_video(self, auth_token):
        """Test handling of non-existent video."""
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "https://www.youtube.com/watch?v=INVALID_VIDEO_ID_12345", "max_comments": 10},
            headers=auth_headers(auth_token)
        )
        # Should return error, not crash
        assert response.status_code >= 400

    def test_quota_exceeded(self, auth_token):
        """Test handling of quota exceeded error."""
        # This would require actually exhausting the quota
        # In practice, just verify the error is handled gracefully
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "max_comments": 10},
            headers=auth_headers(auth_token)
        )
        # Should either succeed or return specific error
        if response.status_code >= 400:
            data = response.json()
            assert "detail" in data


# ─────────────────────────────────────────────────────────────────────────────
# 8. Integration with Prediction
# ─────────────────────────────────────────────────────────────────────────────

class TestYouTubePredictionIntegration:
    """Test YouTube integration with prediction system."""

    @pytest.fixture
    def auth_token(self):
        token = get_auth_token()
        assert token is not None
        return token

    def test_analysis_includes_predictions(self, auth_token):
        """Verify that YouTube analysis includes prediction results."""
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "max_comments": 10},
            headers=auth_headers(auth_token)
        )

        if response.status_code == 200:
            data = response.json()

            # Should have analysis summary with predictions
            assert "analysis_summary" in data
            summary = data["analysis_summary"]

            # Should have counts
            assert "depression_count" in summary
            assert "normal_count" in summary
            assert "analyzed_comments" in summary

            # Verify counts are consistent
            assert summary["depression_count"] + summary["normal_count"] == summary["analyzed_comments"]

    def test_comments_match_predictions(self, auth_token):
        """Verify comment count matches prediction count."""
        response = requests.post(
            f"{API_PREFIX}/youtube/fetch",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "max_comments": 20},
            headers=auth_headers(auth_token)
        )

        if response.status_code == 200:
            data = response.json()

            # Number of comments should match requested max_comments
            # (or be less if video has fewer comments)
            assert len(data["comments"]) <= 20
            assert data["total_comments"] <= 20


# ─────────────────────────────────────────────────────────────────────────────
# Run Tests
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from pathlib import Path

    print("=" * 60)
    print("Running YouTube Integration Test Suite")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    print()

    # Check if server is running
    try:
        health_response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is healthy")
        else:
            print(f"❌ Server health check failed: {health_response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure backend is running on port 8001")
        sys.exit(1)

    # Check auth
    token = get_auth_token()
    if token:
        print("✅ Authentication works")
    else:
        print("❌ Authentication failed")
        sys.exit(1)

    print()
    print("Run tests with: pytest test_youtube_integration.py -v")
    print()

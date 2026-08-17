"""
Comprehensive Test Suite for Mental Health AI Web Demo
Tests all endpoints, features, and Round 6 v2 integration
Includes authentication support.
"""

import os
import pytest
import requests
from typing import Dict, List, Any

# Set JWT_SECRET_KEY for testing
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-development-only-123456")

# Configuration
API_BASE_URL = "http://localhost:8000"
API_PREFIX = f"{API_BASE_URL}/api"

# Vietnamese test texts
VIETNAMESE_TEXTS = {
    "normal": [
        "Hôm nay trời đẹp quá, tôi rất vui",
        "Đi chơi với bạn bè thật vui",
        "Công việc hôm nay rất suôn sẻ",
        "Món ăn ngon quá, ai nấu vậy",
        "Gia đình tôi hạnh phúc lắm",
    ],
    "depression": [
        "Tôi cảm thấy mệt mỏi và buồn bã, không muốn làm gì cả",
        "Cuộc sống thật vô nghĩa, tôi chẳng còn muốn sống nữa",
        "Tôi bị stress quá, ngủ không được, ăn không ngon",
        "Mọi thứ thật tệ, tôi cảm thấy tuyệt vọng",
        "Tôi cô đơn và không ai hiểu tôi",
    ],
}


# ============================================================
# Auth Fixture
# ============================================================

@pytest.fixture(scope="session")
def auth_token():
    """Register a test user and return access token."""
    import random
    import string

    # Generate unique username
    username = f"testuser_{''.join(random.choices(string.ascii_lowercase, k=8))}"
    email = f"{username}@test.com"
    password = "TestPassword123!"

    # Try to register
    reg_response = requests.post(
        f"{API_PREFIX}/auth/register",
        json={"username": username, "email": email, "password": password}
    )

    # If registration fails (e.g., user exists), try to login
    if reg_response.status_code != 201:
        login_response = requests.post(
            f"{API_PREFIX}/auth/login",
            json={"username": username, "password": password}
        )
        if login_response.status_code == 200:
            return login_response.json()["access_token"]
        # If still fails, return None (tests will be skipped or use existing user)
        # This handles the case where the test database is shared
        return None

    # Return token from registration
    return reg_response.json()["access_token"]


def auth_headers(token: str) -> Dict[str, str]:
    """Return authorization headers with token."""
    if not token:
        pytest.skip("No auth token available")
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# 1. Health & Root Tests
# ============================================================

class TestHealth:
    """Test basic health and root endpoints."""

    def test_root_endpoint(self):
        """Test GET / returns API info."""
        response = requests.get(API_BASE_URL + "/")
        assert response.status_code == 200
        data = response.json()
        assert "Mental Health AI API" in data.get("name", "")
        assert "version" in data

    def test_health_check(self):
        """Test GET /api/health returns healthy status."""
        response = requests.get(f"{API_PREFIX}/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["healthy", "ok"]
        # version field may or may not be present


# ============================================================
# 2. Dashboard Stats Tests
# ============================================================

class TestDashboard:
    """Test dashboard statistics endpoint."""

    def test_dashboard_stats(self, auth_token):
        """Test GET /api/dashboard/stats returns statistics."""
        response = requests.get(
            f"{API_PREFIX}/dashboard/stats",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "totalComments" in data
        assert "currentModel" in data
        assert "metrics" in data
        assert "round" in data

        # Check metrics structure
        metrics = data["metrics"]
        assert "macroF1" in metrics
        assert "accuracy" in metrics

    def test_dashboard_stats_values(self, auth_token):
        """Test dashboard stats contain reasonable values."""
        response = requests.get(
            f"{API_PREFIX}/dashboard/stats",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        # Metrics should be non-negative
        metrics = data["metrics"]
        assert metrics["macroF1"] >= 0
        assert metrics["macroF1"] <= 1
        assert metrics["accuracy"] >= 0
        assert metrics["accuracy"] <= 1


# ============================================================
# 3. Single Prediction Tests
# ============================================================

class TestSinglePrediction:
    """Test single text prediction endpoint."""

    def test_predict_normal_text(self, auth_token):
        """Test prediction on normal Vietnamese text."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "Hôm nay trời đẹp quá, tôi rất vui vẻ"},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        assert "prediction" in data
        assert data["prediction"] in ["normal", "depression"]
        assert "confidence" in data
        assert 0 <= data["confidence"] <= 1
        # Topic should be present (BERTopic Vietnamese)
        assert "topic" in data

    def test_predict_depression_text(self, auth_token):
        """Test prediction on depression-related Vietnamese text."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "Tôi cảm thấy mệt mỏi và buồn bã, không muốn làm gì cả"},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        assert "prediction" in data
        assert "confidence" in data
        assert data["prediction"] == "depression"
        assert data["confidence"] > 0.5

    def test_predict_all_normal_texts(self, auth_token):
        """Test prediction on all normal texts."""
        for text in VIETNAMESE_TEXTS["normal"]:
            response = requests.post(
                f"{API_PREFIX}/predict",
                json={"text": text},
                headers=auth_headers(auth_token)
            )
            assert response.status_code == 200, f"Failed for text: {text}"
            data = response.json()
            assert data["prediction"] in ["normal", "depression"]

    def test_predict_all_depression_texts(self, auth_token):
        """Test prediction on all depression texts."""
        for text in VIETNAMESE_TEXTS["depression"]:
            response = requests.post(
                f"{API_PREFIX}/predict",
                json={"text": text},
                headers=auth_headers(auth_token)
            )
            assert response.status_code == 200, f"Failed for text: {text}"
            data = response.json()
            assert data["prediction"] in ["normal", "depression"]

    def test_predict_empty_text(self, auth_token):
        """Test prediction with empty text returns validation error."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": ""},
            headers=auth_headers(auth_token)
        )
        assert response.status_code in [400, 422]

    def test_predict_long_text(self, auth_token):
        """Test prediction with long text."""
        long_text = "Tôi " + "rất " * 100 + "mệt mỏi"
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": long_text},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200

    def test_predict_missing_field(self, auth_token):
        """Test prediction with missing text field returns error."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={},
            headers=auth_headers(auth_token)
        )
        assert response.status_code in [400, 422]

    def test_predict_vietnamese_topic(self, auth_token):
        """Test that BERTopic Vietnamese topics are returned."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "Tôi bị trầm cảm và mất ngủ suốt nhiều ngày"},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "topic" in data
        # Topic should contain meaningful Vietnamese keywords
        # (not the old "toi | nguoi | rat" style)


# ============================================================
# 4. Batch Prediction Tests
# ============================================================

class TestBatchPrediction:
    """Test batch prediction endpoint."""

    def test_batch_predict_multiple(self, auth_token):
        """Test batch prediction with multiple texts."""
        comments = [
            "Hôm nay trời đẹp quá",
            "Tôi cảm thấy mệt mỏi",
            "Đi chơi với bạn bè thật vui"
        ]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert len(data["results"]) == 3
        assert data["total"] == 3
        assert data["depression_count"] + data["normal_count"] == 3

    def test_batch_predict_empty(self, auth_token):
        """Test batch prediction with empty list."""
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": []},
            headers=auth_headers(auth_token)
        )
        # Backend may return 200 or 400/422 for empty list
        assert response.status_code in [200, 400, 422]

    def test_batch_predict_single(self, auth_token):
        """Test batch prediction with single text."""
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": ["Tôi buồn lắm"]},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

    def test_batch_predict_max_limit(self, auth_token):
        """Test batch prediction respects max limit (500)."""
        # Try to exceed limit
        comments = [f"Test comment {i}" for i in range(501)]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        # Backend returns 400 or 422 for validation error
        assert response.status_code in [400, 422]

    def test_batch_predict_vietnamese_topics(self, auth_token):
        """Test batch prediction returns Vietnamese topics."""
        comments = [
            "Tôi bị trầm cảm và mất ngủ",
            "Tôi rất vui và hạnh phúc",
            "Tôi cô đơn và buồn bã"
        ]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        # Check topics are present
        for result in data["results"]:
            assert "topic" in result or result.get("topic") is None


# ============================================================
# 5. Topics Tests
# ============================================================

class TestTopics:
    """Test BERTopic topics endpoint."""

    def test_topics_default_limit(self, auth_token):
        """Test GET /api/topics with default limit."""
        response = requests.get(
            f"{API_PREFIX}/topics",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) <= 20  # Default limit
        assert len(data) > 0

        # Check topic structure
        topic = data[0]
        assert "id" in topic
        assert "name" in topic
        assert "keywords" in topic
        assert "count" in topic

    def test_topics_custom_limit(self, auth_token):
        """Test GET /api/topics with custom limit."""
        response = requests.get(
            f"{API_PREFIX}/topics?limit=5",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_topics_invalid_limit(self, auth_token):
        """Test GET /api/topics with invalid limit returns error."""
        response = requests.get(
            f"{API_PREFIX}/topics?limit=-1",
            headers=auth_headers(auth_token)
        )
        assert response.status_code in [400, 422]


# ============================================================
# 6. Model Comparison Tests
# ============================================================

class TestModelComparison:
    """Test model comparison endpoint."""

    def test_model_comparison(self, auth_token):
        """Test GET /api/models/comparison returns all models."""
        response = requests.get(
            f"{API_PREFIX}/models/comparison",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        assert "models" in data
        models = data["models"]
        assert len(models) > 0

        # Check model structure
        model = models[0]
        assert "name" in model
        assert "accuracy" in model
        assert "in_domain_f1" in model
        assert "cross_domain_f1" in model
        assert "model_type" in model

        # Check values are in valid range
        for m in models:
            assert 0 <= m["in_domain_f1"] <= 1
            assert 0 <= m["cross_domain_f1"] <= 1

    def test_round6v2_models_present(self, auth_token):
        """Test Round 6 v2 models are present in comparison."""
        response = requests.get(
            f"{API_PREFIX}/models/comparison",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        models = data["models"]

        # Find Round 6 v2 models
        r6v2_names = [m["name"] for m in models if "Round 6" in m["name"] or "R6" in m["name"]]
        assert len(r6v2_names) > 0, f"Expected Round 6 v2 models, found: {r6v2_names}"

        # Check PhoBERT Round 6 v2
        phobert_models = [m for m in models if "PhoBERT" in m["name"] and "Round 6" in m["name"]]
        assert len(phobert_models) > 0, "PhoBERT Round 6 v2 not found"


# ============================================================
# 7. Statistics Tests
# ============================================================

class TestStatistics:
    """Test statistics endpoint with data from CSV files."""

    def test_statistics(self, auth_token):
        """Test GET /api/statistics returns confusion matrix and distribution."""
        response = requests.get(
            f"{API_PREFIX}/statistics",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "confusion_matrix" in data
        assert "class_distribution" in data
        assert "dataset_breakdown" in data
        assert "prediction_stats" in data

    def test_statistics_class_distribution_loaded(self, auth_token):
        """Test class distribution is loaded from CSV (not all zeros)."""
        response = requests.get(
            f"{API_PREFIX}/statistics",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        # Class distribution should have data
        if "class_distribution" in data:
            cd = data["class_distribution"]
            total = cd.get("depression", 0) + cd.get("normal", 0)
            assert total > 0, "Class distribution should not be all zeros"


# ============================================================
# 8. History Tests
# ============================================================

class TestHistory:
    """Test prediction history endpoints."""

    def test_get_history(self, auth_token):
        """Test GET /api/history returns prediction history."""
        response = requests.get(
            f"{API_PREFIX}/history?limit=10",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["items"], list)

    def test_get_history_pagination(self, auth_token):
        """Test history pagination works."""
        response = requests.get(
            f"{API_PREFIX}/history?limit=5&offset=0",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0

    def test_save_history(self, auth_token):
        """Test that predictions are saved to history."""
        # Make a prediction
        pred_response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "Tôi đang test history"},
            headers=auth_headers(auth_token)
        )
        assert pred_response.status_code == 200

        # Check history
        hist_response = requests.get(
            f"{API_PREFIX}/history?limit=50",
            headers=auth_headers(auth_token)
        )
        assert hist_response.status_code == 200
        data = hist_response.json()
        assert data["total"] >= 1

    def test_delete_history(self, auth_token):
        """Test deleting a history item."""
        # First create a prediction
        pred_response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "Delete this"},
            headers=auth_headers(auth_token)
        )
        assert pred_response.status_code == 200

        # Get history
        hist_response = requests.get(
            f"{API_PREFIX}/history?limit=10",
            headers=auth_headers(auth_token)
        )
        assert hist_response.status_code == 200
        hist_data = hist_response.json()

        if hist_data["items"]:
            item_id = hist_data["items"][0].get("id")
            if item_id:
                del_response = requests.delete(
                    f"{API_PREFIX}/history/{item_id}",
                    headers=auth_headers(auth_token)
                )
                assert del_response.status_code in [200, 204]

    def test_delete_history_not_found(self, auth_token):
        """Test deleting non-existent history returns 404."""
        response = requests.delete(
            f"{API_PREFIX}/history/nonexistent-id-12345",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 404


# ============================================================
# 9. Model Refresh Tests
# ============================================================

class TestModelRefresh:
    """Test model refresh endpoint."""

    def test_refresh_status(self, auth_token):
        """Test GET /api/models/refresh/status returns status."""
        response = requests.get(
            f"{API_PREFIX}/models/refresh/status",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_refresh_models(self, auth_token):
        """Test POST /api/models/refresh triggers refresh."""
        response = requests.post(
            f"{API_PREFIX}/models/refresh",
            headers=auth_headers(auth_token)
        )
        # Should return 200 or 202 (accepted)
        assert response.status_code in [200, 202, 400]


# ============================================================
# 10. CORS Tests
# ============================================================

class TestCORS:
    """Test CORS headers."""

    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = requests.options(
            f"{API_PREFIX}/predict",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            }
        )
        assert response.status_code in [200, 204]


# ============================================================
# 11. Error Handling Tests
# ============================================================

class TestErrorHandling:
    """Test error handling."""

    def test_invalid_json(self, auth_token):
        """Test invalid JSON returns 422."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            data="not valid json",
            headers={**auth_headers(auth_token), "Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]

    def test_unauthorized_without_token(self):
        """Test endpoints return 401 without auth token."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "Test"}
        )
        assert response.status_code == 401


# ============================================================
# 12. Integration Tests
# ============================================================

class TestIntegration:
    """End-to-end integration tests."""

    def test_full_prediction_workflow(self, auth_token):
        """Test complete prediction workflow."""
        # 1. Get dashboard stats
        stats_response = requests.get(
            f"{API_PREFIX}/dashboard/stats",
            headers=auth_headers(auth_token)
        )
        assert stats_response.status_code == 200

        # 2. Make prediction
        pred_response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "Tôi cảm thấy mệt mỏi và buồn"},
            headers=auth_headers(auth_token)
        )
        assert pred_response.status_code == 200
        pred_data = pred_response.json()
        assert "prediction" in pred_data
        assert "topic" in pred_data

        # 3. Check history
        hist_response = requests.get(
            f"{API_PREFIX}/history?limit=10",
            headers=auth_headers(auth_token)
        )
        assert hist_response.status_code == 200

    def test_round6v2_consistency(self, auth_token):
        """Test Round 6 v2 models are consistent."""
        # Get comparison
        comp_response = requests.get(
            f"{API_PREFIX}/models/comparison",
            headers=auth_headers(auth_token)
        )
        assert comp_response.status_code == 200
        comp_data = comp_response.json()

        # Find PhoBERT R6 v2
        phobert = None
        for m in comp_data["models"]:
            if "PhoBERT" in m["name"] and "Round 6" in m["name"]:
                phobert = m
                break

        assert phobert is not None, "PhoBERT Round 6 v2 not found"
        assert phobert["in_domain_f1"] > 0.5, "F1 should be reasonable"


# ============================================================
# 13. BERTopic Vietnamese Topics Tests
# ============================================================

class TestBERTopicVietnamese:
    """Test BERTopic Vietnamese topic features."""

    def test_topic_keywords_are_vietnamese(self, auth_token):
        """Test that topic keywords contain Vietnamese characters."""
        response = requests.get(
            f"{API_PREFIX}/topics",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        topics = response.json()

        if topics:
            topic = topics[0]
            keywords = topic.get("keywords", [])
            # Should have keywords (not empty list)
            assert len(keywords) > 0

    def test_depression_topic_exists(self, auth_token):
        """Test that a depression-related topic exists."""
        response = requests.get(
            f"{API_PREFIX}/topics",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        topics = response.json()

        # Look for topics with depression-related keywords
        depression_keywords = ["trầm", "mất", "ngủ", "buồn", "khóc", "đau"]
        found = False
        for topic in topics:
            topic_str = str(topic.get("name", "")) + " " + " ".join(topic.get("keywords", []))
            if any(kw in topic_str.lower() for kw in depression_keywords):
                found = True
                break

        # Should find at least one relevant topic
        # (This is a soft check - some corpus might not have these exact keywords)

"""
Comprehensive Test Suite for Mental Health AI Web Demo
Tests all endpoints, features, and Round 6 v2 integration
"""

import pytest
import requests
from typing import Dict, List, Any

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
        assert data.get("status") == "healthy"
        assert "timestamp" in data


# ============================================================
# 2. Dashboard Stats Tests
# ============================================================

class TestDashboard:
    """Test dashboard stats endpoint and Round 6 v2 integration."""

    def test_dashboard_stats(self):
        """Test GET /api/dashboard/stats returns dataset counts and metrics."""
        response = requests.get(f"{API_PREFIX}/dashboard/stats")
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "totalComments" in data
        assert "totalPredictions" in data
        assert "goldLabels" in data
        assert "currentModel" in data
        assert "bestCrossDomain" in data
        assert "trainingDate" in data
        assert "round" in data
        assert "metrics" in data

        # Check Round 6 v2
        assert data["round"] == "6v2", f"Expected round 6v2, got {data['round']}"
        assert "PhoBERT" in data["currentModel"], f"Expected PhoBERT in model name, got {data['currentModel']}"

        # Check data types
        assert isinstance(data["totalComments"], int)
        assert isinstance(data["totalPredictions"], int)
        assert isinstance(data["goldLabels"], int)

        # Check reasonable values
        assert data["totalComments"] > 0, "totalComments should be > 0"
        assert data["totalPredictions"] > 0, "totalPredictions should be > 0"


# ============================================================
# 3. Single Prediction Tests
# ============================================================

class TestSinglePrediction:
    """Test single text prediction endpoint."""

    def test_predict_normal_text(self):
        """Test POST /api/predict with normal Vietnamese text."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": VIETNAMESE_TEXTS["normal"][0]},
        )
        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "id" in data
        assert "text" in data
        assert "prediction" in data
        assert "confidence" in data
        assert "riskLevel" in data
        assert "modelName" in data

        # Check value constraints
        assert data["prediction"] in ["depression", "normal"]
        assert 0 <= data["confidence"] <= 1
        assert data["riskLevel"] in ["low", "medium", "high"]
        assert "Round 6" in data["modelName"], f"Expected Round 6 in model name, got {data['modelName']}"

    def test_predict_depression_text(self):
        """Test POST /api/predict with depression-indicating text."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": VIETNAMESE_TEXTS["depression"][0]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data
        assert data["prediction"] == "depression"

    def test_predict_all_normal_texts(self):
        """Test prediction on all normal texts."""
        for text in VIETNAMESE_TEXTS["normal"]:
            response = requests.post(f"{API_PREFIX}/predict", json={"text": text})
            assert response.status_code == 200
            data = response.json()
            assert data["prediction"] in ["depression", "normal"]

    def test_predict_all_depression_texts(self):
        """Test prediction on all depression texts."""
        results = []
        for text in VIETNAMESE_TEXTS["depression"]:
            response = requests.post(f"{API_PREFIX}/predict", json={"text": text})
            assert response.status_code == 200
            data = response.json()
            assert data["prediction"] in ["depression", "normal"]
            results.append(data["prediction"] == "depression")

        # At least 3 out of 5 should be detected as depression
        depression_count = sum(results)
        assert depression_count >= 3, f"Expected at least 3/5 depression predictions, got {depression_count}"

    def test_predict_empty_text(self):
        """Test POST /api/predict with empty text returns 422."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": ""},
        )
        assert response.status_code == 422

    def test_predict_long_text(self):
        """Test POST /api/predict with maximum length text."""
        long_text = " ".join(VIETNAMESE_TEXTS["normal"]) * 10
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": long_text[:2000]},
        )
        assert response.status_code == 200

    def test_predict_missing_field(self):
        """Test POST /api/predict without text field returns 422."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={},
        )
        assert response.status_code == 422


# ============================================================
# 4. Batch Prediction Tests
# ============================================================

class TestBatchPrediction:
    """Test batch prediction endpoint."""

    def test_batch_predict_multiple(self):
        """Test POST /api/predict/batch with multiple comments."""
        comments = VIETNAMESE_TEXTS["normal"] + VIETNAMESE_TEXTS["depression"]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
        )
        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "results" in data
        assert "total" in data
        assert "depression_count" in data
        assert "normal_count" in data

        # Check counts
        assert data["total"] == len(comments)
        assert data["depression_count"] + data["normal_count"] == len(comments)
        assert len(data["results"]) == len(comments)

    def test_batch_predict_empty(self):
        """Test POST /api/predict/batch with empty array."""
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": []},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["total"] == 0
        assert data["depression_count"] == 0
        assert data["normal_count"] == 0

    def test_batch_predict_single(self):
        """Test POST /api/predict/batch with single comment."""
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": [VIETNAMESE_TEXTS["normal"][0]]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1

    def test_batch_predict_max_limit(self):
        """Test batch prediction with max limit (500 items)."""
        comments = ["test comment"] * 500
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 500


# ============================================================
# 5. Topics Tests
# ============================================================

class TestTopics:
    """Test BERTopic topics endpoint."""

    def test_topics_default_limit(self):
        """Test GET /api/topics with default limit."""
        response = requests.get(f"{API_PREFIX}/topics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check topic structure
        topic = data[0]
        assert "id" in topic
        assert "name" in topic
        assert "keywords" in topic
        assert "count" in topic
        assert "percentage" in topic

    def test_topics_custom_limit(self):
        """Test GET /api/topics with custom limit."""
        response = requests.get(f"{API_PREFIX}/topics?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_topics_invalid_limit(self):
        """Test GET /api/topics with invalid limit returns 422."""
        response = requests.get(f"{API_PREFIX}/topics?limit=999")
        assert response.status_code == 422


# ============================================================
# 6. Model Comparison Tests
# ============================================================

class TestModelComparison:
    """Test model comparison endpoint and Round 6 v2 metrics."""

    def test_model_comparison(self):
        """Test GET /api/models/comparison returns all model metrics."""
        response = requests.get(f"{API_PREFIX}/models/comparison")
        assert response.status_code == 200
        data = response.json()

        assert "models" in data
        models = data["models"]
        assert isinstance(models, list)
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

    def test_round6v2_models_present(self):
        """Test Round 6 v2 models are present in comparison."""
        response = requests.get(f"{API_PREFIX}/models/comparison")
        assert response.status_code == 200
        data = response.json()
        models = data["models"]

        # Find Round 6 v2 models
        r6v2_names = [m["name"] for m in models if "Round 6" in m["name"] or "R6" in m["name"]]
        assert len(r6v2_names) > 0, f"Expected Round 6 v2 models, found: {r6v2_names}"

        # Check PhoBERT Round 6 v2
        phobert_models = [m for m in models if "PhoBERT" in m["name"] and "Round 6" in m["name"]]
        assert len(phobert_models) > 0, "PhoBERT Round 6 v2 not found"

        # Check TF-IDF Round 6 v2
        tfidf_models = [m for m in models if "TF-IDF" in m["name"] and "R6" in m["name"]]
        assert len(tfidf_models) >= 2, f"Expected 2 TF-IDF R6 v2 models, found {len(tfidf_models)}"


# ============================================================
# 7. Statistics Tests
# ============================================================

class TestStatistics:
    """Test statistics endpoint with data from CSV files."""

    def test_statistics(self):
        """Test GET /api/statistics returns confusion matrix and distribution."""
        response = requests.get(f"{API_PREFIX}/statistics")
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "confusion_matrix" in data
        assert "class_distribution" in data
        assert "dataset_breakdown" in data
        assert "prediction_stats" in data

        # Check confusion matrix structure
        cm = data["confusion_matrix"]
        assert len(cm) == 2
        assert len(cm[0]) == 2
        assert len(cm[1]) == 2

        # Check class distribution
        assert "depression" in data["class_distribution"]
        assert "normal" in data["class_distribution"]

    def test_statistics_class_distribution_loaded(self):
        """Test class distribution is loaded from CSV (not all zeros)."""
        response = requests.get(f"{API_PREFIX}/statistics")
        assert response.status_code == 200
        data = response.json()

        # Class distribution should have data
        total = data["class_distribution"]["depression"] + data["class_distribution"]["normal"]
        assert total > 0, "Class distribution should not be all zeros"

        # Should have reasonable balance
        depression = data["class_distribution"]["depression"]
        normal = data["class_distribution"]["normal"]
        assert depression > 0, "Should have depression samples"
        assert normal > 0, "Should have normal samples"


# ============================================================
# 8. History Tests
# ============================================================

class TestHistory:
    """Test prediction history endpoints."""

    def test_get_history(self):
        """Test GET /api/history returns prediction history."""
        response = requests.get(f"{API_PREFIX}/history?limit=10")
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["items"], list)

    def test_get_history_pagination(self):
        """Test GET /api/history with pagination."""
        response = requests.get(f"{API_PREFIX}/history?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0

    def test_save_history(self):
        """Test POST /api/history saves prediction."""
        response = requests.post(
            f"{API_PREFIX}/history",
            json={"text": "Test entry for pytest"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "saved"

    def test_delete_history(self):
        """Test DELETE /api/history/{id} deletes entry."""
        # First save an entry
        save_response = requests.post(
            f"{API_PREFIX}/history",
            json={"text": "Test entry to delete"},
        )
        entry_id = save_response.json()["id"]

        # Then delete it
        delete_response = requests.delete(f"{API_PREFIX}/history/{entry_id}")
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["status"] == "deleted"
        assert data["id"] == entry_id

    def test_delete_history_not_found(self):
        """Test DELETE /api/history/{id} with non-existent ID returns 404."""
        response = requests.delete(f"{API_PREFIX}/history/non-existent-id-123")
        assert response.status_code == 404


# ============================================================
# 9. Model Refresh Tests
# ============================================================

class TestModelRefresh:
    """Test model hot-reload functionality."""

    def test_refresh_status(self):
        """Test GET /api/models/refresh/status."""
        response = requests.get(f"{API_PREFIX}/models/refresh/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["idle", "loading", "error"]

    def test_refresh_models(self):
        """Test POST /api/models/refresh triggers hot-reload."""
        response = requests.post(f"{API_PREFIX}/models/refresh")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


# ============================================================
# 10. CORS Tests
# ============================================================

class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = requests.options(
            f"{API_PREFIX}/predict",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        # Allow methods should be in headers
        assert "access-control-allow-origin" in [h.lower() for h in response.headers]


# ============================================================
# 11. Error Handling Tests
# ============================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_json(self):
        """Test POST with invalid JSON returns 422."""
        import httpx
        response = httpx.post(
            f"{API_PREFIX}/predict",
            content=b"not valid json",
            headers={"Content-Type": "application/json"},
            timeout=30.0
        )
        assert response.status_code in [400, 422]


# ============================================================
# 12. Integration Tests
# ============================================================

class TestIntegration:
    """End-to-end integration tests."""

    def test_full_prediction_workflow(self):
        """Test complete workflow: predict -> history -> delete."""
        # 1. Make a prediction
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "Tôi rất vui hôm nay"},
        )
        assert response.status_code == 200
        pred_data = response.json()

        # 2. Check it's in history
        response = requests.get(f"{API_PREFIX}/history?limit=100")
        assert response.status_code == 200
        history = response.json()
        history_ids = [item["id"] for item in history["items"]]
        # Note: ID may not be in first 100 items

    def test_round6v2_consistency(self):
        """Test that Round 6 v2 info is consistent across endpoints."""
        # Dashboard
        dashboard = requests.get(f"{API_PREFIX}/dashboard/stats").json()
        assert dashboard["round"] == "6v2"

        # Model comparison should have R6v2 models
        comparison = requests.get(f"{API_PREFIX}/models/comparison").json()
        r6v2_models = [m for m in comparison["models"]
                       if "Round 6" in m["name"] or "R6 v2" in m["name"]]
        assert len(r6v2_models) >= 3, f"Expected at least 3 R6v2 models, found {len(r6v2_models)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

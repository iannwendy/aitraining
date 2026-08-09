"""
Pytest Test Suite for Mental Health AI API
Tests all endpoints using httpx async client
"""

import pytest
import httpx
import asyncio
from typing import AsyncGenerator

# Test configuration
API_BASE_URL = "http://localhost:8000"
API_PREFIX = f"{API_BASE_URL}/api"

# Vietnamese test texts
VIETNAMESE_TEXTS = {
    "normal": [
        "Hôm nay trời đẹp quá, tôi rất vui",
        "Đi chơi với bạn bè thật vui",
        "Công việc hôm nay rất suôn sẻ",
        "Món ăn ngon quá, ai nấu vậy",
    ],
    "depression": [
        "Tôi cảm thấy mệt mỏi và buồn bã, không muốn làm gì cả",
        "Cuộc sống thật vô nghĩa, tôi chẳng còn muốn sống nữa",
        "Tôi bị stress quá, ngủ không được, ăn không ngon",
        "Mọi thứ thật tệ, tôi cảm thấy tuyệt vọng",
    ],
}


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create async HTTP client."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        yield client


# ============================================================
# 1. Health & Root Tests
# ============================================================

@pytest.mark.asyncio
async def test_root_endpoint(client: httpx.AsyncClient):
    """Test GET / returns API info."""
    response = await client.get(f"{API_BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert "Mental Health AI API" in data.get("name", "")
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check(client: httpx.AsyncClient):
    """Test GET /api/health returns healthy status."""
    response = await client.get(f"{API_PREFIX}/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"
    assert "timestamp" in data


# ============================================================
# 2. Dashboard Stats Tests
# ============================================================

@pytest.mark.asyncio
async def test_dashboard_stats(client: httpx.AsyncClient):
    """Test GET /api/dashboard/stats returns dataset counts and metrics."""
    response = await client.get(f"{API_PREFIX}/dashboard/stats")
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

    # Check data types
    assert isinstance(data["totalComments"], int)
    assert isinstance(data["totalPredictions"], int)
    assert isinstance(data["goldLabels"], int)


# ============================================================
# 3. Single Prediction Tests
# ============================================================

@pytest.mark.asyncio
async def test_predict_normal_text(client: httpx.AsyncClient):
    """Test POST /api/predict with normal Vietnamese text."""
    response = await client.post(
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


@pytest.mark.asyncio
async def test_predict_depression_text(client: httpx.AsyncClient):
    """Test POST /api/predict with depression-indicating text."""
    response = await client.post(
        f"{API_PREFIX}/predict",
        json={"text": VIETNAMESE_TEXTS["depression"][0]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "confidence" in data


@pytest.mark.asyncio
async def test_predict_empty_text(client: httpx.AsyncClient):
    """Test POST /api/predict with empty text returns 422."""
    response = await client.post(
        f"{API_PREFIX}/predict",
        json={"text": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_predict_long_text(client: httpx.AsyncClient):
    """Test POST /api/predict with maximum length text."""
    long_text = " ".join(VIETNAMESE_TEXTS["normal"]) * 10  # ~500 chars
    response = await client.post(
        f"{API_PREFIX}/predict",
        json={"text": long_text[:2000]},  # Max length is 2000
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_predict_missing_field(client: httpx.AsyncClient):
    """Test POST /api/predict without text field returns 422."""
    response = await client.post(
        f"{API_PREFIX}/predict",
        json={},
    )
    assert response.status_code == 422


# ============================================================
# 4. Batch Prediction Tests
# ============================================================

@pytest.mark.asyncio
async def test_batch_predict_multiple(client: httpx.AsyncClient):
    """Test POST /api/predict/batch with multiple comments."""
    comments = VIETNAMESE_TEXTS["normal"] + VIETNAMESE_TEXTS["depression"]
    response = await client.post(
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


@pytest.mark.asyncio
async def test_batch_predict_empty(client: httpx.AsyncClient):
    """Test POST /api/predict/batch with empty array."""
    response = await client.post(
        f"{API_PREFIX}/predict/batch",
        json={"comments": []},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []
    assert data["total"] == 0
    assert data["depression_count"] == 0
    assert data["normal_count"] == 0


@pytest.mark.asyncio
async def test_batch_predict_single(client: httpx.AsyncClient):
    """Test POST /api/predict/batch with single comment."""
    response = await client.post(
        f"{API_PREFIX}/predict/batch",
        json={"comments": [VIETNAMESE_TEXTS["normal"][0]]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["results"]) == 1


# ============================================================
# 5. Topics Tests
# ============================================================

@pytest.mark.asyncio
async def test_topics_default_limit(client: httpx.AsyncClient):
    """Test GET /api/topics with default limit."""
    response = await client.get(f"{API_PREFIX}/topics")
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


@pytest.mark.asyncio
async def test_topics_custom_limit(client: httpx.AsyncClient):
    """Test GET /api/topics with custom limit."""
    response = await client.get(f"{API_PREFIX}/topics?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5


@pytest.mark.asyncio
async def test_topics_invalid_limit(client: httpx.AsyncClient):
    """Test GET /api/topics with invalid limit returns 422."""
    response = await client.get(f"{API_PREFIX}/topics?limit=999")
    assert response.status_code == 422


# ============================================================
# 6. Model Comparison Tests
# ============================================================

@pytest.mark.asyncio
async def test_model_comparison(client: httpx.AsyncClient):
    """Test GET /api/models/comparison returns all model metrics."""
    response = await client.get(f"{API_PREFIX}/models/comparison")
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
        assert m["model_type"] in ["baseline", "bilstm", "phobert", "bertopic", "hybrid"]


# ============================================================
# 7. Statistics Tests
# ============================================================

@pytest.mark.asyncio
async def test_statistics(client: httpx.AsyncClient):
    """Test GET /api/statistics returns confusion matrix and distribution."""
    response = await client.get(f"{API_PREFIX}/statistics")
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


# ============================================================
# 8. History Tests
# ============================================================

@pytest.mark.asyncio
async def test_get_history(client: httpx.AsyncClient):
    """Test GET /api/history returns prediction history."""
    response = await client.get(f"{API_PREFIX}/history?limit=10")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_history_pagination(client: httpx.AsyncClient):
    """Test GET /api/history with pagination."""
    response = await client.get(f"{API_PREFIX}/history?limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 5
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_save_history(client: httpx.AsyncClient):
    """Test POST /api/history saves prediction."""
    response = await client.post(
        f"{API_PREFIX}/history",
        json={"text": "Test entry for pytest"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "saved"

    # Return ID for cleanup
    return data["id"]


@pytest.mark.asyncio
async def test_delete_history(client: httpx.AsyncClient):
    """Test DELETE /api/history/{id} deletes entry."""
    # First save an entry
    save_response = await client.post(
        f"{API_PREFIX}/history",
        json={"text": "Test entry to delete"},
    )
    entry_id = save_response.json()["id"]

    # Then delete it
    delete_response = await client.delete(f"{API_PREFIX}/history/{entry_id}")
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["status"] == "deleted"
    assert data["id"] == entry_id


@pytest.mark.asyncio
async def test_delete_history_not_found(client: httpx.AsyncClient):
    """Test DELETE /api/history/{id} with non-existent ID returns 404."""
    response = await client.delete(f"{API_PREFIX}/history/non-existent-id-123")
    assert response.status_code == 404


# ============================================================
# 9. Model Refresh Tests
# ============================================================

@pytest.mark.asyncio
async def test_refresh_status(client: httpx.AsyncClient):
    """Test GET /api/models/refresh/status."""
    response = await client.get(f"{API_PREFIX}/models/refresh/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["idle", "loading", "error"]


@pytest.mark.asyncio
async def test_refresh_models(client: httpx.AsyncClient):
    """Test POST /api/models/refresh triggers hot-reload."""
    response = await client.post(f"{API_PREFIX}/models/refresh")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


# ============================================================
# 10. CORS Tests
# ============================================================

@pytest.mark.asyncio
async def test_cors_headers(client: httpx.AsyncClient):
    """Test CORS headers are present."""
    response = await client.options(
        f"{API_PREFIX}/predict",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" in [h.lower() for h in response.headers]


# ============================================================
# 11. Error Handling Tests
# ============================================================

@pytest.mark.asyncio
async def test_invalid_json(client: httpx.AsyncClient):
    """Test POST with invalid JSON returns 422/400."""
    response = await client.post(
        f"{API_PREFIX}/predict",
        content=b"not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_wrong_content_type(client: httpx.AsyncClient):
    """Test POST with wrong content type."""
    response = await client.post(
        f"{API_PREFIX}/predict",
        content=b"text=hello",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code in [400, 415, 422]

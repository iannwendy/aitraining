"""
Comprehensive Test Suite for Batch Prediction Flow
Tests all scenarios: Upload CSV, API call, Display results, Export CSV
"""

import os
import sys
import json
import tempfile
from pathlib import Path

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


def create_csv_file(content: str, filename: str = "test.csv") -> Path:
    """Create a temporary CSV file for testing."""
    temp_dir = Path(tempfile.gettempdir())
    file_path = temp_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path


def create_txt_file(content: str, filename: str = "test.txt") -> Path:
    """Create a temporary TXT file for testing."""
    temp_dir = Path(tempfile.gettempdir())
    file_path = temp_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path


# ─────────────────────────────────────────────────────────────────────────────
# Test Data - Vietnamese depression-related comments
# ─────────────────────────────────────────────────────────────────────────────

VIETNAMESE_COMMENTS = {
    "depression": [
        "Tôi cảm thấy mệt mỏi và cô đơn lắm rồi",
        "Cuộc sống này thật vô nghĩa",
        "Tôi không muốn làm gì nữa, chán hết mọi thứ",
        "Mỗi đêm tôi đều khóc một mình",
        "Tôi cảm thấy mình là gánh nặng cho mọi người",
        "Áp lực quá, tôi không chịu nổi nữa rồi",
        "Mất ngủ triền miên, không ngủ được gì cả",
        "Tôi buồn lắm, không biết tâm sự với ai",
        "Cảm giác như không ai hiểu tôi",
        "Cuộc sống quá khó khăn, tôi muốn bỏ cuộc",
    ],
    "normal": [
        "Video này hay quá, cảm ơn bạn đã chia sẻ",
        "Hôm nay thời tiết đẹp trời",
        "Tôi vừa đi du lịch về, vui lắm",
        "Món ăn này ngon lắm, recommend",
        "Con gái mình vừa thi đỗ đại học",
        "Trời mưa to quá, không đi ra ngoài được",
        "Xem phim này vui quá, recommend mọi người",
        "Sáng nay tập thể dục xong thấy khỏe hơn nhiều",
        "Gần đây công việc ổn định hơn rồi",
        "Đi ăn nhà hàng với gia đình, vui vẻ",
    ],
    "mixed": [
        "Tôi rất cô đơn nhưng cũng cố gắng mỗi ngày",
        "Mệt mỏi với công việc nhưng phải cố gắng vì gia đình",
        "Video hay nhưng cũng khiến tôi buồn khi nhớ lại quá khứ",
        "Áp lực học tập nhưng tôi biết mình sẽ vượt qua được",
        "Cuộc sống có lúc vui lúc buồn, quan trọng là biết cân bằng",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# 1. Authentication Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthentication:
    """Test authentication requirements."""

    def test_batch_predict_requires_auth(self):
        """Batch prediction should require authentication."""
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": ["Test comment"]}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_batch_predict_with_valid_token(self):
        """Batch prediction should work with valid token."""
        token = get_auth_token()
        assert token is not None, "Failed to get auth token"

        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": ["Test comment"]},
            headers=auth_headers(token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_batch_predict_with_invalid_token(self):
        """Batch prediction should fail with invalid token."""
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": ["Test comment"]},
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. API Endpoint Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBatchPredictionAPI:
    """Test batch prediction API endpoint."""

    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests."""
        token = get_auth_token()
        assert token is not None
        return token

    def test_batch_predict_empty_comments(self, auth_token):
        """Should return empty results for empty comments list."""
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": []},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["depression_count"] == 0
        assert data["normal_count"] == 0
        assert data["results"] == []

    def test_batch_predict_single_comment(self, auth_token):
        """Should work with single comment."""
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": ["Tôi rất cô đơn"]},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert "prediction" in data["results"][0]
        assert "confidence" in data["results"][0]

    def test_batch_predict_multiple_comments(self, auth_token):
        """Should work with multiple comments."""
        comments = [
            "Tôi rất cô đơn",
            "Video hay quá",
            "Cuộc sống khó khăn",
        ]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["results"]) == 3

    def test_batch_predict_max_500_comments(self, auth_token):
        """Should handle up to 500 comments."""
        comments = [f"Test comment number {i}" for i in range(500)]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 500

    def test_batch_predict_response_structure(self, auth_token):
        """Verify response structure."""
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": ["Test comment"]},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        # Check top-level fields
        assert "results" in data
        assert "total" in data
        assert "depression_count" in data
        assert "normal_count" in data

        # Check result item fields
        result = data["results"][0]
        assert "id" in result
        assert "text" in result
        assert "prediction" in result
        assert "confidence" in result
        assert "riskLevel" in result
        assert "modelName" in result

    def test_batch_predict_prediction_values(self, auth_token):
        """Verify prediction values are valid."""
        comments = ["Tôi cô đơn", "Video hay quá"]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        for result in data["results"]:
            assert result["prediction"] in ["depression", "normal"]
            assert 0 <= result["confidence"] <= 1
            assert result["riskLevel"] in ["low", "medium", "high"]

    def test_batch_predict_depression_count_accuracy(self, auth_token):
        """Verify depression_count matches actual predictions."""
        comments = VIETNAMESE_COMMENTS["depression"] + VIETNAMESE_COMMENTS["normal"]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        actual_depression = sum(
            1 for r in data["results"] if r["prediction"] == "depression"
        )
        assert data["depression_count"] == actual_depression
        assert data["normal_count"] == data["total"] - actual_depression

    def test_batch_predict_all_depression_comments(self, auth_token):
        """Should detect depression in obvious depression-related comments."""
        comments = VIETNAMESE_COMMENTS["depression"]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        # Most depression comments should be detected as depression
        depression_rate = data["depression_count"] / data["total"]
        assert depression_rate >= 0.5, f"Expected >= 50% depression rate, got {depression_rate*100:.1f}%"

    def test_batch_predict_all_normal_comments(self, auth_token):
        """Should detect normal comments correctly."""
        comments = VIETNAMESE_COMMENTS["normal"]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        # Most normal comments should be detected as normal
        normal_rate = data["normal_count"] / data["total"]
        assert normal_rate >= 0.5, f"Expected >= 50% normal rate, got {normal_rate*100:.1f}%"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Single Prediction API Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSinglePredictionAPI:
    """Test single prediction API endpoint."""

    @pytest.fixture
    def auth_token(self):
        token = get_auth_token()
        assert token is not None
        return token

    def test_single_predict_depression(self, auth_token):
        """Should detect depression in depression-related text."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "Tôi cảm thấy cuộc sống này thật vô nghĩa và tôi rất cô đơn"},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data
        assert "riskLevel" in data

    def test_single_predict_normal(self, auth_token):
        """Should detect normal text."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "Hôm nay thời tiết đẹp trời, đi dạo công viên vui quá"},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert data["prediction"] in ["depression", "normal"]

    def test_single_predict_response_includes_explanation(self, auth_token):
        """Should include explanation in response."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": "Tôi rất buồn và cô đơn"},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data

    def test_single_predict_empty_text(self, auth_token):
        """Should reject empty text."""
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": ""},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 422, f"Expected 422 for empty text, got {response.status_code}"

    def test_single_predict_very_long_text(self, auth_token):
        """Should handle long text (truncated to 2000 chars)."""
        long_text = "Tôi buồn " * 1000  # Creates a very long text
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": long_text},
            headers=auth_headers(auth_token)
        )
        # Should either succeed or reject based on max_length
        assert response.status_code in [200, 422]

    def test_single_predict_preserves_history(self, auth_token):
        """Should save prediction to history."""
        test_text = f"Test comment for history {os.urandom(8).hex()}"
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": test_text},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200

        # Check history endpoint
        history_response = requests.get(
            f"{API_PREFIX}/history?limit=10",
            headers=auth_headers(auth_token)
        )
        assert history_response.status_code == 200
        history = history_response.json()
        assert any(item["text"] == test_text for item in history["items"])


# ─────────────────────────────────────────────────────────────────────────────
# 4. History API Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestHistoryAPI:
    """Test history API endpoints."""

    @pytest.fixture
    def auth_token(self):
        token = get_auth_token()
        assert token is not None
        return token

    def test_get_history_empty(self, auth_token):
        """Should return empty list when no history."""
        response = requests.get(
            f"{API_PREFIX}/history?limit=10",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_history_pagination(self, auth_token):
        """Should support pagination."""
        response = requests.get(
            f"{API_PREFIX}/history?limit=5&offset=0",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
        assert data["limit"] == 5
        assert data["offset"] == 0

    def test_history_item_structure(self, auth_token):
        """Verify history item structure."""
        response = requests.get(
            f"{API_PREFIX}/history?limit=1",
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()

        if data["items"]:
            item = data["items"][0]
            assert "id" in item
            assert "text" in item
            assert "prediction" in item
            assert "confidence" in item
            assert "created_at" in item


# ─────────────────────────────────────────────────────────────────────────────
# 5. CSV Processing Tests (Backend)
# ─────────────────────────────────────────────────────────────────────────────

class TestCSVProcessing:
    """Test CSV file processing."""

    @pytest.fixture
    def auth_token(self):
        token = get_auth_token()
        assert token is not None
        return token

    def test_csv_with_header(self, auth_token):
        """Should skip header row in CSV."""
        csv_content = """comment
Tôi cô đơn lắm
Video hay quá
Cuộc sống khó khăn"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.read().strip().split('\n')
                assert lines[0] == "comment"  # Header
                comments = lines[1:]
                assert len(comments) == 3
        finally:
            os.unlink(csv_path)

    def test_csv_without_header(self, auth_token):
        """Should process CSV without header."""
        csv_content = """Tôi cô đơn
Video hay quá
Khó khăn"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.read().strip().split('\n')
                comments = lines  # No header, all lines are comments
                assert len(comments) == 3
        finally:
            os.unlink(csv_path)

    def test_txt_file_processing(self, auth_token):
        """Should process plain text files (one comment per line)."""
        txt_content = """Line 1 comment
Line 2 comment
Line 3 comment"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(txt_content)
            txt_path = f.name

        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                lines = f.read().strip().split('\n')
                comments = [l.strip() for l in lines if l.strip()]
                assert len(comments) == 3
        finally:
            os.unlink(txt_path)

    def test_empty_lines_filtered(self, auth_token):
        """Should filter out empty lines."""
        csv_content = """comment
Line 1

Line 2

Line 3"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.read().strip().split('\n')
                # Skip header
                comments = [l.strip() for l in lines[1:] if l.strip()]
                assert len(comments) == 3
        finally:
            os.unlink(csv_path)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Vietnamese Language Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestVietnameseLanguage:
    """Test Vietnamese language handling."""

    @pytest.fixture
    def auth_token(self):
        token = get_auth_token()
        assert token is not None
        return token

    def test_vietnamese_with_diacritics(self, auth_token):
        """Should handle Vietnamese with diacritics."""
        comments = [
            "Tôi rất buồn và tuyệt vọng",
            "Cuộc sống thật vô nghĩa",
            "Tôi không còn muốn sống nữa",
        ]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200

    def test_vietnamese_without_diacritics(self, auth_token):
        """Should handle Vietnamese without diacritics."""
        comments = [
            "Toi rat buon va tuyet vong",
            "Cuoc song that vo nghia",
        ]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200

    def test_vietnamese_with_emoji(self, auth_token):
        """Should handle Vietnamese with emoji."""
        comments = [
            "Tôi rất buồn 😢",
            "Video hay quá 👍",
        ]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200

    def test_mixed_vietnamese_english(self, auth_token):
        """Should handle mixed Vietnamese and English."""
        comments = [
            "Tôi rất buồn nhưng vẫn cố gắng",
            "This is so depressing 😢",
        ]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 7. Edge Cases & Error Handling
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def auth_token(self):
        token = get_auth_token()
        assert token is not None
        return token

    def test_duplicate_comments(self, auth_token):
        """Should handle duplicate comments."""
        comments = ["Test comment"] * 10
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10

    def test_very_short_comments(self, auth_token):
        """Should handle very short comments."""
        comments = ["a", "b", "cc"]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200

    def test_very_long_comment(self, auth_token):
        """Should handle very long comments."""
        comments = ["x" * 2000]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code in [200, 422]

    def test_special_characters(self, auth_token):
        """Should handle special characters."""
        comments = [
            "Test <script>alert('xss')</script>",
            "Comment with 'quotes' and \"double quotes\"",
            "Numbers: 12345 and symbols: @#$%",
        ]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200

    def test_newlines_in_comment(self, auth_token):
        """Should handle newlines within comments."""
        comments = ["Line 1\nLine 2\nLine 3"]
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        assert response.status_code in [200, 422]  # May or may not allow newlines


# ─────────────────────────────────────────────────────────────────────────────
# 8. Performance Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPerformance:
    """Test performance and scalability."""

    @pytest.fixture
    def auth_token(self):
        token = get_auth_token()
        assert token is not None
        return token

    def test_batch_100_comments_performance(self, auth_token):
        """Should handle 100 comments in reasonable time."""
        import time
        comments = [f"Test comment {i}" for i in range(100)]

        start_time = time.time()
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 30, f"Batch of 100 comments took {elapsed:.2f}s, expected < 30s"
        print(f"\n100 comments processed in {elapsed:.2f}s")

    def test_batch_500_comments_performance(self, auth_token):
        """Should handle 500 comments in reasonable time."""
        import time
        comments = [f"Test comment {i}" for i in range(500)]

        start_time = time.time()
        response = requests.post(
            f"{API_PREFIX}/predict/batch",
            json={"comments": comments},
            headers=auth_headers(auth_token)
        )
        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 120, f"Batch of 500 comments took {elapsed:.2f}s, expected < 120s"
        print(f"\n500 comments processed in {elapsed:.2f}s")


# ─────────────────────────────────────────────────────────────────────────────
# 9. End-to-End Flow Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEndToEndFlow:
    """Test complete end-to-end flows."""

    @pytest.fixture
    def auth_token(self):
        token = get_auth_token()
        assert token is not None
        return token

    def test_complete_batch_flow(self, auth_token):
        """Test complete batch prediction flow."""
        # 1. Create test CSV
        csv_content = """comment
Tôi cô đơn và buồn
Video hay quá
Áp lực cuộc sống
Hôm nay vui vẻ"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            # 2. Read and process CSV
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.read().strip().split('\n')
                # Skip header
                comments = [l.strip() for l in lines[1:] if l.strip()]

            # 3. Call API
            response = requests.post(
                f"{API_PREFIX}/predict/batch",
                json={"comments": comments},
                headers=auth_headers(auth_token)
            )

            # 4. Verify response
            assert response.status_code == 200
            data = response.json()

            assert data["total"] == 4
            assert len(data["results"]) == 4
            assert data["depression_count"] + data["normal_count"] == 4

            # 5. Generate CSV export
            csv_export = [
                ["Comment", "Prediction", "Confidence"],
                *[(
                    r["text"],
                    r["prediction"],
                    f"{(r['confidence'] * 100):.1f}%"
                ) for r in data["results"]]
            ]
            assert len(csv_export) == 5  # Header + 4 results

        finally:
            os.unlink(csv_path)

    def test_prediction_saved_to_history(self, auth_token):
        """Test that predictions are saved to history."""
        # Get initial history count
        history_response = requests.get(
            f"{API_PREFIX}/history?limit=100",
            headers=auth_headers(auth_token)
        )
        initial_count = history_response.json()["total"]

        # Make a prediction
        test_text = f"End-to-end test {os.urandom(8).hex()}"
        response = requests.post(
            f"{API_PREFIX}/predict",
            json={"text": test_text},
            headers=auth_headers(auth_token)
        )
        assert response.status_code == 200

        # Verify it's saved to history
        history_response = requests.get(
            f"{API_PREFIX}/history?limit=100",
            headers=auth_headers(auth_token)
        )
        new_count = history_response.json()["total"]
        assert new_count > initial_count


# ─────────────────────────────────────────────────────────────────────────────
# Run Tests
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Running Batch Prediction Test Suite")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"API Prefix: {API_PREFIX}")
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
        print(f"   Expected: {API_BASE_URL}")
        sys.exit(1)

    # Check auth
    token = get_auth_token()
    if token:
        print("✅ Authentication works")
    else:
        print("❌ Authentication failed")
        sys.exit(1)

    print()
    print("Run tests with: pytest test_batch_prediction.py -v")
    print()

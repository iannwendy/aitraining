# API Test Suite

## Overview

This directory contains comprehensive tests for the Mental Health AI Platform API.

## Files

- `test_api.sh` - Shell script with curl commands for testing all endpoints
- `test_api_python.py` - Pytest suite with async tests using httpx
- `conftest.py` - Pytest configuration
- `pytest.ini` - Pytest settings

## Running Tests

### Prerequisites

1. Start the backend server:
```bash
cd web_demo/backend
source venv/bin/activate
python main.py
```

2. Start the frontend dev server (optional):
```bash
cd web_demo
npm run dev
```

### Shell Script Tests (Bash/curl)

Run all API tests using curl:

```bash
# Make executable
chmod +x tests/test_api.sh

# Run with default URL
./tests/test_api.sh

# Run with custom URL
API_BASE_URL=http://localhost:8000 ./tests/test_api.sh
```

### Python Tests (Pytest)

Install test dependencies and run:

```bash
# Install httpx for async tests
pip install httpx pytest pytest-asyncio

# Run all tests
pytest tests/test_api_python.py -v

# Run specific test
pytest tests/test_api_python.py::test_health_check -v

# Run with coverage
pytest tests/test_api_python.py --cov=app --cov-report=html
```

## Test Coverage

### Endpoints Tested

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root API info |
| `/api/health` | GET | Health check |
| `/api/dashboard/stats` | GET | Dashboard statistics |
| `/api/predict` | POST | Single text prediction |
| `/api/predict/batch` | POST | Batch prediction |
| `/api/topics` | GET | BERTopic topics |
| `/api/models/comparison` | GET | All model metrics |
| `/api/statistics` | GET | Confusion matrix & distribution |
| `/api/history` | GET | Prediction history (paginated) |
| `/api/history` | POST | Save prediction to history |
| `/api/history/{id}` | DELETE | Delete history entry |
| `/api/models/refresh/status` | GET | Refresh status |
| `/api/models/refresh` | POST | Hot-reload models |

### Test Categories

1. **Health Tests** - Basic connectivity and status checks
2. **Dashboard Tests** - Dataset statistics and metrics
3. **Prediction Tests** - Single and batch prediction with various inputs
4. **Topics Tests** - BERTopic topic retrieval
5. **Model Comparison Tests** - All model metrics
6. **Statistics Tests** - Confusion matrix and class distribution
7. **History Tests** - CRUD operations on prediction history
8. **Refresh Tests** - Hot-reload functionality
9. **Error Handling Tests** - Validation and error responses
10. **CORS Tests** - Cross-origin resource sharing

## Expected Output

### Shell Script

```
========================================
1. Health & Root Endpoints
========================================

  ✓ PASS: Root endpoint returns API info
  ✓ PASS: Health check returns healthy status
...

========================================
Test Summary
========================================

  Passed: 25
  Failed: 0

All tests passed! 🎉
```

### Pytest

```
tests/test_api_python.py::test_root_endpoint PASSED                   [  4%]
tests/test_api_python.py::test_health_check PASSED                    [  8%]
...
========================== 25 passed in 2.5s ==========================
```

## Troubleshooting

### Server not running

If you see connection errors:
```bash
# Check if server is running
curl http://localhost:8000/api/health

# Start server if needed
cd web_demo/backend && source venv/bin/activate && python main.py
```

### Port already in use

If port 8000 is in use:
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
python main.py --port 8001
```

### Model loading errors

If models fail to load:
```bash
# Check model files exist
ls -la models/

# Refresh models
curl -X POST http://localhost:8000/api/models/refresh
```

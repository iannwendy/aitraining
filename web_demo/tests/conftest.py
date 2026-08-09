"""
Pytest configuration for Mental Health AI API tests.
"""

import pytest
import httpx
import asyncio


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Get API base URL from environment or default."""
    import os
    return os.getenv("API_BASE_URL", "http://localhost:8000")

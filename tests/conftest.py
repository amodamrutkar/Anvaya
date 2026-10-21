"""
tests/conftest.py
Shared pytest fixtures for root integration & golden regression tests.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from sutradhar_api.main import app
from sutradhar_api.store import get_store


@pytest.fixture(scope="session", autouse=True)
def preload_store():
    """Load the data store once for the test session."""
    store = get_store()
    store.load()
    return store


@pytest.fixture
async def client():
    """Async test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

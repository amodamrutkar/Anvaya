"""
tests/test_entities.py
Tests for entity search, profile, and links.
"""

import pytest


@pytest.mark.asyncio
async def test_entity_search_hit(client):
    r = await client.get(
        "/entities/search", params={"q": "Rakesh"}, headers={"X-Demo-User": "analyst1"}
    )
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert any("Rakesh" in e.get("canonical_name", "") for e in body), (
        "Expected Rakesh Pawar in results"
    )


@pytest.mark.asyncio
async def test_entity_search_no_auth(client):
    r = await client.get("/entities/search", params={"q": "Rakesh"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_entity_not_found(client):
    r = await client.get("/entities/P-NONEXISTENT", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_entity_profile(client, preload_store):
    # Use a known entity from fixtures
    entity_id = next(iter(preload_store.entities))
    r = await client.get(f"/entities/{entity_id}", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    body = r.json()
    assert body["entity_id"] == entity_id


@pytest.mark.asyncio
async def test_entity_links(client, preload_store):
    entity_id = next(iter(preload_store.entities))
    r = await client.get(f"/entities/{entity_id}/links", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)

"""
tests/test_graph.py
Tests for graph read endpoints: communities, neighborhood, path, roles, bridges, and mule chains.
"""

import pytest

from sutradhar_api.store import get_store


@pytest.mark.asyncio
async def test_graph_communities(client):
    r = await client.get("/graph/communities", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_graph_community_detail(client):
    store = get_store()
    comm_id = next(iter(store.communities))
    r = await client.get(f"/graph/communities/{comm_id}", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    data = r.json()
    assert data["community_id"] == comm_id
    assert "roles" in data


@pytest.mark.asyncio
async def test_graph_neighborhood(client):
    store = get_store()
    eid = next(iter(store.entities))
    r = await client.get(f"/graph/entity/{eid}/neighborhood", headers={"X-Demo-User": "analyst1"})
    assert r.status_code == 200
    data = r.json()
    assert "nodes" in data
    assert "edges" in data


@pytest.mark.asyncio
async def test_graph_path(client):
    r = await client.get(
        "/graph/path?from=P-000045&to=P-000046", headers={"X-Demo-User": "analyst1"}
    )
    assert r.status_code == 200
    data = r.json()
    assert "path" in data


@pytest.mark.asyncio
async def test_roles_bridges_mules(client):
    r_roles = await client.get("/roles", headers={"X-Demo-User": "analyst1"})
    assert r_roles.status_code == 200
    assert isinstance(r_roles.json(), list)

    r_bridges = await client.get("/bridges", headers={"X-Demo-User": "analyst1"})
    assert r_bridges.status_code == 200
    assert isinstance(r_bridges.json(), list)

    r_mules = await client.get("/mule/chains", headers={"X-Demo-User": "analyst1"})
    assert r_mules.status_code == 200
    assert isinstance(r_mules.json(), list)

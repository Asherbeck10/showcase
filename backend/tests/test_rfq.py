"""Tests for GET /rfq/{product_ref}"""
from tests.conftest import login, auth


async def test_rfq_returns_quote(client):
    token = await login(client, "demo_client")
    resp = await client.get("/rfq/1", headers=auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_ref"] == 1
    assert data["isin"] == "XS1111111111"
    assert data["price"] == 101.25
    assert data["valid_for_seconds"] == 30


async def test_rfq_all_fields_present(client):
    token = await login(client, "demo_client")
    data = (await client.get("/rfq/2", headers=auth(token))).json()
    for field in ("product_ref", "isin", "description", "price", "valid_for_seconds"):
        assert field in data


async def test_rfq_not_found(client):
    token = await login(client, "demo_client")
    resp = await client.get("/rfq/9999", headers=auth(token))
    assert resp.status_code == 404


async def test_rfq_requires_auth(client):
    resp = await client.get("/rfq/1")
    assert resp.status_code == 401

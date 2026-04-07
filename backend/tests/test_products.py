"""Tests for GET /products"""
from tests.conftest import login, auth


async def test_list_products(client):
    token = await login(client, "demo_client")
    resp = await client.get("/products", headers=auth(token))
    assert resp.status_code == 200
    products = resp.json()
    assert len(products) == 5


async def test_products_fields(client):
    token = await login(client, "demo_client")
    products = (await client.get("/products", headers=auth(token))).json()
    p = products[0]
    for field in ("ref", "isin", "description", "bank", "bid", "ask"):
        assert field in p, f"Missing field: {field}"


async def test_products_requires_auth(client):
    resp = await client.get("/products")
    assert resp.status_code == 401


async def test_bank_can_list_products(client):
    token = await login(client, "demo_bank")
    resp = await client.get("/products", headers=auth(token))
    assert resp.status_code == 200

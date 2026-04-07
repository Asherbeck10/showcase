"""Tests for GET /orders and POST /trade"""
import pytest
from tests.conftest import login, auth


# ── GET /orders ───────────────────────────────────────────────────────────────

async def test_client_sees_own_orders(client):
    token = await login(client, "demo_client")
    resp = await client.get("/orders", headers=auth(token))
    assert resp.status_code == 200
    orders = resp.json()
    assert len(orders) == 3  # 3 pre-seeded trades


async def test_orders_fields(client):
    token = await login(client, "demo_client")
    orders = (await client.get("/orders", headers=auth(token))).json()
    o = orders[0]
    for field in ("id", "trade_ref", "product_ref", "buy_sell", "quantity", "price", "notional", "status", "created_at"):
        assert field in o


async def test_orders_requires_auth(client):
    resp = await client.get("/orders")
    assert resp.status_code == 401


async def test_seeded_statuses(client):
    token = await login(client, "demo_client")
    orders = (await client.get("/orders", headers=auth(token))).json()
    statuses = {o["trade_ref"]: o["status"] for o in orders}
    assert statuses["TRD-0001"] == "CONFIRMED"
    assert statuses["TRD-0002"] == "CONFIRMED"
    assert statuses["TRD-0003"] == "PENDING"


# ── POST /trade ───────────────────────────────────────────────────────────────

async def test_place_trade_success(client):
    token = await login(client, "demo_client")
    resp = await client.post(
        "/trade",
        json={"product_ref": 1, "buy_sell": "BUY", "quantity": 50000, "price": 101.25},
        headers=auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "PENDING"
    assert data["notional"] == 50000 * 101.25
    assert data["trade_ref"].startswith("TRD-")


async def test_place_sell_trade(client):
    token = await login(client, "demo_client")
    resp = await client.post(
        "/trade",
        json={"product_ref": 2, "buy_sell": "SELL", "quantity": 10000, "price": 97.00},
        headers=auth(token),
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "PENDING"


async def test_trade_appears_in_orders(client):
    token = await login(client, "demo_client")
    await client.post(
        "/trade",
        json={"product_ref": 3, "buy_sell": "BUY", "quantity": 25000, "price": 102.00},
        headers=auth(token),
    )
    orders = (await client.get("/orders", headers=auth(token))).json()
    assert any(o["product_ref"] == 3 and o["quantity"] == 25000 for o in orders)


async def test_trade_notional_calculated(client):
    token = await login(client, "demo_client")
    resp = await client.post(
        "/trade",
        json={"product_ref": 1, "buy_sell": "BUY", "quantity": 100000, "price": 101.25},
        headers=auth(token),
    )
    assert resp.json()["notional"] == pytest.approx(100000 * 101.25)


async def test_trade_invalid_buy_sell(client):
    token = await login(client, "demo_client")
    resp = await client.post(
        "/trade",
        json={"product_ref": 1, "buy_sell": "HOLD", "quantity": 1000, "price": 101.25},
        headers=auth(token),
    )
    assert resp.status_code == 400


async def test_trade_zero_quantity(client):
    token = await login(client, "demo_client")
    resp = await client.post(
        "/trade",
        json={"product_ref": 1, "buy_sell": "BUY", "quantity": 0, "price": 101.25},
        headers=auth(token),
    )
    assert resp.status_code == 400


async def test_trade_requires_auth(client):
    resp = await client.post(
        "/trade",
        json={"product_ref": 1, "buy_sell": "BUY", "quantity": 1000, "price": 101.25},
    )
    assert resp.status_code == 401

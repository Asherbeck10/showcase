"""Tests for bank approval endpoints: GET /orders/pending, GET /orders/approved, POST /orders/{ref}/approve"""
from tests.conftest import login, auth


# ── GET /orders/pending ───────────────────────────────────────────────────────

async def test_bank_can_list_pending(client):
    token = await login(client, "demo_bank")
    resp = await client.get("/orders/pending", headers=auth(token))
    assert resp.status_code == 200
    orders = resp.json()
    assert all(o["status"] == "PENDING" for o in orders)
    assert any(o["trade_ref"] == "TRD-0003" for o in orders)


async def test_client_cannot_list_pending(client):
    token = await login(client, "demo_client")
    resp = await client.get("/orders/pending", headers=auth(token))
    assert resp.status_code == 403


async def test_pending_requires_auth(client):
    resp = await client.get("/orders/pending")
    assert resp.status_code == 401


# ── GET /orders/approved ──────────────────────────────────────────────────────

async def test_bank_can_list_approved(client):
    token = await login(client, "demo_bank")
    resp = await client.get("/orders/approved", headers=auth(token))
    assert resp.status_code == 200
    orders = resp.json()
    assert all(o["status"] == "CONFIRMED" for o in orders)


async def test_approved_includes_seeded_confirmed(client):
    token = await login(client, "demo_bank")
    orders = (await client.get("/orders/approved", headers=auth(token))).json()
    refs = {o["trade_ref"] for o in orders}
    assert "TRD-0001" in refs
    assert "TRD-0002" in refs


async def test_client_cannot_list_approved(client):
    token = await login(client, "demo_client")
    resp = await client.get("/orders/approved", headers=auth(token))
    assert resp.status_code == 403


# ── POST /orders/{ref}/approve ────────────────────────────────────────────────

async def test_bank_approves_pending_order(client):
    token = await login(client, "demo_bank")
    resp = await client.post("/orders/TRD-0003/approve", headers=auth(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "CONFIRMED"


async def test_approved_order_leaves_pending_list(client):
    bank_token = await login(client, "demo_bank")
    await client.post("/orders/TRD-0003/approve", headers=auth(bank_token))
    pending = (await client.get("/orders/pending", headers=auth(bank_token))).json()
    assert not any(o["trade_ref"] == "TRD-0003" for o in pending)


async def test_approved_order_appears_in_history(client):
    bank_token = await login(client, "demo_bank")
    await client.post("/orders/TRD-0003/approve", headers=auth(bank_token))
    approved = (await client.get("/orders/approved", headers=auth(bank_token))).json()
    assert any(o["trade_ref"] == "TRD-0003" for o in approved)


async def test_client_order_status_updates_after_approval(client):
    client_token = await login(client, "demo_client")
    bank_token = await login(client, "demo_bank")
    await client.post("/orders/TRD-0003/approve", headers=auth(bank_token))
    orders = (await client.get("/orders", headers=auth(client_token))).json()
    statuses = {o["trade_ref"]: o["status"] for o in orders}
    assert statuses["TRD-0003"] == "CONFIRMED"


async def test_approve_already_confirmed_returns_400(client):
    token = await login(client, "demo_bank")
    resp = await client.post("/orders/TRD-0001/approve", headers=auth(token))
    assert resp.status_code == 400


async def test_approve_nonexistent_returns_404(client):
    token = await login(client, "demo_bank")
    resp = await client.post("/orders/TRD-9999/approve", headers=auth(token))
    assert resp.status_code == 404


async def test_client_cannot_approve(client):
    token = await login(client, "demo_client")
    resp = await client.post("/orders/TRD-0003/approve", headers=auth(token))
    assert resp.status_code == 403


async def test_approve_requires_auth(client):
    resp = await client.post("/orders/TRD-0003/approve")
    assert resp.status_code == 401

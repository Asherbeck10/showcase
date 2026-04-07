"""Tests for POST /token"""
import pytest
from tests.conftest import login


async def test_client_login_success(client):
    token = await login(client, "demo_client")
    assert token


async def test_bank_login_success(client):
    token = await login(client, "demo_bank")
    assert token


async def test_login_wrong_password(client):
    resp = await client.post(
        "/token",
        data={"username": "demo_client", "password": "wrong", "grant_type": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


async def test_login_unknown_user(client):
    resp = await client.post(
        "/token",
        data={"username": "nobody", "password": "demo123", "grant_type": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401


async def test_jwt_contains_usertype(client):
    import base64, json
    token = await login(client, "demo_client")
    payload = json.loads(base64.b64decode(token.split(".")[1] + "=="))
    assert payload["usertype"] == "client"
    assert payload["sub"] == "demo_client"


async def test_bank_jwt_contains_usertype(client):
    import base64, json
    token = await login(client, "demo_bank")
    payload = json.loads(base64.b64decode(token.split(".")[1] + "=="))
    assert payload["usertype"] == "bank"

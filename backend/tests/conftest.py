"""
Shared fixtures for all tests.
Each test gets a fresh in-memory DB with tables created and seeded.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import engine, Base
from app.seed import seed


@pytest.fixture
async def client():
    # Fresh schema + seed for every test (StaticPool keeps the same in-memory DB)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ── helpers ───────────────────────────────────────────────────────────────────

async def login(client: AsyncClient, username: str, password: str = "demo123") -> str:
    resp = await client.post(
        "/token",
        data={"username": username, "password": password, "grant_type": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

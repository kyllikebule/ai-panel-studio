"""REST API integration tests: in-memory SQLite + TestClient, 11 endpoints."""
import pytest
import importlib
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.backend.db import models as _models


@pytest.fixture(autouse=True)
async def _patch_db():
    """Per-test: inject in-memory engine + build tables, mock init_db."""
    import src.backend.db.database as db_mod

    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    db_mod.engine = engine
    db_mod.async_session = maker

    async with engine.begin() as conn:
        await conn.run_sync(_models.Base.metadata.create_all)

    patcher = patch.object(db_mod, "init_db", new=AsyncMock())
    patcher.start()
    try:
        import src.backend.main as main_mod
        importlib.reload(main_mod)
        yield
    finally:
        patcher.stop()


@pytest.fixture
async def async_client():
    import src.backend.main
    app = src.backend.main.app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ════════════════════════════
# Guest routes (4 endpoints)
# ════════════════════════════
class TestGuestRoutes:

    async def test_list_empty(self, async_client):
        res = await async_client.get("/api/guests/")
        assert res.status_code == 200
        assert res.json() == []

    async def test_create(self, async_client):
        payload = {"name": "alice", "persona": "AI expert person here", "system_prompt": "you are expert"}
        res = await async_client.post("/api/guests/", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "alice"
        assert "id" in data

    async def test_update(self, async_client):
        payload = {"name": "old", "persona": "old persona data here", "system_prompt": "sp"}
        create = await async_client.post("/api/guests/", json=payload)
        gid = create.json()["id"]
        res = await async_client.patch(f"/api/guests/{gid}", json={"name": "new"})
        assert res.status_code == 200
        assert res.json()["name"] == "new"

    async def test_delete(self, async_client):
        payload = {"name": "tmp", "persona": "tmp persona data here", "system_prompt": "sp"}
        create = await async_client.post("/api/guests/", json=payload)
        gid = create.json()["id"]
        res = await async_client.delete(f"/api/guests/{gid}")
        assert res.status_code == 204
        lst = await async_client.get("/api/guests/")
        ids = [g["id"] for g in lst.json()]
        assert gid not in ids


# ════════════════════════════
# Discussion routes (7 endpoints)
# ════════════════════════════
class TestDiscussionRoutes:

    async def _create(self, client, topic="AI", host="host1"):
        payload = {
            "topic": topic, "max_rounds": 5,
            "host": {"name": host, "system_prompt": "neutral host"},
        }
        return await client.post("/api/discussions/", json=payload)

    async def _create_guest(self, client):
        return await client.post("/api/guests/", json={
            "name": "alice", "persona": "expert persona text here",
            "system_prompt": "you are expert",
        })

    async def test_create_discussion(self, async_client):
        res = await self._create(async_client)
        assert res.status_code == 201
        data = res.json()
        assert data["topic"] == "AI"
        assert data["host_name"] == "host1"

    async def test_list_discussions(self, async_client):
        await self._create(async_client)
        res = await async_client.get("/api/discussions/")
        assert res.status_code == 200
        assert len(res.json()) >= 1

    async def test_get_discussion_detail(self, async_client):
        create = await self._create(async_client)
        did = create.json()["id"]
        res = await async_client.get(f"/api/discussions/{did}")
        assert res.status_code == 200
        assert "guests" in res.json()

    async def test_patch_discussion(self, async_client):
        create = await self._create(async_client)
        did = create.json()["id"]
        res = await async_client.patch(
            f"/api/discussions/{did}",
            json={"status": "active", "current_round": 1},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "active"

    async def test_delete_discussion(self, async_client):
        create = await self._create(async_client)
        did = create.json()["id"]
        res = await async_client.delete(f"/api/discussions/{did}")
        assert res.status_code == 204

    async def test_add_guest_to_discussion(self, async_client):
        d_res = await self._create(async_client)
        did = d_res.json()["id"]
        g_res = await self._create_guest(async_client)
        gid = g_res.json()["id"]
        res = await async_client.post(f"/api/discussions/{did}/guests", json={"guest_id": gid})
        assert res.status_code == 201
        res2 = await async_client.post(f"/api/discussions/{did}/guests", json={"guest_id": gid})
        assert res2.status_code == 409

    async def test_list_messages(self, async_client):
        create = await self._create(async_client)
        did = create.json()["id"]
        res = await async_client.get(f"/api/discussions/{did}/messages")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

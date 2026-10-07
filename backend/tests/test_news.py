import hashlib
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.schemas.news import NewsCreate, NewsUpdate
from app.services.news import NewsService


def _payload(**overrides) -> dict:
    base = {
        "title": "Title",
        "summary": "Summary",
        "tag": "tag",
        "source": "Source",
        "url": "https://example.com/a",
        "published_on": "2026-01-01",
        "published": True,
    }
    return {**base, **overrides}


async def _create(db: AsyncSession, **overrides):
    return await NewsService(db).create(NewsCreate(**_payload(**overrides)))


def _admin_headers(password: str) -> dict:
    return {"X-Admin-Token": hashlib.sha256(f"stem-admin:{password}".encode()).hexdigest()}


class TestNewsService:
    async def test_create_and_list(self, db_session: AsyncSession):
        item = await _create(db_session)
        svc = NewsService(db_session)
        assert item.id in [i.id for i in await svc.list(published_only=False, limit=10)]
        assert item.url == "https://example.com/a"
        assert isinstance(item.url, str)

    async def test_published_only_filter(self, db_session: AsyncSession):
        pub = await _create(db_session, published=True)
        draft = await _create(db_session, published=False)
        svc = NewsService(db_session)
        all_ids = {i.id for i in await svc.list(published_only=False, limit=10)}
        pub_ids = {i.id for i in await svc.list(published_only=True, limit=10)}
        assert {pub.id, draft.id} <= all_ids
        assert pub.id in pub_ids
        assert draft.id not in pub_ids

    async def test_ordering_published_on_desc_then_id_desc(self, db_session: AsyncSession):
        old = await _create(db_session, published_on=date(2025, 1, 1))
        new_a = await _create(db_session, published_on=date(2026, 1, 1))
        new_b = await _create(db_session, published_on=date(2026, 1, 1))
        items = await NewsService(db_session).list(published_only=False, limit=10)
        assert [i.id for i in items] == [new_b.id, new_a.id, old.id]

    async def test_list_limit(self, db_session: AsyncSession):
        for _ in range(3):
            await _create(db_session)
        assert len(await NewsService(db_session).list(published_only=False, limit=2)) == 2

    async def test_update(self, db_session: AsyncSession):
        item = await _create(db_session)
        svc = NewsService(db_session)
        updated = await svc.update(
            item.id,
            NewsUpdate(title="New", url="https://example.com/b", published=False, published_on=date(2024, 5, 6)),
        )
        assert updated is not None
        assert updated.title == "New"
        assert updated.url == "https://example.com/b"
        assert isinstance(updated.url, str)
        assert updated.published is False
        assert updated.published_on == date(2024, 5, 6)
        assert updated.summary == "Summary"
        assert await svc.update(999_999, NewsUpdate(title="x")) is None

    async def test_delete(self, db_session: AsyncSession):
        item = await _create(db_session)
        svc = NewsService(db_session)
        assert await svc.delete(item.id) is True
        assert await svc.delete(item.id) is False
        assert await svc.get(item.id) is None


class TestNewsPublicAPI:
    async def test_list_returns_only_published(self, client, db_session: AsyncSession):
        pub = await _create(db_session, published=True)
        await _create(db_session, published=False)
        resp = await client.get("/api/v1/news")
        assert resp.status_code == 200
        body = resp.json()
        assert [i["id"] for i in body] == [pub.id]
        assert body[0]["url"] == "https://example.com/a"
        assert body[0]["published_on"] == "2026-01-01"

    async def test_list_respects_limit(self, client, db_session: AsyncSession):
        for _ in range(3):
            await _create(db_session)
        resp = await client.get("/api/v1/news", params={"limit": 2})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_limit_out_of_range(self, client, db_session: AsyncSession):
        assert (await client.get("/api/v1/news", params={"limit": 0})).status_code == 422
        assert (await client.get("/api/v1/news", params={"limit": 51})).status_code == 422


class TestNewsAdminAPI:
    @pytest.fixture(autouse=True)
    def _admin_password(self, monkeypatch):
        monkeypatch.setattr(settings, "admin_password", "pw")

    async def test_without_token_401(self, client, db_session: AsyncSession):
        assert (await client.get("/api/v1/admin/news")).status_code == 401
        assert (await client.post("/api/v1/admin/news", json=_payload())).status_code == 401
        assert (await client.put("/api/v1/admin/news/1", json={"title": "x"})).status_code == 401
        assert (await client.delete("/api/v1/admin/news/1")).status_code == 401

    async def test_wrong_token_401(self, client, db_session: AsyncSession):
        resp = await client.get("/api/v1/admin/news", headers=_admin_headers("wrong"))
        assert resp.status_code == 401

    async def test_disabled_when_password_unset_403(self, client, db_session: AsyncSession, monkeypatch):
        monkeypatch.setattr(settings, "admin_password", "")
        resp = await client.get("/api/v1/admin/news", headers=_admin_headers("pw"))
        assert resp.status_code == 403

    async def test_crud(self, client, db_session: AsyncSession):
        headers = _admin_headers("pw")

        resp = await client.post("/api/v1/admin/news", json=_payload(published=False), headers=headers)
        assert resp.status_code == 201
        created = resp.json()
        news_id = created["id"]
        assert created["title"] == "Title"
        assert created["published"] is False

        resp = await client.get("/api/v1/admin/news", headers=headers)
        assert resp.status_code == 200
        assert news_id in [i["id"] for i in resp.json()]
        assert (await client.get("/api/v1/news")).json() == []

        resp = await client.put(
            f"/api/v1/admin/news/{news_id}",
            json={"title": "Updated", "url": "https://example.com/z", "published": True},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated"
        assert resp.json()["url"] == "https://example.com/z"
        assert [i["id"] for i in (await client.get("/api/v1/news")).json()] == [news_id]

        resp = await client.delete(f"/api/v1/admin/news/{news_id}", headers=headers)
        assert resp.status_code == 204

        assert (await client.put(f"/api/v1/admin/news/{news_id}", json={"title": "x"}, headers=headers)).status_code == 404
        assert (await client.delete(f"/api/v1/admin/news/{news_id}", headers=headers)).status_code == 404

    async def test_invalid_url_422(self, client, db_session: AsyncSession):
        headers = _admin_headers("pw")
        resp = await client.post("/api/v1/admin/news", json=_payload(url="not-a-url"), headers=headers)
        assert resp.status_code == 422
        resp = await client.post("/api/v1/admin/news", json=_payload(title=""), headers=headers)
        assert resp.status_code == 422

import pytest
from httpx import AsyncClient


# Helper functions to create test data
async def create_test_volume(client: AsyncClient, title: str = "Test Volume", description: str = None) -> dict:
    """Create a test volume via API"""
    response = await client.post(
        "/api/v1/volumes",
        json={"title": title, "description": description} if description else {"title": title},
    )
    assert response.status_code == 201
    return response.json()


async def create_test_chapter(client: AsyncClient, volume_id: int, title: str = "Test Chapter", description: str = None) -> dict:
    """Create a test chapter via API"""
    response = await client.post(
        "/api/v1/chapters",
        json={"volume_id": volume_id, "title": title, "description": description} if description else {"volume_id": volume_id, "title": title},
    )
    assert response.status_code == 201
    return response.json()


async def create_test_section(client: AsyncClient, chapter_id: int, title: str = "Test Section", content: str = None) -> dict:
    """Create a test section via API"""
    response = await client.post(
        "/api/v1/sections",
        json={"chapter_id": chapter_id, "title": title, "content": content} if content else {"chapter_id": chapter_id, "title": title},
    )
    assert response.status_code == 201
    return response.json()


class TestVolumeAPI:
    """Tests for Volume API endpoints"""

    @pytest.mark.asyncio
    async def test_create_volume(self, client: AsyncClient):
        """Golden path: create volume with valid data"""
        response = await client.post("/api/v1/volumes", json={"title": "New Volume", "description": "A new volume"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Volume"
        assert data["description"] == "A new volume"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_volume_minimal(self, client: AsyncClient):
        """Edge case: create volume with only required fields"""
        response = await client.post("/api/v1/volumes", json={"title": "Minimal Volume"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Volume"
        assert data["description"] is None
        assert data["order"] == 0

    @pytest.mark.asyncio
    async def test_create_volume_invalid_empty_title(self, client: AsyncClient):
        """Error case: create volume with empty title"""
        response = await client.post("/api/v1/volumes", json={"title": ""})
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_list_volumes_empty(self, client: AsyncClient):
        """Edge case: list volumes when none exist"""
        response = await client.get("/api/v1/volumes")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_volumes(self, client: AsyncClient):
        """Golden path: list volumes"""
        await create_test_volume(client, "Volume 1")
        await create_test_volume(client, "Volume 2")

        response = await client.get("/api/v1/volumes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_volumes_pagination(self, client: AsyncClient):
        """Edge case: list volumes with pagination"""
        for i in range(5):
            await create_test_volume(client, f"Volume {i}")

        response = await client.get("/api/v1/volumes?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_volume(self, client: AsyncClient):
        """Golden path: get existing volume"""
        created = await create_test_volume(client, "Get Test")
        response = await client.get(f"/api/v1/volumes/{created['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]
        assert data["title"] == "Get Test"

    @pytest.mark.asyncio
    async def test_get_volume_not_found(self, client: AsyncClient):
        """Error case: get non-existent volume"""
        response = await client.get("/api/v1/volumes/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_volume(self, client: AsyncClient):
        """Golden path: update existing volume"""
        created = await create_test_volume(client, "Original")
        response = await client.put(f"/api/v1/volumes/{created['id']}", json={"title": "Updated"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"

    @pytest.mark.asyncio
    async def test_update_volume_partial(self, client: AsyncClient):
        """Edge case: partial update"""
        created = await create_test_volume(client, "Original")
        response = await client.put(f"/api/v1/volumes/{created['id']}", json={"title": "New Title Only"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title Only"
        assert data["description"] is None  # unchanged

    @pytest.mark.asyncio
    async def test_update_volume_not_found(self, client: AsyncClient):
        """Error case: update non-existent volume"""
        response = await client.put("/api/v1/volumes/99999", json={"title": "Should fail"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_volume(self, client: AsyncClient):
        """Golden path: delete existing volume"""
        created = await create_test_volume(client, "To Delete")
        response = await client.delete(f"/api/v1/volumes/{created['id']}")
        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(f"/api/v1/volumes/{created['id']}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_volume_not_found(self, client: AsyncClient):
        """Error case: delete non-existent volume"""
        response = await client.delete("/api/v1/volumes/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_volume_chapters(self, client: AsyncClient):
        """Golden path: get chapters for a volume"""
        volume = await create_test_volume(client)
        await create_test_chapter(client, volume["id"], "Chapter 1")
        await create_test_chapter(client, volume["id"], "Chapter 2")

        response = await client.get(f"/api/v1/volumes/{volume['id']}/chapters")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_volume_chapters_not_found(self, client: AsyncClient):
        """Error case: get chapters for non-existent volume"""
        response = await client.get("/api/v1/volumes/99999/chapters")
        assert response.status_code == 404


class TestChapterAPI:
    """Tests for Chapter API endpoints"""

    @pytest.mark.asyncio
    async def test_create_chapter(self, client: AsyncClient):
        """Golden path: create chapter with valid data"""
        volume = await create_test_volume(client)
        response = await client.post(
            "/api/v1/chapters",
            json={"volume_id": volume["id"], "title": "New Chapter", "description": "A new chapter"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Chapter"
        assert data["volume_id"] == volume["id"]

    @pytest.mark.asyncio
    async def test_create_chapter_minimal(self, client: AsyncClient):
        """Edge case: create chapter with only required fields"""
        volume = await create_test_volume(client)
        response = await client.post("/api/v1/chapters", json={"volume_id": volume["id"], "title": "Minimal Chapter"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Chapter"
        assert data["description"] is None

    @pytest.mark.asyncio
    async def test_create_chapter_invalid_volume(self, client: AsyncClient):
        """Error case: create chapter with non-existent volume"""
        response = await client.post("/api/v1/chapters", json={"volume_id": 99999, "title": "Should fail"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_chapters(self, client: AsyncClient):
        """Golden path: list chapters"""
        volume = await create_test_volume(client)
        await create_test_chapter(client, volume["id"], "Chapter 1")
        await create_test_chapter(client, volume["id"], "Chapter 2")

        response = await client.get("/api/v1/chapters")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_chapters_pagination(self, client: AsyncClient):
        """Edge case: list chapters with pagination"""
        volume = await create_test_volume(client)
        for i in range(5):
            await create_test_chapter(client, volume["id"], f"Chapter {i}")

        response = await client.get("/api/v1/chapters?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_chapter(self, client: AsyncClient):
        """Golden path: get existing chapter"""
        volume = await create_test_volume(client)
        created = await create_test_chapter(client, volume["id"], "Get Test")
        response = await client.get(f"/api/v1/chapters/{created['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]
        assert data["title"] == "Get Test"

    @pytest.mark.asyncio
    async def test_get_chapter_not_found(self, client: AsyncClient):
        """Error case: get non-existent chapter"""
        response = await client.get("/api/v1/chapters/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_chapter(self, client: AsyncClient):
        """Golden path: update existing chapter"""
        volume = await create_test_volume(client)
        created = await create_test_chapter(client, volume["id"], "Original")
        response = await client.put(f"/api/v1/chapters/{created['id']}", json={"title": "Updated"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"

    @pytest.mark.asyncio
    async def test_update_chapter_change_volume(self, client: AsyncClient):
        """Golden path: update chapter to different volume"""
        volume1 = await create_test_volume(client, "Volume 1")
        volume2 = await create_test_volume(client, "Volume 2")
        chapter = await create_test_chapter(client, volume1["id"], "Test Chapter")

        response = await client.put(f"/api/v1/chapters/{chapter['id']}", json={"volume_id": volume2["id"]})
        assert response.status_code == 200
        data = response.json()
        assert data["volume_id"] == volume2["id"]

    @pytest.mark.asyncio
    async def test_update_chapter_invalid_volume(self, client: AsyncClient):
        """Error case: update chapter to non-existent volume"""
        volume = await create_test_volume(client)
        created = await create_test_chapter(client, volume["id"], "Original")
        response = await client.put(f"/api/v1/chapters/{created['id']}", json={"volume_id": 99999})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_chapter_not_found(self, client: AsyncClient):
        """Error case: update non-existent chapter"""
        response = await client.put("/api/v1/chapters/99999", json={"title": "Should fail"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_chapter(self, client: AsyncClient):
        """Golden path: delete existing chapter"""
        volume = await create_test_volume(client)
        created = await create_test_chapter(client, volume["id"], "To Delete")
        response = await client.delete(f"/api/v1/chapters/{created['id']}")
        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(f"/api/v1/chapters/{created['id']}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_chapter_not_found(self, client: AsyncClient):
        """Error case: delete non-existent chapter"""
        response = await client.delete("/api/v1/chapters/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_chapter_sections(self, client: AsyncClient):
        """Golden path: get sections for a chapter"""
        volume = await create_test_volume(client)
        chapter = await create_test_chapter(client, volume["id"], "Test Chapter")
        await create_test_section(client, chapter["id"], "Section 1")
        await create_test_section(client, chapter["id"], "Section 2")

        response = await client.get(f"/api/v1/chapters/{chapter['id']}/sections")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_chapter_sections_not_found(self, client: AsyncClient):
        """Error case: get sections for non-existent chapter"""
        response = await client.get("/api/v1/chapters/99999/sections")
        assert response.status_code == 404


class TestSectionAPI:
    """Tests for Section API endpoints"""

    @pytest.mark.asyncio
    async def test_create_section(self, client: AsyncClient):
        """Golden path: create section with valid data"""
        volume = await create_test_volume(client)
        chapter = await create_test_chapter(client, volume["id"], "Test Chapter")
        response = await client.post(
            "/api/v1/sections",
            json={"chapter_id": chapter["id"], "title": "New Section", "content": "Test content"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Section"
        assert data["content"] == "Test content"
        assert data["chapter_id"] == chapter["id"]

    @pytest.mark.asyncio
    async def test_create_section_minimal(self, client: AsyncClient):
        """Edge case: create section with only required fields"""
        volume = await create_test_volume(client)
        chapter = await create_test_chapter(client, volume["id"], "Test Chapter")
        response = await client.post("/api/v1/sections", json={"chapter_id": chapter["id"], "title": "Minimal Section"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Section"
        assert data["content"] is None

    @pytest.mark.asyncio
    async def test_create_section_invalid_chapter(self, client: AsyncClient):
        """Error case: create section with non-existent chapter"""
        response = await client.post("/api/v1/sections", json={"chapter_id": 99999, "title": "Should fail"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_sections(self, client: AsyncClient):
        """Golden path: list sections"""
        volume = await create_test_volume(client)
        chapter = await create_test_chapter(client, volume["id"], "Test Chapter")
        await create_test_section(client, chapter["id"], "Section 1")
        await create_test_section(client, chapter["id"], "Section 2")

        response = await client.get("/api/v1/sections")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_sections_pagination(self, client: AsyncClient):
        """Edge case: list sections with pagination"""
        volume = await create_test_volume(client)
        chapter = await create_test_chapter(client, volume["id"], "Test Chapter")
        for i in range(5):
            await create_test_section(client, chapter["id"], f"Section {i}")

        response = await client.get("/api/v1/sections?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_section(self, client: AsyncClient):
        """Golden path: get existing section"""
        volume = await create_test_volume(client)
        chapter = await create_test_chapter(client, volume["id"], "Test Chapter")
        created = await create_test_section(client, chapter["id"], "Get Test")

        response = await client.get(f"/api/v1/sections/{created['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]
        assert data["title"] == "Get Test"

    @pytest.mark.asyncio
    async def test_get_section_not_found(self, client: AsyncClient):
        """Error case: get non-existent section"""
        response = await client.get("/api/v1/sections/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_section(self, client: AsyncClient):
        """Golden path: update existing section"""
        volume = await create_test_volume(client)
        chapter = await create_test_chapter(client, volume["id"], "Test Chapter")
        created = await create_test_section(client, chapter["id"], "Original")

        response = await client.put(f"/api/v1/sections/{created['id']}", json={"title": "Updated"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"

    @pytest.mark.asyncio
    async def test_update_section_change_chapter(self, client: AsyncClient):
        """Golden path: update section to different chapter"""
        volume = await create_test_volume(client)
        chapter1 = await create_test_chapter(client, volume["id"], "Chapter 1")
        chapter2 = await create_test_chapter(client, volume["id"], "Chapter 2")
        section = await create_test_section(client, chapter1["id"], "Test Section")

        response = await client.put(f"/api/v1/sections/{section['id']}", json={"chapter_id": chapter2["id"]})
        assert response.status_code == 200
        data = response.json()
        assert data["chapter_id"] == chapter2["id"]

    @pytest.mark.asyncio
    async def test_update_section_invalid_chapter(self, client: AsyncClient):
        """Error case: update section to non-existent chapter"""
        volume = await create_test_volume(client)
        chapter = await create_test_chapter(client, volume["id"], "Test Chapter")
        created = await create_test_section(client, chapter["id"], "Original")

        response = await client.put(f"/api/v1/sections/{created['id']}", json={"chapter_id": 99999})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_section_not_found(self, client: AsyncClient):
        """Error case: update non-existent section"""
        response = await client.put("/api/v1/sections/99999", json={"title": "Should fail"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_section(self, client: AsyncClient):
        """Golden path: delete existing section"""
        volume = await create_test_volume(client)
        chapter = await create_test_chapter(client, volume["id"], "Test Chapter")
        created = await create_test_section(client, chapter["id"], "To Delete")

        response = await client.delete(f"/api/v1/sections/{created['id']}")
        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(f"/api/v1/sections/{created['id']}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_section_not_found(self, client: AsyncClient):
        """Error case: delete non-existent section"""
        response = await client.delete("/api/v1/sections/99999")
        assert response.status_code == 404

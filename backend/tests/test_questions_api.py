from httpx import AsyncClient

from app.models.question import QuestionType


QUESTIONS_URL = "/api/v1/questions"


async def create_test_volume(client: AsyncClient, title: str = "Test Volume") -> dict:
    response = await client.post("/api/v1/volumes", json={"title": title})
    assert response.status_code == 201
    return response.json()


async def create_test_chapter(client: AsyncClient, volume_id: int, title: str = "Test Chapter") -> dict:
    response = await client.post("/api/v1/chapters", json={"volume_id": volume_id, "title": title})
    assert response.status_code == 201
    return response.json()


async def create_test_section(client: AsyncClient, chapter_id: int, title: str = "Test Section") -> dict:
    response = await client.post("/api/v1/sections", json={"chapter_id": chapter_id, "title": title})
    assert response.status_code == 201
    return response.json()


async def create_knowledge_chain(client: AsyncClient) -> dict:
    volume = await create_test_volume(client)
    chapter = await create_test_chapter(client, volume["id"])
    section = await create_test_section(client, chapter["id"])
    return section


class TestQuestionAPI:
    """Tests for Question API endpoints"""

    async def test_create_question_full_data(self, client: AsyncClient):
        """Golden path: create question with full data"""
        section = await create_knowledge_chain(client)

        response = await client.post(QUESTIONS_URL, json={
            "type": "single_choice",
            "content": "What is 2+2?",
            "content_image": "https://example.com/img.png",
            "answer": "4",
            "answer_image": "https://example.com/ans.png",
            "analysis": "Basic arithmetic",
            "analysis_image": "https://example.com/analysis.png",
            "difficulty": "hard",
            "knowledge_point_ids": [section["id"]],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "single_choice"
        assert data["content"] == "What is 2+2?"
        assert data["content_image"] == "https://example.com/img.png"
        assert data["answer"] == "4"
        assert data["answer_image"] == "https://example.com/ans.png"
        assert data["analysis"] == "Basic arithmetic"
        assert data["analysis_image"] == "https://example.com/analysis.png"
        assert data["difficulty"] == "hard"
        assert section["id"] in data["knowledge_point_ids"]
        assert "id" in data
        assert "created_at" in data

    async def test_create_question_minimal(self, client: AsyncClient):
        """Golden path: create question with minimal data"""
        response = await client.post(QUESTIONS_URL, json={
            "type": "fill_blank",
            "content": "Fill in the blank",
            "answer": "answer",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "fill_blank"
        assert data["content"] == "Fill in the blank"
        assert data["answer"] == "answer"
        assert data["content_image"] is None
        assert data["answer_image"] is None
        assert data["analysis"] is None
        assert data["analysis_image"] is None
        assert data["difficulty"] == "medium"
        assert data["knowledge_point_ids"] == []

    async def test_create_question_with_knowledge_points(self, client: AsyncClient):
        """Golden path: create question with knowledge points"""
        section1 = await create_knowledge_chain(client)
        section2 = await create_knowledge_chain(client)

        response = await client.post(QUESTIONS_URL, json={
            "type": "multiple_choice",
            "content": "Select all correct",
            "answer": "A and B",
            "knowledge_point_ids": [section1["id"], section2["id"]],
        })
        assert response.status_code == 201
        data = response.json()
        assert len(data["knowledge_point_ids"]) == 2
        assert section1["id"] in data["knowledge_point_ids"]
        assert section2["id"] in data["knowledge_point_ids"]

    async def test_get_question_by_id(self, client: AsyncClient):
        """Golden path: get question by ID"""
        created = await create_test_question(client)

        response = await client.get(f"{QUESTIONS_URL}/{created['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]
        assert data["content"] == created["content"]

    async def test_list_questions(self, client: AsyncClient):
        """Golden path: list questions"""
        await create_test_question(client)
        await create_test_question(client)

        response = await client.get(QUESTIONS_URL)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    async def test_filter_questions_by_type(self, client: AsyncClient):
        """Golden path: filter questions by type"""
        await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "SC Q", "answer": "A",
        })
        await client.post(QUESTIONS_URL, json={
            "type": "multiple_choice", "content": "MC Q", "answer": "B",
        })

        response = await client.get(QUESTIONS_URL, params={"type": "single_choice"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(q["type"] == "single_choice" for q in data)

    async def test_filter_questions_by_difficulty(self, client: AsyncClient):
        """Golden path: filter questions by difficulty"""
        await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "Easy Q", "answer": "A", "difficulty": "easy",
        })
        await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "Hard Q", "answer": "B", "difficulty": "hard",
        })

        response = await client.get(QUESTIONS_URL, params={"difficulty": "hard"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(q["difficulty"] == "hard" for q in data)

    async def test_filter_questions_by_multiple_knowledge_point_ids(self, client: AsyncClient):
        """match_all_kps=true => AND semantics; default => OR semantics"""
        section1 = await create_knowledge_chain(client)
        section2 = await create_knowledge_chain(client)
        section3 = await create_knowledge_chain(client)

        await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "Q with KP1+KP2", "answer": "A",
            "knowledge_point_ids": [section1["id"], section2["id"]],
        })
        await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "Q with KP1 only", "answer": "A",
            "knowledge_point_ids": [section1["id"]],
        })
        await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "Q with KP3", "answer": "A",
            "knowledge_point_ids": [section3["id"]],
        })

        response = await client.get(QUESTIONS_URL, params={
            "knowledge_point_ids": [section1["id"], section2["id"]],
            "match_all_kps": "true",
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Q with KP1+KP2"

        response_or = await client.get(QUESTIONS_URL, params={
            "knowledge_point_ids": [section1["id"], section2["id"]],
        })
        assert response_or.status_code == 200
        data_or = response_or.json()
        assert {q["content"] for q in data_or} == {"Q with KP1+KP2", "Q with KP1 only"}

    async def test_filter_questions_by_volume_id(self, client: AsyncClient):
        """Golden path: filter questions by volume_id"""
        volume = await create_test_volume(client)
        chapter = await create_test_chapter(client, volume["id"])
        section = await create_test_section(client, chapter["id"])
        other_section = await create_knowledge_chain(client)

        await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "Q in volume", "answer": "A",
            "knowledge_point_ids": [section["id"]],
        })
        await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "Q in other volume", "answer": "A",
            "knowledge_point_ids": [other_section["id"]],
        })

        response = await client.get(QUESTIONS_URL, params={"volume_id": volume["id"]})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Q in volume"

    async def test_filter_questions_by_chapter_id(self, client: AsyncClient):
        """Golden path: filter questions by chapter_id"""
        volume = await create_test_volume(client)
        chapter = await create_test_chapter(client, volume["id"])
        section = await create_test_section(client, chapter["id"])
        other_chapter = await create_test_chapter(client, volume["id"], title="Other Chapter")
        other_section = await create_test_section(client, other_chapter["id"])

        await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "Q in chapter", "answer": "A",
            "knowledge_point_ids": [section["id"]],
        })
        await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "Q in other chapter", "answer": "A",
            "knowledge_point_ids": [other_section["id"]],
        })

        response = await client.get(QUESTIONS_URL, params={"chapter_id": chapter["id"]})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Q in chapter"

    async def test_filter_questions_by_chapter_and_knowledge_point(self, client: AsyncClient):
        """Golden path: filter questions by chapter_id and knowledge_point_ids"""
        volume = await create_test_volume(client)
        chapter = await create_test_chapter(client, volume["id"])
        section1 = await create_test_section(client, chapter["id"])
        section2 = await create_test_section(client, chapter["id"], title="Section 2")

        await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "Q with KP1", "answer": "A",
            "knowledge_point_ids": [section1["id"]],
        })
        await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "Q with KP2", "answer": "A",
            "knowledge_point_ids": [section2["id"]],
        })
        await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "Q with KP1+KP2", "answer": "A",
            "knowledge_point_ids": [section1["id"], section2["id"]],
        })

        response = await client.get(QUESTIONS_URL, params={
            "chapter_id": chapter["id"],
            "knowledge_point_ids": [section1["id"]],
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_update_question(self, client: AsyncClient):
        """Golden path: update question"""
        created = await create_test_question(client)

        response = await client.put(f"{QUESTIONS_URL}/{created['id']}", json={
            "content": "Updated content",
            "answer": "Updated answer",
            "difficulty": "hard",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["answer"] == "Updated answer"
        assert data["difficulty"] == "hard"

    async def test_delete_question(self, client: AsyncClient):
        """Golden path: delete question"""
        created = await create_test_question(client)

        response = await client.delete(f"{QUESTIONS_URL}/{created['id']}")
        assert response.status_code == 204

        get_response = await client.get(f"{QUESTIONS_URL}/{created['id']}")
        assert get_response.status_code == 404

    async def test_create_question_default_difficulty(self, client: AsyncClient):
        """Edge case: create question with default difficulty"""
        response = await client.post(QUESTIONS_URL, json={
            "type": "calculation", "content": "Calculate", "answer": "42",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["difficulty"] == "medium"

    async def test_list_with_pagination(self, client: AsyncClient):
        """Edge case: list with pagination"""
        for i in range(5):
            await client.post(QUESTIONS_URL, json={
                "type": "single_choice", "content": f"Page Q{i}", "answer": f"A{i}",
            })

        response = await client.get(QUESTIONS_URL, params={"skip": 2, "limit": 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_partial_update(self, client: AsyncClient):
        """Edge case: partial update"""
        created = await create_test_question(client)

        response = await client.put(f"{QUESTIONS_URL}/{created['id']}", json={
            "type": "multiple_choice",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "multiple_choice"
        assert data["content"] == created["content"]
        assert data["answer"] == created["answer"]

    async def test_get_nonexistent_question(self, client: AsyncClient):
        """Error case: get non-existent question -> 404"""
        response = await client.get(f"{QUESTIONS_URL}/99999")
        assert response.status_code == 404

    async def test_update_nonexistent_question(self, client: AsyncClient):
        """Error case: update non-existent question -> 404"""
        response = await client.put(f"{QUESTIONS_URL}/99999", json={"content": "Nope"})
        assert response.status_code == 404

    async def test_delete_nonexistent_question(self, client: AsyncClient):
        """Error case: delete non-existent question -> 404"""
        response = await client.delete(f"{QUESTIONS_URL}/99999")
        assert response.status_code == 404

    async def test_create_with_invalid_type(self, client: AsyncClient):
        """Error case: create with invalid type -> 422"""
        response = await client.post(QUESTIONS_URL, json={
            "type": "invalid_type", "content": "Q", "answer": "A",
        })
        assert response.status_code == 422

    async def test_create_with_empty_content(self, client: AsyncClient):
        """Error case: create with empty content -> 422"""
        response = await client.post(QUESTIONS_URL, json={
            "type": "single_choice", "content": "", "answer": "A",
        })
        assert response.status_code == 422



async def create_test_question(client: AsyncClient, **overrides) -> dict:
    payload = {
        "type": "single_choice",
        "content": "Test question",
        "answer": "Test answer",
    }
    payload.update(overrides)
    response = await client.post(QUESTIONS_URL, json=payload)
    assert response.status_code == 201
    return response.json()

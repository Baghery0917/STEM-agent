from httpx import AsyncClient

from app.models.student import Gender


STUDENTS_URL = "/api/v1/students"


async def create_test_student(client: AsyncClient, **overrides) -> dict:
    payload = {"name": "Test Student", "gender": Gender.MALE.value}
    payload.update(overrides)
    response = await client.post(STUDENTS_URL, json=payload)
    assert response.status_code == 201
    return response.json()


class TestStudentAPI:
    """Tests for Student API endpoints"""

    async def test_create_student(self, client: AsyncClient):
        """Golden path: create a student"""
        response = await client.post(STUDENTS_URL, json={
            "name": "Alice",
            "gender": Gender.FEMALE.value,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Alice"
        assert data["gender"] == Gender.FEMALE.value
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_get_student_by_id(self, client: AsyncClient):
        """Golden path: get a student by id"""
        created = await create_test_student(client, name="Bob")

        response = await client.get(f"{STUDENTS_URL}/{created['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]
        assert data["name"] == "Bob"

    async def test_list_students(self, client: AsyncClient):
        """Golden path: list all students"""
        await create_test_student(client, name="Alice")
        await create_test_student(client, name="Bob")

        response = await client.get(STUDENTS_URL)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    async def test_list_students_with_gender_filter(self, client: AsyncClient):
        """Golden path: list students filtered by gender"""
        await create_test_student(client, name="Alice", gender=Gender.FEMALE.value)
        await create_test_student(client, name="Bob", gender=Gender.MALE.value)
        await create_test_student(client, name="Charlie", gender=Gender.MALE.value)

        response = await client.get(STUDENTS_URL, params={"gender": Gender.MALE.value})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(s["gender"] == Gender.MALE.value for s in data)

    async def test_list_students_pagination(self, client: AsyncClient):
        """Golden path: list students with pagination"""
        for i in range(5):
            await create_test_student(client, name=f"Student{i}")

        response = await client.get(STUDENTS_URL, params={"skip": 2, "limit": 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_update_student(self, client: AsyncClient):
        """Golden path: update a student"""
        created = await create_test_student(client, name="Old Name", gender=Gender.MALE.value)

        response = await client.put(f"{STUDENTS_URL}/{created['id']}", json={
            "name": "New Name",
            "gender": Gender.FEMALE.value,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["gender"] == Gender.FEMALE.value

    async def test_partial_update_student(self, client: AsyncClient):
        """Golden path: partial update (only name)"""
        created = await create_test_student(client, name="Original", gender=Gender.MALE.value)

        response = await client.put(f"{STUDENTS_URL}/{created['id']}", json={
            "name": "Updated",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["gender"] == Gender.MALE.value

    async def test_delete_student(self, client: AsyncClient):
        """Golden path: delete a student"""
        created = await create_test_student(client, name="ToDelete")

        response = await client.delete(f"{STUDENTS_URL}/{created['id']}")
        assert response.status_code == 204

        get_response = await client.get(f"{STUDENTS_URL}/{created['id']}")
        assert get_response.status_code == 404

    async def test_create_student_with_max_length_name(self, client: AsyncClient):
        """Edge case: create student with 100-character name (boundary)"""
        long_name = "A" * 100
        response = await client.post(STUDENTS_URL, json={
            "name": long_name,
            "gender": Gender.FEMALE.value,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == long_name

    async def test_list_students_skip_beyond_total(self, client: AsyncClient):
        """Edge case: skip beyond total count returns empty list"""
        await create_test_student(client)

        response = await client.get(STUDENTS_URL, params={"skip": 100, "limit": 10})
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_students_limit_zero(self, client: AsyncClient):
        """Edge case: limit of zero returns empty list"""
        await create_test_student(client)

        response = await client.get(STUDENTS_URL, params={"skip": 0, "limit": 0})
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_students_gender_filter_no_matches(self, client: AsyncClient):
        """Edge case: gender filter with no matches returns empty list"""
        await create_test_student(client, name="Alice", gender=Gender.FEMALE.value)

        response = await client.get(STUDENTS_URL, params={"gender": Gender.MALE.value})
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_nonexistent_student(self, client: AsyncClient):
        """Error case: get non-existent student -> 404"""
        response = await client.get(f"{STUDENTS_URL}/99999")
        assert response.status_code == 404

    async def test_update_nonexistent_student(self, client: AsyncClient):
        """Error case: update non-existent student -> 404"""
        response = await client.put(f"{STUDENTS_URL}/99999", json={"name": "Nope"})
        assert response.status_code == 404

    async def test_delete_nonexistent_student(self, client: AsyncClient):
        """Error case: delete non-existent student -> 404"""
        response = await client.delete(f"{STUDENTS_URL}/99999")
        assert response.status_code == 404

    async def test_create_with_empty_name(self, client: AsyncClient):
        """Error case: create with empty name -> 422"""
        response = await client.post(STUDENTS_URL, json={
            "name": "",
            "gender": Gender.MALE.value,
        })
        assert response.status_code == 422

    async def test_create_with_invalid_gender(self, client: AsyncClient):
        """Error case: create with invalid gender -> 422"""
        response = await client.post(STUDENTS_URL, json={
            "name": "Alice",
            "gender": "invalid_gender",
        })
        assert response.status_code == 422

    async def test_create_with_name_too_long(self, client: AsyncClient):
        """Error case: create with name over 100 chars -> 422"""
        response = await client.post(STUDENTS_URL, json={
            "name": "A" * 101,
            "gender": Gender.MALE.value,
        })
        assert response.status_code == 422

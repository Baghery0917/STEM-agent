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


SIGNATURE = "M10 40 L20 30 Q30 20 40 40"


class TestStudentSignature:
    """Tests for the student roommate-agreement signature field"""

    async def test_create_student_with_signature(self, client: AsyncClient):
        """Golden path: create with a valid signature echoes it, GET returns it"""
        response = await client.post(STUDENTS_URL, json={
            "name": "Alice",
            "gender": Gender.FEMALE.value,
            "signature": SIGNATURE,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["signature"] == SIGNATURE

        get_response = await client.get(f"{STUDENTS_URL}/{data['id']}")
        assert get_response.status_code == 200
        assert get_response.json()["signature"] == SIGNATURE

    async def test_create_student_without_signature(self, client: AsyncClient):
        """Golden path: create without signature -> signature is null"""
        created = await create_test_student(client)
        assert created["signature"] is None

        get_response = await client.get(f"{STUDENTS_URL}/{created['id']}")
        assert get_response.json()["signature"] is None

    async def test_update_signature(self, client: AsyncClient):
        """Golden path: PUT sets the signature"""
        created = await create_test_student(client)
        new_signature = "M0 0 L260 80"

        response = await client.put(f"{STUDENTS_URL}/{created['id']}", json={
            "signature": new_signature,
        })
        assert response.status_code == 200
        assert response.json()["signature"] == new_signature

        get_response = await client.get(f"{STUDENTS_URL}/{created['id']}")
        assert get_response.json()["signature"] == new_signature

    async def test_update_other_fields_keeps_signature(self, client: AsyncClient):
        """Golden path: PUT without signature leaves it unchanged"""
        created = await create_test_student(client, signature=SIGNATURE)

        response = await client.put(f"{STUDENTS_URL}/{created['id']}", json={
            "name": "Renamed",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Renamed"
        assert data["signature"] == SIGNATURE

    async def test_create_with_decimal_and_negative_coords(self, client: AsyncClient):
        """Edge: decimals and negative numbers are accepted"""
        signature = "M10.5 40.25 L-1 30 Q30.0 20 40 40"
        created = await create_test_student(client, signature=signature)
        assert created["signature"] == signature

    async def test_create_with_min_length_signature(self, client: AsyncClient):
        """Edge: 3-character signature (boundary) is accepted"""
        created = await create_test_student(client, signature="M10")
        assert created["signature"] == "M10"

    async def test_create_with_max_length_signature(self, client: AsyncClient):
        """Edge: 20000-character signature (boundary) is accepted"""
        signature = "M" + "1" * 19999
        created = await create_test_student(client, signature=signature)
        assert created["signature"] == signature

    async def test_create_with_script_tag_signature(self, client: AsyncClient):
        """Edge: signature containing <script> -> 422"""
        response = await client.post(STUDENTS_URL, json={
            "name": "Mallory",
            "gender": Gender.MALE.value,
            "signature": "M10 40 <script>alert(1)</script>",
        })
        assert response.status_code == 422

    async def test_create_with_disallowed_path_command(self, client: AsyncClient):
        """Edge: signature using Z or C commands -> 422"""
        for signature in ("M10 40 L20 30 Z", "M10 40 C20 30 30 20 40 40"):
            response = await client.post(STUDENTS_URL, json={
                "name": "Alice",
                "gender": Gender.FEMALE.value,
                "signature": signature,
            })
            assert response.status_code == 422, signature

    async def test_create_with_signature_too_short(self, client: AsyncClient):
        """Edge: signature under 3 chars -> 422"""
        response = await client.post(STUDENTS_URL, json={
            "name": "Alice",
            "gender": Gender.FEMALE.value,
            "signature": "M1",
        })
        assert response.status_code == 422

    async def test_create_with_signature_too_long(self, client: AsyncClient):
        """Edge: signature over 20000 chars -> 422"""
        response = await client.post(STUDENTS_URL, json={
            "name": "Alice",
            "gender": Gender.FEMALE.value,
            "signature": "M" + "1" * 20000,
        })
        assert response.status_code == 422

    async def test_update_with_invalid_signature(self, client: AsyncClient):
        """Edge: PUT with invalid signature -> 422 and stored value unchanged"""
        created = await create_test_student(client, signature=SIGNATURE)

        response = await client.put(f"{STUDENTS_URL}/{created['id']}", json={
            "signature": "M10 40 Z",
        })
        assert response.status_code == 422

        get_response = await client.get(f"{STUDENTS_URL}/{created['id']}")
        assert get_response.json()["signature"] == SIGNATURE

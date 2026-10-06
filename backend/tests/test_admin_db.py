from datetime import datetime

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base
from app.models.practice import PracticeSession
from app.models.question import Difficulty, Question, QuestionType
from app.models.student import Gender, Student
from app.models.teaching import TeachingSession, TeachingSessionStatus


ADMIN_URL = "/api/v1/admin/db"

EXPECTED_TABLES = {
    "volumes",
    "chapters",
    "sections",
    "questions",
    "students",
    "teaching_sessions",
    "teaching_messages",
    "practice_sessions",
    "practice_items",
    "student_knowledge_summaries",
    "teaching_references",
}


async def _make_student(db: AsyncSession, name: str = "S") -> Student:
    s = Student(name=name, gender=Gender.MALE)
    db.add(s)
    await db.flush()
    await db.refresh(s)
    return s


class TestAdminDbListTables:
    """Tests for GET /api/v1/admin/db/tables"""

    async def test_lists_all_whitelisted_tables(self, client: AsyncClient):
        """Golden path: response includes every table in Base.metadata.tables, with row_count and columns"""
        response = await client.get(f"{ADMIN_URL}/tables")
        assert response.status_code == 200
        data = response.json()

        names_in_response = {item["name"] for item in data}
        # Sanity: all registered tables are included
        assert set(Base.metadata.tables.keys()).issubset(names_in_response)
        # Explicit check for the tables the spec calls out
        assert EXPECTED_TABLES.issubset(names_in_response)

        for item in data:
            assert isinstance(item["columns"], list)
            assert len(item["columns"]) > 0
            assert isinstance(item["row_count"], int)
            assert item["row_count"] >= 0

    async def test_column_schema_shape(self, client: AsyncClient):
        """Each column entry has name, non-empty type string, nullable, primary_key"""
        response = await client.get(f"{ADMIN_URL}/tables")
        assert response.status_code == 200
        data = response.json()

        for item in data:
            for col in item["columns"]:
                assert "name" in col and isinstance(col["name"], str) and col["name"]
                assert "type" in col and isinstance(col["type"], str) and col["type"]
                assert "nullable" in col and isinstance(col["nullable"], bool)
                assert "primary_key" in col and isinstance(col["primary_key"], bool)

    async def test_questions_table_reports_vector_column_type(self, client: AsyncClient):
        """Schema reports questions.embedding as a VECTOR-typed column (pgvector)."""
        response = await client.get(f"{ADMIN_URL}/tables")
        assert response.status_code == 200
        data = response.json()

        questions = next(t for t in data if t["name"] == "questions")
        embedding = next(c for c in questions["columns"] if c["name"] == "embedding")
        assert embedding["type"].upper().startswith("VECTOR")


class TestAdminDbQueryRowsBasic:
    """Tests for GET /api/v1/admin/db/tables/{table_name}"""

    async def test_returns_rows_and_total(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """Golden path: rows come back after seeding, total matches count, limit is respected"""
        for i in range(3):
            await _make_student(db_session, name=f"S{i}")

        response = await client.get(
            f"{ADMIN_URL}/tables/students", params={"limit": 2},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["table"] == "students"
        assert data["total"] == 3
        assert len(data["rows"]) == 2
        # Columns are reported alongside rows
        col_names = {c["name"] for c in data["columns"]}
        assert {"id", "name", "gender"}.issubset(col_names)

    async def test_default_sort_is_pk_desc(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """Default order is first PK column DESC — newest (highest id) first."""
        s1 = await _make_student(db_session, name="first")
        s2 = await _make_student(db_session, name="second")
        s3 = await _make_student(db_session, name="third")

        response = await client.get(f"{ADMIN_URL}/tables/students")
        assert response.status_code == 200
        rows = response.json()["rows"]

        ids = [row["id"] for row in rows]
        assert ids == sorted(ids, reverse=True)
        assert ids[0] == s3.id

    async def test_pagination_middle_row(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """limit=1 offset=1 returns the middle row in default PK-desc order."""
        s1 = await _make_student(db_session, name="a")
        s2 = await _make_student(db_session, name="b")
        s3 = await _make_student(db_session, name="c")

        response = await client.get(
            f"{ADMIN_URL}/tables/students",
            params={"limit": 1, "offset": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["rows"]) == 1
        assert data["rows"][0]["id"] == s2.id

    async def test_unknown_table_returns_404(self, client: AsyncClient):
        """Error case: unknown table name -> 404 with detail mentioning the name."""
        response = await client.get(f"{ADMIN_URL}/tables/no_such_table")
        assert response.status_code == 404
        assert "no_such_table" in response.json()["detail"]

    async def test_unknown_sort_column_returns_400(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """Error case: unknown sort column -> 400."""
        await _make_student(db_session)

        response = await client.get(
            f"{ADMIN_URL}/tables/students",
            params={"sort": "no_such_col"},
        )
        assert response.status_code == 400
        assert "no_such_col" in response.json()["detail"]

    async def test_sort_asc_on_valid_column(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """Valid sort + order=asc returns rows ascending by that column."""
        await _make_student(db_session, name="Charlie")
        await _make_student(db_session, name="Alice")
        await _make_student(db_session, name="Bob")

        response = await client.get(
            f"{ADMIN_URL}/tables/students",
            params={"sort": "name", "order": "asc"},
        )
        assert response.status_code == 200
        names = [row["name"] for row in response.json()["rows"]]
        assert names == sorted(names)
        assert names[0] == "Alice"


class TestAdminDbSerialization:
    """Tests for _serialize_value behavior exposed via the query endpoint."""

    async def test_long_string_truncated_with_ellipsis(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """String >200 chars gets truncated to 200 + single ellipsis char (total length 201)."""
        long_content = "x" * 500
        q = Question(
            type=QuestionType.SINGLE_CHOICE,
            content=long_content,
            answer="A",
            difficulty=Difficulty.EASY,
        )
        db_session.add(q)
        await db_session.flush()

        response = await client.get(f"{ADMIN_URL}/tables/questions")
        assert response.status_code == 200
        rows = response.json()["rows"]
        assert len(rows) == 1

        content = rows[0]["content"]
        assert content.endswith("…")
        assert len(content) == 201
        assert content[:200] == "x" * 200

    async def test_array_columns_serialized_as_json_strings(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """list/tuple/set columns come back as json.dumps(...) strings."""
        student = await _make_student(db_session)
        ps = PracticeSession(
            timed=False,
            knowledge_point_ids=[1, 2, 3],
            difficulty_range=[Difficulty.EASY, Difficulty.MEDIUM],
            student_id=student.id,
            total_count=0,
            started_at=datetime(2026, 4, 22, 10, 0, 0),
        )
        db_session.add(ps)
        await db_session.flush()

        response = await client.get(f"{ADMIN_URL}/tables/practice_sessions")
        assert response.status_code == 200
        rows = response.json()["rows"]
        assert len(rows) == 1
        row = rows[0]

        kp_ids = row["knowledge_point_ids"]
        assert isinstance(kp_ids, str)
        assert kp_ids == "[1, 2, 3]"

        diff_range = row["difficulty_range"]
        assert isinstance(diff_range, str)
        # Enum values are serialized via default=str; accept either the .value form
        # or the enum-repr form since Difficulty is a (str, Enum) subclass.
        assert "easy" in diff_range.lower()
        assert "medium" in diff_range.lower()
        # JSON-list shape, not Python repr
        assert diff_range.startswith("[") and diff_range.endswith("]")

    async def test_pgvector_column_rendered_as_placeholder(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """Vector columns come back as 'vector[<len>]' placeholder, never raw floats."""
        q = Question(
            type=QuestionType.SINGLE_CHOICE,
            content="Q with embedding",
            answer="A",
            difficulty=Difficulty.EASY,
            embedding=[0.0] * 1024,
        )
        db_session.add(q)
        await db_session.flush()

        response = await client.get(f"{ADMIN_URL}/tables/questions")
        assert response.status_code == 200
        rows = response.json()["rows"]
        assert len(rows) == 1
        assert rows[0]["embedding"] == "vector[1024]"

    async def test_null_vector_stays_none(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """None is preserved in serialization (not converted to 'vector[...]')."""
        q = Question(
            type=QuestionType.SINGLE_CHOICE,
            content="Q no embedding",
            answer="A",
            difficulty=Difficulty.EASY,
            embedding=None,
        )
        db_session.add(q)
        await db_session.flush()

        response = await client.get(f"{ADMIN_URL}/tables/questions")
        assert response.status_code == 200
        rows = response.json()["rows"]
        assert len(rows) == 1
        assert rows[0]["embedding"] is None

    async def test_enum_column_returns_value_string(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """Enum column value comes back as .value string, not an Enum repr."""
        student = await _make_student(db_session)
        ts = TeachingSession(
            student_id=student.id,
            status=TeachingSessionStatus.ACTIVE,
        )
        db_session.add(ts)
        await db_session.flush()

        response = await client.get(f"{ADMIN_URL}/tables/teaching_sessions")
        assert response.status_code == 200
        rows = response.json()["rows"]
        assert len(rows) == 1
        assert rows[0]["status"] == "active"

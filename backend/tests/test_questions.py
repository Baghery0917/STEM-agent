from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question, QuestionType, Difficulty
from app.schemas.chapter import ChapterCreate
from app.schemas.question import QuestionCreate, QuestionUpdate
from app.schemas.section import SectionCreate
from app.schemas.volume import VolumeCreate
from app.services.chapter import ChapterService
from app.services.question import QuestionService
from app.services.section import SectionService
from app.services.volume import VolumeService


def make_vector(dim: int = 1024, fill: float = 0.0) -> list[float]:
    return [fill] * dim


def make_basis_vector(dim: int = 1024, index: int = 0, value: float = 1.0) -> list[float]:
    v = [0.0] * dim
    v[index] = value
    return v


async def create_test_volume(db: AsyncSession):
    service = VolumeService(db)
    return await service.create(VolumeCreate(title="Test Volume"))


async def create_test_chapter(db: AsyncSession, volume_id: int):
    service = ChapterService(db)
    return await service.create(ChapterCreate(volume_id=volume_id, title="Test Chapter"))


async def create_test_section(db: AsyncSession, chapter_id: int):
    service = SectionService(db)
    return await service.create(SectionCreate(chapter_id=chapter_id, title="Test Section"))


async def create_knowledge_chain(db: AsyncSession):
    volume = await create_test_volume(db)
    chapter = await create_test_chapter(db, volume.id)
    section = await create_test_section(db, chapter.id)
    return volume, chapter, section


class TestQuestionService:
    """Tests for QuestionService"""

    async def test_create_question_with_all_fields(self, db_session: AsyncSession):
        """Golden path: create question with all fields"""
        _, _, section = await create_knowledge_chain(db_session)

        service = QuestionService()
        data = QuestionCreate(
            type=QuestionType.SINGLE_CHOICE,
            content="What is 2+2?",
            content_image="https://example.com/img.png",
            answer="4",
            answer_image="https://example.com/ans.png",
            analysis="Basic arithmetic",
            analysis_image="https://example.com/analysis.png",
            difficulty=Difficulty.HARD,
            knowledge_point_ids=[section.id],
        )
        question = await service.create(db_session, data)

        assert question.id is not None
        assert question.type == QuestionType.SINGLE_CHOICE
        assert question.content == "What is 2+2?"
        assert question.content_image == "https://example.com/img.png"
        assert question.answer == "4"
        assert question.answer_image == "https://example.com/ans.png"
        assert question.analysis == "Basic arithmetic"
        assert question.analysis_image == "https://example.com/analysis.png"
        assert question.difficulty == Difficulty.HARD
        assert section.id in question.knowledge_point_ids

    async def test_create_question_minimal(self, db_session: AsyncSession):
        """Golden path: create question with minimal fields (only required: type, content, answer)"""
        service = QuestionService()
        data = QuestionCreate(
            type=QuestionType.FILL_BLANK,
            content="Fill in the blank",
            answer="answer",
        )
        question = await service.create(db_session, data)

        assert question.id is not None
        assert question.type == QuestionType.FILL_BLANK
        assert question.content == "Fill in the blank"
        assert question.answer == "answer"
        assert question.content_image is None
        assert question.answer_image is None
        assert question.analysis is None
        assert question.analysis_image is None
        assert question.difficulty == Difficulty.MEDIUM
        assert question.knowledge_point_ids == []

    async def test_create_question_with_knowledge_points(self, db_session: AsyncSession):
        """Golden path: create question with knowledge points"""
        _, _, section1 = await create_knowledge_chain(db_session)
        _, _, section2 = await create_knowledge_chain(db_session)

        service = QuestionService()
        data = QuestionCreate(
            type=QuestionType.MULTIPLE_CHOICE,
            content="Select all correct answers",
            answer="A and B",
            knowledge_point_ids=[section1.id, section2.id],
        )
        question = await service.create(db_session, data)

        assert len(question.knowledge_point_ids) == 2
        assert section1.id in question.knowledge_point_ids
        assert section2.id in question.knowledge_point_ids

    async def test_get_question_by_id(self, db_session: AsyncSession):
        """Golden path: get question by ID (with knowledge points loaded)"""
        _, _, section = await create_knowledge_chain(db_session)

        service = QuestionService()
        created = await service.create(db_session, QuestionCreate(
            type=QuestionType.SHORT_ANSWER,
            content="Explain photosynthesis",
            answer="Process by which plants convert light to energy",
            knowledge_point_ids=[section.id],
        ))

        found = await service.get(db_session, created.id)

        assert found is not None
        assert found.id == created.id
        assert found.content == "Explain photosynthesis"
        assert len(found.knowledge_points) == 1
        assert found.knowledge_points[0].id == section.id

    async def test_list_questions(self, db_session: AsyncSession):
        """Golden path: list questions"""
        service = QuestionService()
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q1", answer="A1",
        ))
        await service.create(db_session, QuestionCreate(
            type=QuestionType.MULTIPLE_CHOICE, content="Q2", answer="A2",
        ))

        questions = await service.get_list(db_session)

        assert len(questions) == 2

    async def test_list_questions_filtered_by_type(self, db_session: AsyncSession):
        """Golden path: list questions filtered by type"""
        service = QuestionService()
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q1", answer="A1",
        ))
        await service.create(db_session, QuestionCreate(
            type=QuestionType.MULTIPLE_CHOICE, content="Q2", answer="A2",
        ))

        questions = await service.get_list(db_session, type="single_choice")

        assert len(questions) == 1
        assert questions[0].type == QuestionType.SINGLE_CHOICE

    async def test_list_questions_filtered_by_difficulty(self, db_session: AsyncSession):
        """Golden path: list questions filtered by difficulty"""
        service = QuestionService()
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q1", answer="A1",
            difficulty=Difficulty.EASY,
        ))
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q2", answer="A2",
            difficulty=Difficulty.HARD,
        ))

        questions = await service.get_list(db_session, difficulty="hard")

        assert len(questions) == 1
        assert questions[0].difficulty == Difficulty.HARD

    async def test_list_questions_filtered_by_knowledge_point_id(self, db_session: AsyncSession):
        """Golden path: list questions filtered by knowledge_point_ids"""
        _, _, section = await create_knowledge_chain(db_session)

        service = QuestionService()
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q with KP", answer="A",
            knowledge_point_ids=[section.id],
        ))
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q without KP", answer="A",
        ))

        questions = await service.get_list(db_session, knowledge_point_ids=[section.id])

        assert len(questions) == 1
        assert questions[0].content == "Q with KP"

    async def test_list_questions_filtered_by_multiple_knowledge_point_ids(self, db_session: AsyncSession):
        """OR default + AND opt-in via match_all_kps"""
        _, _, section1 = await create_knowledge_chain(db_session)
        _, _, section2 = await create_knowledge_chain(db_session)
        _, _, section3 = await create_knowledge_chain(db_session)

        service = QuestionService()
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q with KP1+KP2", answer="A",
            knowledge_point_ids=[section1.id, section2.id],
        ))
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q with KP1 only", answer="A",
            knowledge_point_ids=[section1.id],
        ))
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q with KP3", answer="A",
            knowledge_point_ids=[section3.id],
        ))

        questions_all = await service.get_list(
            db_session,
            knowledge_point_ids=[section1.id, section2.id],
            match_all_kps=True,
        )
        assert len(questions_all) == 1
        assert questions_all[0].content == "Q with KP1+KP2"

        questions_any = await service.get_list(
            db_session,
            knowledge_point_ids=[section1.id, section2.id],
        )
        assert {q.content for q in questions_any} == {"Q with KP1+KP2", "Q with KP1 only"}

    async def test_list_questions_filtered_by_volume_id(self, db_session: AsyncSession):
        """Golden path: list questions under a specific volume"""
        volume, chapter, section = await create_knowledge_chain(db_session)
        _, _, other_section = await create_knowledge_chain(db_session)

        service = QuestionService()
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q in volume", answer="A",
            knowledge_point_ids=[section.id],
        ))
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q in other volume", answer="A",
            knowledge_point_ids=[other_section.id],
        ))

        questions = await service.get_list(db_session, volume_id=volume.id)

        assert len(questions) == 1
        assert questions[0].content == "Q in volume"

    async def test_list_questions_filtered_by_chapter_id(self, db_session: AsyncSession):
        """Golden path: list questions under a specific chapter"""
        volume, chapter, section = await create_knowledge_chain(db_session)
        other_chapter = await create_test_chapter(db_session, volume.id)
        other_section = await create_test_section(db_session, other_chapter.id)

        service = QuestionService()
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q in chapter", answer="A",
            knowledge_point_ids=[section.id],
        ))
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q in other chapter", answer="A",
            knowledge_point_ids=[other_section.id],
        ))

        questions = await service.get_list(db_session, chapter_id=chapter.id)

        assert len(questions) == 1
        assert questions[0].content == "Q in chapter"

    async def test_list_questions_filtered_by_chapter_and_knowledge_point(self, db_session: AsyncSession):
        """Golden path: list questions filtered by both chapter and knowledge point"""
        volume, chapter, section1 = await create_knowledge_chain(db_session)
        section2 = await create_test_section(db_session, chapter.id)

        service = QuestionService()
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q with KP1", answer="A",
            knowledge_point_ids=[section1.id],
        ))
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q with KP2", answer="A",
            knowledge_point_ids=[section2.id],
        ))
        await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q with KP1+KP2", answer="A",
            knowledge_point_ids=[section1.id, section2.id],
        ))

        questions = await service.get_list(db_session, chapter_id=chapter.id, knowledge_point_ids=[section1.id])

        assert len(questions) == 2

    async def test_update_question_fields(self, db_session: AsyncSession):
        """Golden path: update question fields"""
        service = QuestionService()
        created = await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Original", answer="A",
        ))

        updated = await service.update(db_session, created.id, QuestionUpdate(
            content="Updated content",
            answer="B",
            difficulty=Difficulty.HARD,
        ))

        assert updated is not None
        assert updated.content == "Updated content"
        assert updated.answer == "B"
        assert updated.difficulty == Difficulty.HARD

    async def test_update_question_knowledge_points(self, db_session: AsyncSession):
        """Golden path: update question knowledge points"""
        _, _, section1 = await create_knowledge_chain(db_session)
        _, _, section2 = await create_knowledge_chain(db_session)

        service = QuestionService()
        created = await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q", answer="A",
            knowledge_point_ids=[section1.id],
        ))
        assert section1.id in created.knowledge_point_ids

        updated = await service.update(db_session, created.id, QuestionUpdate(
            knowledge_point_ids=[section2.id],
        ))

        assert section1.id not in updated.knowledge_point_ids
        assert section2.id in updated.knowledge_point_ids

    async def test_delete_question(self, db_session: AsyncSession):
        """Golden path: delete question"""
        service = QuestionService()
        created = await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="To delete", answer="A",
        ))

        result = await service.delete(db_session, created.id)

        assert result is True
        found = await service.get(db_session, created.id)
        assert found is None

    async def test_create_question_default_difficulty(self, db_session: AsyncSession):
        """Edge case: create question with default difficulty (MEDIUM)"""
        service = QuestionService()
        question = await service.create(db_session, QuestionCreate(
            type=QuestionType.CALCULATION, content="Calculate", answer="42",
        ))

        assert question.difficulty == Difficulty.MEDIUM

    async def test_create_question_empty_knowledge_point_ids(self, db_session: AsyncSession):
        """Edge case: create question with empty knowledge_point_ids"""
        service = QuestionService()
        question = await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q", answer="A",
            knowledge_point_ids=[],
        ))

        assert question.knowledge_point_ids == []

    async def test_list_questions_with_pagination(self, db_session: AsyncSession):
        """Edge case: list questions with pagination (skip/limit)"""
        service = QuestionService()
        for i in range(5):
            await service.create(db_session, QuestionCreate(
                type=QuestionType.SINGLE_CHOICE, content=f"Q{i}", answer=f"A{i}",
            ))

        first_page = await service.get_list(db_session, skip=0, limit=2)
        assert len(first_page) == 2

        second_page = await service.get_list(db_session, skip=2, limit=2)
        assert len(second_page) == 2

        remainder = await service.get_list(db_session, skip=4, limit=10)
        assert len(remainder) == 1

    async def test_partial_update_only_change_type(self, db_session: AsyncSession):
        """Edge case: partial update (only change type)"""
        service = QuestionService()
        created = await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE,
            content="Original content",
            answer="Original answer",
            difficulty=Difficulty.EASY,
        ))

        updated = await service.update(db_session, created.id, QuestionUpdate(
            type=QuestionType.MULTIPLE_CHOICE,
        ))

        assert updated.type == QuestionType.MULTIPLE_CHOICE
        assert updated.content == "Original content"
        assert updated.answer == "Original answer"
        assert updated.difficulty == Difficulty.EASY

    async def test_update_knowledge_point_ids_to_empty(self, db_session: AsyncSession):
        """Edge case: update knowledge_point_ids to empty list (clear association)"""
        _, _, section = await create_knowledge_chain(db_session)

        service = QuestionService()
        created = await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Q", answer="A",
            knowledge_point_ids=[section.id],
        ))
        assert len(created.knowledge_point_ids) == 1

        updated = await service.update(db_session, created.id, QuestionUpdate(
            knowledge_point_ids=[],
        ))

        assert updated.knowledge_point_ids == []

    async def test_get_nonexistent_question(self, db_session: AsyncSession):
        """Error case: get non-existent question (returns None)"""
        service = QuestionService()
        found = await service.get(db_session, 99999)

        assert found is None

    async def test_update_nonexistent_question(self, db_session: AsyncSession):
        """Error case: update non-existent question (returns None)"""
        service = QuestionService()
        result = await service.update(db_session, 99999, QuestionUpdate(content="Nope"))

        assert result is None

    async def test_delete_nonexistent_question(self, db_session: AsyncSession):
        """Error case: delete non-existent question (returns False)"""
        service = QuestionService()
        result = await service.delete(db_session, 99999)

        assert result is False

    async def test_search_by_text_returns_sorted_by_similarity(self, db_session: AsyncSession):
        """Golden path: search returns questions sorted by similarity"""
        service = QuestionService()
        q1 = await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Close Q", answer="A",
        ))
        q1.embedding = make_basis_vector(index=0)
        q2 = await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Far Q", answer="A",
        ))
        q2.embedding = make_basis_vector(index=1)
        await db_session.flush()

        with patch("app.services.question.LLMClient") as MockLLM:
            mock_llm = MockLLM.return_value
            mock_llm.embed = AsyncMock(return_value=[make_basis_vector(index=0)])
            results = await service.search_by_text(db_session, "test query")

        assert len(results) == 2
        assert results[0][0].id == q1.id
        assert results[0][1] < results[1][1]

    async def test_search_by_text_with_threshold(self, db_session: AsyncSession):
        """Golden path: search with threshold filters out distant results"""
        service = QuestionService()
        q1 = await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Close Q", answer="A",
        ))
        q1.embedding = make_basis_vector(index=0)
        q2 = await service.create(db_session, QuestionCreate(
            type=QuestionType.SINGLE_CHOICE, content="Far Q", answer="A",
        ))
        q2.embedding = make_basis_vector(index=1)
        await db_session.flush()

        with patch("app.services.question.LLMClient") as MockLLM:
            mock_llm = MockLLM.return_value
            mock_llm.embed = AsyncMock(return_value=[make_basis_vector(index=0)])
            results = await service.search_by_text(db_session, "test query", threshold=0.5)

        assert len(results) == 1
        assert results[0][0].id == q1.id

    async def test_search_by_text_empty_when_no_embeddings(self, db_session: AsyncSession):
        """Edge case: search returns empty when no questions have embeddings"""
        service = QuestionService()
        with patch("app.services.question.LLMClient") as MockLLM:
            mock_llm = MockLLM.return_value
            mock_llm.embed = AsyncMock(side_effect=Exception("no key"))
            await service.create(db_session, QuestionCreate(
                type=QuestionType.SINGLE_CHOICE, content="No embedding Q", answer="A",
            ))

            mock_llm.embed = AsyncMock(return_value=[make_vector(fill=0.5)])
            results = await service.search_by_text(db_session, "test query")

        assert results == []

    async def test_search_by_text_ignores_questions_without_embeddings(self, db_session: AsyncSession):
        """Edge case: search ignores questions without embeddings"""
        service = QuestionService()
        with patch("app.services.question.LLMClient") as MockLLM:
            mock_llm = MockLLM.return_value
            mock_llm.embed = AsyncMock(side_effect=Exception("no key"))
            q_with = await service.create(db_session, QuestionCreate(
                type=QuestionType.SINGLE_CHOICE, content="Has embedding", answer="A",
            ))
            q_with.embedding = make_vector(fill=0.5)
            await service.create(db_session, QuestionCreate(
                type=QuestionType.SINGLE_CHOICE, content="No embedding", answer="A",
            ))
            await db_session.flush()

            mock_llm.embed = AsyncMock(return_value=[make_vector(fill=0.5)])
            results = await service.search_by_text(db_session, "test query")

        assert len(results) == 1
        assert results[0][0].id == q_with.id

    async def test_search_by_text_with_limit(self, db_session: AsyncSession):
        """Edge case: search respects limit parameter"""
        service = QuestionService()
        for i in range(5):
            q = await service.create(db_session, QuestionCreate(
                type=QuestionType.SINGLE_CHOICE, content=f"Q{i}", answer="A",
            ))
            q.embedding = make_vector(fill=0.5)
        await db_session.flush()

        with patch("app.services.question.LLMClient") as MockLLM:
            mock_llm = MockLLM.return_value
            mock_llm.embed = AsyncMock(return_value=[make_vector(fill=0.5)])
            results = await service.search_by_text(db_session, "test query", limit=3)

        assert len(results) == 3

    async def test_search_by_text_empty_query(self, db_session: AsyncSession):
        """Edge case: empty query returns empty results immediately"""
        service = QuestionService()
        results = await service.search_by_text(db_session, "")
        assert results == []

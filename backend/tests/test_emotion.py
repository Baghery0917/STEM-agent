import base64
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.external.emotion import (
    EmotionCategory,
    EmotionClient,
    EmotionResult,
    describe_value,
    value_to_category,
)
from app.services.emotion import (
    _CATEGORY_RE,
    EmotionService,
    InstantEmotion,
    _decode_frame,
)


class TestInstantEmotion:
    def test_value_weights_facial_and_text(self):
        assert InstantEmotion(facial=4.0, text=3.0).value == pytest.approx(3.6)
        assert InstantEmotion(facial=1.0, text=5.0).value == pytest.approx(2.6)

    def test_value_uses_single_source_when_other_missing(self):
        assert InstantEmotion(facial=4.0, text=None).value == 4.0
        assert InstantEmotion(facial=None, text=2.0).value == 2.0

    def test_value_none_when_both_missing(self):
        assert InstantEmotion(facial=None, text=None).value is None

    def test_describe_both_sources(self):
        assert InstantEmotion(facial=4.0, text=3.0).describe() == "受挫（面部 4，文本 3）"

    def test_describe_single_source(self):
        assert InstantEmotion(facial=None, text=1.0).describe() == "自信（文本 1）"
        assert InstantEmotion(facial=5.0, text=None).describe() == "非常受挫（面部 5）"

    def test_describe_none_when_no_value(self):
        assert InstantEmotion(facial=None, text=None).describe() is None


class TestValueMapping:
    @pytest.mark.parametrize(
        ("value", "category"),
        [
            (1.0, EmotionCategory.CONFIDENT),
            (1.49, EmotionCategory.CONFIDENT),
            (1.51, EmotionCategory.SLIGHTLY_UNCERTAIN),
            (2.5, EmotionCategory.SLIGHTLY_UNCERTAIN),
            (2.51, EmotionCategory.DISCOURAGED),
            (3.4, EmotionCategory.DISCOURAGED),
            (3.6, EmotionCategory.FRUSTRATED),
            (4.49, EmotionCategory.FRUSTRATED),
            (4.51, EmotionCategory.VERY_FRUSTRATED),
            (5.0, EmotionCategory.VERY_FRUSTRATED),
        ],
    )
    def test_value_to_category_boundaries(self, value, category):
        assert value_to_category(value) is category

    def test_value_to_category_clamps_out_of_range(self):
        assert value_to_category(0.0) is EmotionCategory.CONFIDENT
        assert value_to_category(-3.0) is EmotionCategory.CONFIDENT
        assert value_to_category(9.0) is EmotionCategory.VERY_FRUSTRATED

    def test_describe_value_labels(self):
        assert describe_value(1.0) == "自信"
        assert describe_value(2.0) == "略犹豫"
        assert describe_value(3.0) == "气馁"
        assert describe_value(4.0) == "受挫"
        assert describe_value(5.0) == "非常受挫"

    def test_emotion_result_value(self):
        assert EmotionResult(EmotionCategory.DISCOURAGED, 0.8).value == 3.0


class TestCategoryRegex:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("confident", "confident"),
            ("  Frustrated\n", "Frustrated"),
            ("very_frustrated", "very_frustrated"),
            ("The answer is: slightly_uncertain.", "slightly_uncertain"),
            ("discouraged", "discouraged"),
        ],
    )
    def test_matches_category_tokens(self, text, expected):
        match = _CATEGORY_RE.search(text)
        assert match is not None
        assert match.group(0) == expected

    def test_very_frustrated_wins_over_frustrated(self):
        # alternation order matters: "frustrated" alone would match inside "very_frustrated"
        assert _CATEGORY_RE.search("VERY_FRUSTRATED").group(0).lower() == "very_frustrated"

    def test_no_match_for_garbage(self):
        assert _CATEGORY_RE.search("I cannot classify this") is None
        assert _CATEGORY_RE.search("") is None


class TestDecodeFrame:
    def test_bare_base64(self):
        raw = b"\xff\xd8\xff\xe0jpeg"
        assert _decode_frame(base64.b64encode(raw).decode()) == raw

    def test_data_url(self):
        raw = b"hello frame"
        encoded = base64.b64encode(raw).decode()
        assert _decode_frame(f"data:image/jpeg;base64,{encoded}") == raw

    def test_data_url_without_comma_separator_raises(self):
        with pytest.raises(IndexError):
            _decode_frame("data:image/jpeg;base64")


def _service(chat: AsyncMock, facial_configured: bool = False) -> EmotionService:
    llm = MagicMock()
    llm.chat = chat
    facial = MagicMock(spec=EmotionClient)
    facial.is_configured.return_value = facial_configured
    facial.recognize = AsyncMock(
        return_value=EmotionResult(EmotionCategory.FRUSTRATED, 0.9),
    )
    return EmotionService(llm=llm, facial=facial)


class TestDetectText:
    async def test_maps_category_to_value(self):
        service = _service(AsyncMock(return_value="frustrated"))
        assert await service._detect_text("我做不出来", student_id=1, session_id=7) == 4.0

        kwargs = service.llm.chat.await_args.kwargs
        assert kwargs["temperature"] == 0.0
        assert kwargs["context"] == {"student_id": 1, "teaching_session_id": 7}
        assert "我做不出来" in service.llm.chat.await_args.args[0][0]["content"]

    async def test_garbage_response_returns_none(self):
        service = _service(AsyncMock(return_value="I'm not sure what you mean"))
        assert await service._detect_text("hi", student_id=1, session_id=None) is None

    async def test_empty_response_returns_none(self):
        service = _service(AsyncMock(return_value=None))
        assert await service._detect_text("hi", student_id=1, session_id=None) is None

    async def test_llm_exception_returns_none(self):
        service = _service(AsyncMock(side_effect=RuntimeError("llm down")))
        assert await service._detect_text("hi", student_id=1, session_id=None) is None

    async def test_blank_text_skips_llm(self):
        service = _service(AsyncMock(return_value="confident"))
        assert await service._detect_text("   \n", student_id=1, session_id=None) is None
        service.llm.chat.assert_not_awaited()


class TestDetectFacial:
    async def test_skipped_when_client_not_configured(self):
        service = _service(AsyncMock(), facial_configured=False)
        frame = base64.b64encode(b"img").decode()
        assert await service._detect_facial(frame, student_id=1) is None
        service.facial.recognize.assert_not_awaited()

    async def test_skipped_when_no_frame(self):
        service = _service(AsyncMock(), facial_configured=True)
        assert await service._detect_facial(None, student_id=1) is None
        assert await service._detect_facial("", student_id=1) is None
        service.facial.recognize.assert_not_awaited()

    async def test_returns_value_when_configured(self):
        service = _service(AsyncMock(), facial_configured=True)
        raw = b"img"
        frame = f"data:image/jpeg;base64,{base64.b64encode(raw).decode()}"
        assert await service._detect_facial(frame, student_id=3) == 4.0
        service.facial.recognize.assert_awaited_once_with(raw, student_id=3)

    async def test_recognize_failure_returns_none(self):
        service = _service(AsyncMock(), facial_configured=True)
        service.facial.recognize = AsyncMock(side_effect=RuntimeError("http 500"))
        frame = base64.b64encode(b"img").decode()
        assert await service._detect_facial(frame, student_id=1) is None

    async def test_invalid_base64_returns_none(self):
        service = _service(AsyncMock(), facial_configured=True)
        assert await service._detect_facial("not base64!!", student_id=1) is None
        service.facial.recognize.assert_not_awaited()


class TestDetectInstant:
    async def test_combines_text_and_facial(self):
        service = _service(AsyncMock(return_value="discouraged"), facial_configured=True)
        frame = base64.b64encode(b"img").decode()
        instant = await service.detect_instant("ugh", frame, student_id=1, session_id=2)
        assert instant.facial == 4.0
        assert instant.text == 3.0
        assert instant.value == pytest.approx(3.6)

    async def test_text_only_without_frame(self):
        service = _service(AsyncMock(return_value="confident"), facial_configured=True)
        instant = await service.detect_instant("got it", None, student_id=1)
        assert instant.facial is None
        assert instant.text == 1.0
        assert instant.value == 1.0

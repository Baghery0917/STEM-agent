from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.llm.client import LLMClient
from app.models.llm_call_log import LLMCallLog, LLMCallStatus, LLMCallType


@pytest.fixture
def patch_session_maker(db_session: AsyncSession, monkeypatch):
    # _record_log 用独立 session 写入 async_session_maker 指向的库（默认是主库），
    # 这里改指向测试库 engine，才能在 db_session 里查到写入的日志行。
    test_maker = async_sessionmaker(
        db_session.bind, class_=AsyncSession, expire_on_commit=False
    )
    monkeypatch.setattr("app.llm.client.async_session_maker", test_maker)


async def _fetch_latest_log(db_session: AsyncSession) -> LLMCallLog:
    await db_session.commit()
    db_session.expire_all()
    result = await db_session.execute(
        select(LLMCallLog).order_by(LLMCallLog.id.desc()).limit(1)
    )
    row = result.scalar_one_or_none()
    assert row is not None, "expected a LLMCallLog row to be written"
    return row


@pytest.mark.asyncio
async def test_embed_logs_success(db_session: AsyncSession, patch_session_maker):
    fake_response = SimpleNamespace(
        data=[
            SimpleNamespace(embedding=[0.1, 0.2, 0.3]),
            SimpleNamespace(embedding=[0.4, 0.5, 0.6]),
        ],
        usage=None,
    )
    client = LLMClient()
    client._embed_raw = AsyncMock(return_value=fake_response)

    vectors = await client.embed(["a", "b"])

    assert vectors == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    log = await _fetch_latest_log(db_session)
    assert log.call_type == LLMCallType.EMBED
    assert log.status == LLMCallStatus.SUCCESS
    assert log.request_payload == {"input": ["a", "b"]}
    assert log.response_text is None
    assert log.response_meta["n_vectors"] == 2
    assert log.response_meta["dim"] == 3
    assert log.duration_ms >= 0
    assert log.error is None


@pytest.mark.asyncio
async def test_chat_logs_success(db_session: AsyncSession, patch_session_maker):
    fake_usage = SimpleNamespace(model_dump=lambda: {"total_tokens": 5})
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))],
        usage=fake_usage,
    )
    client = LLMClient()
    client._chat_raw = AsyncMock(return_value=fake_response)

    content = await client.chat([{"role": "user", "content": "hi"}])

    assert content == "hello"

    log = await _fetch_latest_log(db_session)
    assert log.call_type == LLMCallType.CHAT
    assert log.status == LLMCallStatus.SUCCESS
    assert log.response_text == "hello"
    assert log.response_meta == {"total_tokens": 5}
    assert log.error is None
    assert log.duration_ms >= 0


@pytest.mark.asyncio
async def test_chat_logs_error(db_session: AsyncSession, patch_session_maker):
    client = LLMClient()
    client._chat_raw = AsyncMock(side_effect=ValueError("boom"))

    with pytest.raises(ValueError):
        await client.chat([{"role": "user", "content": "hi"}])

    log = await _fetch_latest_log(db_session)
    assert log.call_type == LLMCallType.CHAT
    assert log.status == LLMCallStatus.ERROR
    assert log.response_text is None
    assert log.response_meta is None
    assert "ValueError" in log.error
    assert "boom" in log.error
    assert log.duration_ms >= 0


def _make_chunk(content=None, usage=None):
    delta = SimpleNamespace(content=content)
    choice = SimpleNamespace(delta=delta)
    return SimpleNamespace(
        choices=[choice] if content is not None else [],
        usage=SimpleNamespace(model_dump=lambda: usage) if usage else None,
    )


class _FakeStream:
    def __init__(self, chunks):
        self._chunks = chunks

    def __aiter__(self):
        async def gen():
            for c in self._chunks:
                yield c
        return gen()


@pytest.mark.asyncio
async def test_chat_stream_logs_success(db_session: AsyncSession, patch_session_maker):
    chunks = [
        _make_chunk("hel"),
        _make_chunk("lo "),
        _make_chunk("world"),
        _make_chunk(usage={"total_tokens": 7}),
    ]
    client = LLMClient()
    client._client.chat.completions.create = AsyncMock(
        return_value=_FakeStream(chunks)
    )

    acc = []
    async for delta in client.chat_stream([{"role": "user", "content": "hi"}]):
        acc.append(delta)

    assert "".join(acc) == "hello world"

    log = await _fetch_latest_log(db_session)
    assert log.call_type == LLMCallType.CHAT
    assert log.status == LLMCallStatus.SUCCESS
    assert log.response_text == "hello world"
    assert log.response_meta == {"total_tokens": 7}
    assert log.request_params.get("stream") is True
    assert log.error is None
    assert log.duration_ms >= 0

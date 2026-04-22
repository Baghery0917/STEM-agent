import logging
import time
from typing import Any, AsyncIterator

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import AsyncOpenAI, APIError, RateLimitError

from app.config import settings
from app.database import async_session_maker
from app.models.llm_call_log import LLMCallLog, LLMCallStatus, LLMCallType

logger = logging.getLogger(__name__)


_SENSITIVE_PARAM_KEYS = {"api_key", "apikey", "authorization"}


def _sanitize_params(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if k.lower() not in _SENSITIVE_PARAM_KEYS}


class LLMClient:
    def __init__(self):
        self._client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )

    async def chat(
        self,
        messages: list[dict],
        *,
        context: dict | None = None,
        **kwargs,
    ) -> str:
        model = kwargs.get("model", settings.llm_model)
        payload = {"messages": messages}
        params = _sanitize_params(kwargs)
        started = time.perf_counter()
        response = None
        error: Exception | None = None
        try:
            response = await self._chat_raw(messages, **kwargs)
            return response.choices[0].message.content
        except Exception as exc:
            error = exc
            raise
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            await self._record_log(
                call_type=LLMCallType.CHAT,
                model=model,
                payload=payload,
                params=params,
                response=response,
                response_text_from_chat=True,
                error=error,
                duration_ms=duration_ms,
                context=context,
            )

    async def vision(
        self,
        image_url: str,
        prompt: str = "请将图片中的数学公式转换为LaTeX格式",
        *,
        context: dict | None = None,
        **kwargs,
    ) -> str:
        model = kwargs.get("model", settings.llm_vision_model)
        payload = {"image_url": image_url, "prompt": prompt}
        params = _sanitize_params(kwargs)
        started = time.perf_counter()
        response = None
        error: Exception | None = None
        try:
            response = await self._vision_raw(image_url, prompt, **kwargs)
            return response.choices[0].message.content
        except Exception as exc:
            error = exc
            raise
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            await self._record_log(
                call_type=LLMCallType.VISION,
                model=model,
                payload=payload,
                params=params,
                response=response,
                response_text_from_chat=True,
                error=error,
                duration_ms=duration_ms,
                context=context,
            )

    async def embed(
        self,
        texts: list[str],
        *,
        context: dict | None = None,
    ) -> list[list[float]]:
        if not texts:
            return []
        model = settings.llm_embedding_model
        payload = {"input": list(texts)}
        started = time.perf_counter()
        response = None
        error: Exception | None = None
        try:
            response = await self._embed_raw(texts)
            return [item.embedding for item in response.data]
        except Exception as exc:
            error = exc
            raise
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            await self._record_log(
                call_type=LLMCallType.EMBED,
                model=model,
                payload=payload,
                params={},
                response=response,
                response_text_from_chat=False,
                error=error,
                duration_ms=duration_ms,
                context=context,
            )

    async def chat_stream(
        self,
        messages: list[dict],
        *,
        context: dict | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        model = kwargs.get("model", settings.llm_model)
        payload = {"messages": messages}
        params = _sanitize_params({**kwargs, "stream": True})
        started = time.perf_counter()
        acc_parts: list[str] = []
        usage_meta: dict | None = None
        error: Exception | None = None

        try:
            stream = await self._client.chat.completions.create(
                model=kwargs.pop("model", settings.llm_model),
                messages=messages,
                stream=True,
                stream_options={"include_usage": True},
                **kwargs,
            )
            async for chunk in stream:
                usage = getattr(chunk, "usage", None)
                if usage is not None and hasattr(usage, "model_dump"):
                    usage_meta = usage.model_dump()
                for choice in getattr(chunk, "choices", []) or []:
                    delta_obj = getattr(choice, "delta", None)
                    delta_text = getattr(delta_obj, "content", None) if delta_obj else None
                    if delta_text:
                        acc_parts.append(delta_text)
                        yield delta_text
        except Exception as exc:
            error = exc
            raise
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            full_text = "".join(acc_parts) if acc_parts else None
            await self._write_log(
                call_type=LLMCallType.CHAT,
                model=model,
                payload=payload,
                params=params,
                response_text=full_text,
                response_meta=usage_meta,
                error=error,
                duration_ms=duration_ms,
                context=context,
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((RateLimitError, APIError)),
    )
    async def _chat_raw(self, messages: list[dict], **kwargs):
        return await self._client.chat.completions.create(
            model=kwargs.pop("model", settings.llm_model),
            messages=messages,
            **kwargs,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((RateLimitError, APIError)),
    )
    async def _vision_raw(self, image_url: str, prompt: str, **kwargs):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]
        return await self._client.chat.completions.create(
            model=kwargs.pop("model", settings.llm_vision_model),
            messages=messages,
            **kwargs,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((RateLimitError, APIError)),
    )
    async def _embed_raw(self, texts: list[str]):
        return await self._client.embeddings.create(
            model=settings.llm_embedding_model,
            input=texts,
        )

    async def _record_log(
        self,
        *,
        call_type: LLMCallType,
        model: str,
        payload: dict,
        params: dict,
        response: Any,
        response_text_from_chat: bool,
        error: Exception | None,
        duration_ms: int,
        context: dict | None,
    ) -> None:
        if error is not None:
            response_text = None
            response_meta = None
        elif response_text_from_chat:
            response_text = response.choices[0].message.content
            usage = getattr(response, "usage", None)
            response_meta = (
                usage.model_dump() if usage is not None and hasattr(usage, "model_dump") else None
            )
        else:
            vectors = [item.embedding for item in response.data]
            response_text = None
            response_meta = {
                "n_vectors": len(vectors),
                "dim": len(vectors[0]) if vectors else 0,
            }
            usage = getattr(response, "usage", None)
            if usage is not None and hasattr(usage, "model_dump"):
                response_meta["usage"] = usage.model_dump()
        await self._write_log(
            call_type=call_type,
            model=model,
            payload=payload,
            params=params,
            response_text=response_text,
            response_meta=response_meta,
            error=error,
            duration_ms=duration_ms,
            context=context,
        )

    async def _write_log(
        self,
        *,
        call_type: LLMCallType,
        model: str,
        payload: dict,
        params: dict,
        response_text: str | None,
        response_meta: dict | None,
        error: Exception | None,
        duration_ms: int,
        context: dict | None,
    ) -> None:
        try:
            if error is not None:
                status = LLMCallStatus.ERROR
                err_text = f"{type(error).__name__}: {error}"
            else:
                status = LLMCallStatus.SUCCESS
                err_text = None

            ctx = context or {}
            log = LLMCallLog(
                call_type=call_type,
                model=model,
                base_url=settings.llm_base_url,
                request_payload=payload,
                request_params=params,
                response_text=response_text,
                response_meta=response_meta,
                status=status,
                error=err_text,
                duration_ms=duration_ms,
                teaching_session_id=ctx.get("teaching_session_id"),
                student_id=ctx.get("student_id"),
            )
            async with async_session_maker() as session:
                session.add(log)
                await session.commit()
        except Exception as log_exc:
            logger.warning("failed to record LLM call log: %s", log_exc)

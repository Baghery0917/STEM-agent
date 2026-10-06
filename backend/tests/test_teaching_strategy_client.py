import json
from types import SimpleNamespace

import pytest

from app.external.teaching_strategy import StrategyResult, TeachingStrategyClient


def _text(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def _result(content=(), structured_content=None, is_error=False) -> SimpleNamespace:
    return SimpleNamespace(
        content=list(content),
        structured_content=structured_content,
        is_error=is_error,
    )


class TestParse:
    def test_structured_content_preferred(self):
        result = _result(
            content=[_text("ignored")],
            structured_content={"strategy": " Socratic ", "reason": " Engaged "},
        )
        parsed = TeachingStrategyClient._parse(result)
        assert isinstance(parsed, StrategyResult)
        assert parsed.strategy == "Socratic"
        assert parsed.reason == "Engaged"

    def test_structured_content_without_reason_uses_default(self):
        parsed = TeachingStrategyClient._parse(_result(structured_content={"strategy": "Scaffold"}))
        assert parsed.strategy == "Scaffold"
        assert parsed.reason == "From strategy service"

    def test_text_json_content(self):
        payload = json.dumps({"strategy": "Worked example", "reason": "Cold start"})
        parsed = TeachingStrategyClient._parse(_result(content=[_text(payload)]))
        assert parsed.strategy == "Worked example"
        assert parsed.reason == "Cold start"

    def test_plain_text_content_becomes_strategy(self):
        parsed = TeachingStrategyClient._parse(_result(content=[_text("Guided inquiry")]))
        assert parsed.strategy == "Guided inquiry"
        assert parsed.reason == "From strategy service"

    def test_skips_non_text_content_blocks(self):
        result = _result(content=[
            SimpleNamespace(type="image", data="..."),
            _text("Peer discussion"),
        ])
        assert TeachingStrategyClient._parse(result).strategy == "Peer discussion"

    def test_empty_structured_content_falls_back_to_text(self):
        result = _result(content=[_text("Fallback text")], structured_content={})
        assert TeachingStrategyClient._parse(result).strategy == "Fallback text"

    def test_is_error_raises(self):
        with pytest.raises(RuntimeError, match="MCP tool error"):
            TeachingStrategyClient._parse(_result(content=[_text("boom")], is_error=True))

    def test_no_content_raises(self):
        with pytest.raises(RuntimeError, match="no content"):
            TeachingStrategyClient._parse(_result(content=[]))

    @pytest.mark.parametrize(
        "result",
        [
            _result(structured_content={"strategy": "   "}),
            _result(content=[_text(json.dumps({"strategy": ""}))]),
            _result(content=[_text(json.dumps({"reason": "no strategy key"}))]),
            _result(content=[_text("   ")]),
        ],
    )
    def test_empty_strategy_raises(self, result):
        with pytest.raises(RuntimeError, match="empty strategy"):
            TeachingStrategyClient._parse(result)


class TestConfiguration:
    def test_is_configured_follows_url(self, monkeypatch):
        from app.config import settings

        monkeypatch.setattr(settings, "teaching_strategy_mcp_url", "")
        assert TeachingStrategyClient().is_configured() is False

        monkeypatch.setattr(settings, "teaching_strategy_mcp_url", "http://mcp.local/mcp")
        assert TeachingStrategyClient().is_configured() is True

    async def test_get_strategy_unconfigured_raises(self, monkeypatch):
        from app.config import settings

        monkeypatch.setattr(settings, "teaching_strategy_mcp_url", "")
        with pytest.raises(ValueError, match="not configured"):
            await TeachingStrategyClient().get_strategy(1, 2, "hi")

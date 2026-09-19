"""AI servislari va System Prompt testlari."""

from __future__ import annotations

from typing import ClassVar

import pytest

from config import AIProvider, Settings, settings
from database.models import ChatMessage
from services.ai_client import create_ai_client
from services.claude_service import ClaudeService
from services.prompts import build_system_prompt


@pytest.mark.parametrize(
    ("lang", "kutilgan"),
    [
        ("uz", "O'ZBEK"),
        ("ru", "РУССКОМ"),
        ("en", "ENGLISH"),
    ],
)
def test_system_prompt_javob_tilini_buyuradi(lang, kutilgan):
    prompt = build_system_prompt(settings, lang)
    assert kutilgan in prompt


def test_system_prompt_kompaniya_malumotini_oz_ichiga_oladi():
    prompt = build_system_prompt(settings, "uz")
    assert settings.company_name in prompt
    assert settings.bot_persona_name in prompt
    assert "Amir Temur 15" in prompt


async def test_factory_sukut_boyicha_claude_qaytaradi():
    client = create_ai_client(settings)
    assert isinstance(client, ClaudeService)
    await client.close()


async def test_factory_openai_ni_ham_qaytara_oladi():
    openai_settings = settings.model_copy(update={"ai_provider": AIProvider.OPENAI})
    client = create_ai_client(openai_settings)
    assert type(client).__name__ == "OpenAIService"
    await client.close()


def test_sukutdagi_model_haiku():
    """Sukutdagi model arzon va tez bo'lishi kerak."""
    default = Settings(bot_token="x", anthropic_api_key="k")
    assert default.anthropic_model == "claude-haiku-4-5"


async def test_haiku_uchun_effort_yuborilmaydi():
    """Haiku modellari `output_config.effort` ni rad etadi (API 400 qaytaradi),
    shuning uchun sukutdagi modelda bu parametr umuman yuborilmasligi kerak."""
    haiku = settings.model_copy(update={"anthropic_model": "claude-haiku-4-5"})
    service = ClaudeService(haiku)
    assert service._supports_effort is False
    await service.close()


async def test_opus_uchun_effort_yuboriladi():
    opus = settings.model_copy(update={"anthropic_model": "claude-opus-5"})
    service = ClaudeService(opus)
    assert service._supports_effort is True
    await service.close()


def test_kalitsiz_provayder_xato_beradi():
    bad = Settings(
        bot_token="x",
        ai_provider=AIProvider.ANTHROPIC,
        anthropic_api_key=None,
    )
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        bad.validate_provider_keys()


def test_notogri_effort_qiymati_rad_etiladi():
    with pytest.raises(ValueError, match="AI_EFFORT"):
        Settings(bot_token="x", anthropic_api_key="k", ai_effort="turbo")


@pytest.mark.parametrize(
    ("raw", "kutilgan"),
    [
        ("111,222", {111, 222}),
        ("111 222", {111, 222}),
        ("", set()),
        ("notogri", set()),
    ],
)
def test_admin_id_tahlili(raw, kutilgan):
    assert Settings(bot_token="x", anthropic_api_key="k", admin_id=raw).admin_ids == kutilgan


class _FakeBlock:
    type = "text"
    text = "Javob."


class _FakeResponse:
    """Anthropic javobiga o'xshash minimal obyekt."""

    stop_reason = "end_turn"
    content: ClassVar[list] = [_FakeBlock()]


async def _capture_request(service: ClaudeService) -> dict:
    """ClaudeService API ga aynan qanday parametrlar yuborishini ushlaydi."""
    yuborilgan: dict = {}

    async def fake_create(**kwargs):
        yuborilgan.update(kwargs)
        return _FakeResponse()

    service._client.messages.create = fake_create  # type: ignore[method-assign]
    await service.ask("system prompt", [ChatMessage(role="user", content="savol")])
    return yuborilgan


async def test_haiku_sorovida_output_config_yoq():
    """Haiku ga `output_config` yuborilsa API 400 qaytaradi, shuning uchun
    u so'rovga umuman qo'shilmasligi kerak."""
    haiku = settings.model_copy(update={"anthropic_model": "claude-haiku-4-5"})
    service = ClaudeService(haiku)
    try:
        yuborilgan = await _capture_request(service)
        assert "output_config" not in yuborilgan, "Haiku ga effort yuborildi"
        assert yuborilgan["model"] == "claude-haiku-4-5"
        assert yuborilgan["system"] == "system prompt"
    finally:
        await service.close()


async def test_opus_sorovida_output_config_bor():
    opus = settings.model_copy(update={"anthropic_model": "claude-opus-5", "ai_effort": "low"})
    service = ClaudeService(opus)
    try:
        yuborilgan = await _capture_request(service)
        assert yuborilgan["output_config"] == {"effort": "low"}
    finally:
        await service.close()

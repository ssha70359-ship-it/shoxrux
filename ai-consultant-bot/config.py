"""Loyiha sozlamalari.

Barcha maxfiy ma'lumotlar (token, API kalit, admin ID) `.env` faylidan
o'qiladi — kodga hech qachon qattiq yozilmaydi. `pydantic-settings`
qiymatlarni o'qiydi va turini tekshiradi, xato bo'lsa bot ishga tushmaydi.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Loyihaning ildiz papkasi (config.py shu yerda joylashgan)
BASE_DIR = Path(__file__).resolve().parent


class AIProvider(StrEnum):
    """Qo'llab-quvvatlanadigan AI provayderlar."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class Language(StrEnum):
    """Bot qo'llab-quvvatlaydigan tillar."""

    UZ = "uz"
    RU = "ru"
    EN = "en"


class Settings(BaseSettings):
    """`.env` faylidan o'qiladigan sozlamalar."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # .env dagi notanish kalitlarni e'tiborsiz qoldiramiz
    )

    # --- Telegram ---
    bot_token: str
    # Bir nechta admin bo'lishi mumkin: ADMIN_ID=111,222,333
    admin_id: str = ""

    # --- AI provayder ---
    ai_provider: AIProvider = AIProvider.ANTHROPIC

    # Anthropic (asosiy)
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-haiku-4-5"
    # Javob chuqurligi: low | medium | high | xhigh | max.
    # DIQQAT 1: sukutdagi model — Haiku, u `effort` ni QO'LLAB-QUVVATLAMAYDI,
    #   shuning uchun bu sozlama e'tiborsiz qoldiriladi (claude_service.py ga
    #   qarang). U faqat Opus yoki Sonnet modeliga o'tganingizda ishlaydi.
    # DIQQAT 2: o'zgaruvchi ataylab AI_EFFORT deb nomlangan. CLAUDE_* prefiksi
    #   Claude Code kabi vositalarning muhit o'zgaruvchilari bilan to'qnashadi,
    #   haqiqiy env o'zgaruvchi esa .env faylidan ustun turadi.
    ai_effort: str = "low"

    # OpenAI (muqobil)
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    ai_max_tokens: int = Field(default=1024, ge=64, le=8192)

    # --- Kompaniya ma'lumotlari (System Prompt uchun) ---
    company_name: str = "Kompaniya"
    company_field: str = "xizmat ko'rsatish"
    company_info: str = ""
    bot_persona_name: str = "Konsultant"

    # --- Operator bilan bog'lanish (menyudagi havolali tugma uchun) ---
    operator_username: str | None = None  # masalan: @sunrise_manager
    operator_phone: str | None = None  # masalan: +998901234567

    # --- Til ---
    default_language: Language = Language.UZ

    # --- Suhbat xotirasi: kontekstga olinadigan oxirgi xabarlar soni ---
    history_limit: int = Field(default=10, ge=2, le=50)

    # --- Ma'lumotlar bazasi ---
    db_path: Path = Path("data/bot.db")

    # --- Anti-spam: bir foydalanuvchidan harakatlar orasidagi minimal vaqt ---
    throttle_rate: float = Field(default=1.0, ge=0.0)

    # --- Ommaviy xabar (broadcast) tezligi: sekundiga nechta xabar ---
    # Telegram limiti ~30/sek; xavfsizlik uchun 20 dan oshirmaslik tavsiya etiladi.
    broadcast_rate: int = Field(default=20, ge=1, le=30)

    # --- Loglash ---
    log_level: str = "INFO"

    @field_validator("ai_effort")
    @classmethod
    def _check_effort(cls, value: str) -> str:
        allowed = {"low", "medium", "high", "xhigh", "max"}
        if value not in allowed:
            raise ValueError(f"AI_EFFORT quyidagilardan biri bo'lishi kerak: {sorted(allowed)}")
        return value

    @property
    def admin_ids(self) -> set[int]:
        """ADMIN_ID satrini butun sonlar to'plamiga aylantiradi.

        "111,222" yoki "111 222" — ikkala format ham qo'llab-quvvatlanadi.
        """
        raw = self.admin_id.replace(",", " ").split()
        return {int(item) for item in raw if item.lstrip("-").isdigit()}

    @property
    def db_file(self) -> Path:
        """DB fayl uchun to'liq (absolyut) yo'l."""
        path = self.db_path
        return path if path.is_absolute() else BASE_DIR / path

    def validate_provider_keys(self) -> None:
        """Tanlangan provayderga mos API kalit borligini tekshiradi."""
        if self.ai_provider is AIProvider.ANTHROPIC and not self.anthropic_api_key:
            raise ValueError("AI_PROVIDER=anthropic tanlandi, lekin ANTHROPIC_API_KEY berilmagan.")
        if self.ai_provider is AIProvider.OPENAI and not self.openai_api_key:
            raise ValueError("AI_PROVIDER=openai tanlandi, lekin OPENAI_API_KEY berilmagan.")


# Butun loyiha bo'ylab ishlatiladigan yagona sozlamalar obyekti
settings = Settings()  # type: ignore[call-arg]

"""Testlar uchun umumiy sozlamalar va fixture'lar.

DIQQAT: `config.settings` — modul yuklanganda bir marta yaratiladigan
obyekt. Shuning uchun muhit o'zgaruvchilari loyiha modullari import
qilinishidan OLDIN o'rnatilishi shart. `conftest.py` pytest tomonidan
test fayllaridan oldin yuklanadi, ya'ni bu yer to'g'ri joy.
"""

from __future__ import annotations

import os

# --- Test muhiti (import'lardan oldin!) ---------------------------------
# Haqiqiy muhit o'zgaruvchilari `.env` faylidan ustun turadi, shuning uchun
# testlar ishlab turgan mashinadagi `.env` ga bog'liq bo'lmaydi.
os.environ.update(
    {
        "BOT_TOKEN": "123456789:AAHtestTokenForPytestOnly_xxxxxxxxxxxxx",
        "ADMIN_ID": "555,999",
        "AI_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "sk-ant-test",
        "ANTHROPIC_MODEL": "claude-haiku-4-5",
        "AI_EFFORT": "low",
        "OPENAI_API_KEY": "sk-test",
        "COMPANY_NAME": "Sunrise Digital",
        "COMPANY_FIELD": "veb-sayt va mobil ilova ishlab chiqish",
        "COMPANY_INFO": "Ish vaqti: Du-Sha 09:00-18:00. Toshkent, Amir Temur 15.",
        "BOT_PERSONA_NAME": "Aziza",
        "OPERATOR_USERNAME": "@sunrise_manager",
        "OPERATOR_PHONE": "+998901234567",
        "DEFAULT_LANGUAGE": "uz",
        "HISTORY_LIMIT": "10",
        "THROTTLE_RATE": "0",
        "BROADCAST_RATE": "30",
        "LOG_LEVEL": "WARNING",
    }
)

import datetime

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import TelegramMethod
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from config import settings
from database.db import Database
from database.models import ChatMessage
from database.repository import Repository
from handlers import routers
from middlewares.deps import DependenciesMiddleware
from services.ai_client import AIClient

BOT_USER = User(id=7, is_bot=True, first_name="TestBot", username="test_bot")

# Shu ID li foydalanuvchi botni "bloklagan" hisoblanadi — MockBot unga
# xabar yuborishga urinsa TelegramForbiddenError ko'taradi.
BLOCKED_USER_ID = 777


class MockBot(Bot):
    """Telegram'ga chiqmaydigan bot.

    Yuborilgan/tahrirlangan xabarlarni ro'yxatlarga yig'adi, shunda
    testlar bot nima javob berganini tekshira oladi.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.sent: list[tuple[int, str, object]] = []  # (chat_id, matn, klaviatura)
        self.edited: list[tuple[str, object]] = []  # (matn, klaviatura)
        self.answered: list[str | None] = []  # callback javoblari

    async def __call__(self, method: TelegramMethod, request_timeout: float | None = None):
        name = type(method).__name__

        if name == "SendMessage":
            if method.chat_id == BLOCKED_USER_ID:
                raise TelegramForbiddenError(method=method, message="bot was blocked by the user")
            self.sent.append((method.chat_id, method.text, method.reply_markup))
            return Message(
                message_id=len(self.sent) + 500,
                date=datetime.datetime.now(),
                chat=Chat(id=method.chat_id, type="private"),
                text=method.text,
                from_user=BOT_USER,
            )

        if name == "EditMessageText":
            self.edited.append((method.text, method.reply_markup))
            return Message(
                message_id=999,
                date=datetime.datetime.now(),
                chat=Chat(id=1, type="private"),
                text=method.text,
                from_user=BOT_USER,
            )

        if name == "AnswerCallbackQuery":
            self.answered.append(method.text)
            return True

        if name == "GetMe":
            return BOT_USER

        return True


class StubAI(AIClient):
    """AI o'rniga ishlaydigan soxta klient — haqiqiy API chaqirilmaydi."""

    def __init__(self, answer: str = "AI javobi.") -> None:
        self._answer = answer
        self.calls: list[tuple[str, list[ChatMessage]]] = []

    async def ask(self, system_prompt: str, history: list[ChatMessage]) -> str:
        self.calls.append((system_prompt, list(history)))
        return self._answer


# --------------------------------------------------------------- fixtures


@pytest.fixture
async def db(tmp_path):
    """Har bir test uchun toza SQLite bazasi."""
    database = Database(tmp_path / "test.db")
    await database.connect()
    yield database
    await database.close()


@pytest.fixture
def repo(db) -> Repository:
    return Repository(db)


@pytest.fixture
def ai() -> StubAI:
    return StubAI()


@pytest.fixture
async def bot():
    """Tarmoqqa chiqmaydigan bot."""
    mock = MockBot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    yield mock
    await mock.session.close()


@pytest.fixture
def dp(repo, ai):
    """Haqiqiy Dispatcher: middleware'lar va barcha routerlar ulangan."""
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.middleware(DependenciesMiddleware(repo, ai, settings))
    dispatcher.include_routers(*routers)

    yield dispatcher

    # Routerlar modul darajasidagi YAGONA obyektlar va bitta Dispatcher'ga
    # biriktirilib qoladi. Keyingi test o'zining yangi Dispatcher'iga ulay
    # olishi uchun bog'lanishni uzamiz, aks holda aiogram
    # "Router is already attached" xatosini beradi.
    for router in routers:
        router._parent_router = None


# ----------------------------------------------------------- yordamchilar


def make_user(user_id: int, name: str = "Shoxrux", language_code: str = "uz") -> User:
    return User(
        id=user_id,
        is_bot=False,
        first_name=name,
        username=f"user{user_id}",
        language_code=language_code,
    )


def text_update(
    text: str,
    user_id: int = 555,
    update_id: int = 1,
    language_code: str = "uz",
) -> Update:
    """Foydalanuvchi matnli xabar yuborgandek yangilanish yasaydi."""
    return Update(
        update_id=update_id,
        message=Message(
            message_id=update_id,
            date=datetime.datetime.now(),
            chat=Chat(id=user_id, type="private"),
            from_user=make_user(user_id, language_code=language_code),
            text=text,
        ),
    )


def photo_update(user_id: int = 555, update_id: int = 1) -> Update:
    """Matnsiz xabar (masalan, rasm) yuborilgandek yangilanish."""
    return Update(
        update_id=update_id,
        message=Message(
            message_id=update_id,
            date=datetime.datetime.now(),
            chat=Chat(id=user_id, type="private"),
            from_user=make_user(user_id),
        ),
    )


def callback_update(data: str, user_id: int = 555, update_id: int = 1) -> Update:
    """Inline tugma bosilgandek yangilanish yasaydi."""
    return Update(
        update_id=update_id,
        callback_query=CallbackQuery(
            id=str(update_id),
            from_user=make_user(user_id),
            chat_instance="test-chat-instance",
            data=data,
            message=Message(
                message_id=999,
                date=datetime.datetime.now(),
                chat=Chat(id=user_id, type="private"),
                text="eski matn",
                from_user=BOT_USER,
            ),
        ),
    )


def button_labels(markup) -> list[str]:
    """Klaviaturadagi tugma yozuvlarini ro'yxat qilib qaytaradi."""
    if markup is None:
        return []
    if hasattr(markup, "inline_keyboard"):
        return [b.text for row in markup.inline_keyboard for b in row]
    return [b.text for row in markup.keyboard for b in row]


def button_urls(markup) -> list[str]:
    """Inline klaviaturadagi havolalarni qaytaradi."""
    if markup is None or not hasattr(markup, "inline_keyboard"):
        return []
    return [b.url for row in markup.inline_keyboard for b in row if b.url]


def text_update_with_entities(
    text: str,
    entities: list,
    user_id: int = 555,
    update_id: int = 1,
) -> Update:
    """Telegram formatlashi (qalin, kursiv, havola) bilan xabar yasaydi.

    Telegram formatlashni matn ichidagi teg sifatida emas, alohida
    `entities` ro'yxati sifatida yuboradi — `message.html_text` aynan
    shulardan HTML yasaydi.
    """
    return Update(
        update_id=update_id,
        message=Message(
            message_id=update_id,
            date=datetime.datetime.now(),
            chat=Chat(id=user_id, type="private"),
            from_user=make_user(user_id),
            text=text,
            entities=entities,
        ),
    )

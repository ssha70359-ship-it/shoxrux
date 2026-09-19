"""Soxta Telegram Bot API va Anthropic API serverlari (faqat demo uchun).

Bot bularni haqiqiy xizmatlardan farqlamaydi: aiogram ham, anthropic SDK
ham oddiy HTTP so'rov yuboradi.
"""

from __future__ import annotations

import asyncio
import time

from aiohttp import web

UPDATES: asyncio.Queue = asyncio.Queue()  # botga yuboriladigan yangilanishlar
SENT: list[dict] = []  # bot yuborgan xabarlar
_msg_id = 1000


def _next_id() -> int:
    global _msg_id
    _msg_id += 1
    return _msg_id


# ----------------------------------------------------- Telegram Bot API


async def tg_method(request: web.Request) -> web.Response:
    method = request.match_info["method"]
    try:
        data = await request.json()
    except Exception:
        data = dict(await request.post())

    if method == "getMe":
        return web.json_response(
            {
                "ok": True,
                "result": {
                    "id": 7000001,
                    "is_bot": True,
                    "first_name": "Sunrise Konsultant",
                    "username": "sunrise_demo_bot",
                    "can_join_groups": True,
                    "can_read_all_group_messages": False,
                    "supports_inline_queries": False,
                },
            }
        )

    if method == "getUpdates":
        # Uzoq so'rov (long polling): 2 soniyagacha yangilanish kutamiz
        updates = []
        try:
            updates.append(await asyncio.wait_for(UPDATES.get(), timeout=2.0))
        except TimeoutError:
            pass
        while not UPDATES.empty():
            updates.append(UPDATES.get_nowait())
        return web.json_response({"ok": True, "result": updates})

    if method == "sendMessage":
        SENT.append(
            {
                "kind": "send",
                "chat_id": data["chat_id"],
                "text": data.get("text", ""),
                "markup": data.get("reply_markup"),
                "at": time.time(),
            }
        )
        return web.json_response(
            {
                "ok": True,
                "result": {
                    "message_id": _next_id(),
                    "date": int(time.time()),
                    "chat": {"id": data["chat_id"], "type": "private"},
                    "text": data.get("text", ""),
                },
            }
        )

    if method == "editMessageText":
        SENT.append(
            {
                "kind": "edit",
                "chat_id": data.get("chat_id"),
                "text": data.get("text", ""),
                "markup": data.get("reply_markup"),
                "at": time.time(),
            }
        )
        return web.json_response(
            {
                "ok": True,
                "result": {
                    "message_id": data.get("message_id", _next_id()),
                    "date": int(time.time()),
                    "chat": {"id": data.get("chat_id"), "type": "private"},
                    "text": data.get("text", ""),
                },
            }
        )

    # getUpdates'dan tashqari qolgan hamma narsa (setMyCommands,
    # deleteWebhook, sendChatAction, answerCallbackQuery...)
    return web.json_response({"ok": True, "result": True})


# ---------------------------------------------------------- Anthropic API

# Tilni System Prompt ichidagi ko'rsatmadan aniqlaymiz va shu tilda javob
# qaytaramiz — ClaudeService'ning haqiqiy kodi shu javobni tahlil qiladi.
REPLIES = {
    "uz": "Albatta! Korporativ sayt narxi 7 000 000 so'mdan boshlanadi. "
    "Aniq hisob-kitob uchun loyihangiz haqida qisqacha yozib bering.",
    "ru": "Конечно! Корпоративный сайт — от 7 000 000 сумов. "
    "Для точного расчёта опишите, пожалуйста, ваш проект.",
    "en": "Of course! A corporate website starts at 7,000,000 UZS. "
    "Tell me a bit about your project for an exact quote.",
}


# Bot yuborgan so'rovlar — demo oxirida nimalar jo'natilganini ko'rish uchun
REQUESTS: list[dict] = []


async def anthropic_messages(request: web.Request) -> web.Response:
    body = await request.json()
    REQUESTS.append(body)
    system = body.get("system", "")

    lang = "uz"
    if "РУССКОМ" in system:
        lang = "ru"
    elif "ENGLISH" in system:
        lang = "en"

    return web.json_response(
        {
            "id": "msg_demo",
            "type": "message",
            "role": "assistant",
            "model": body.get("model", "claude-opus-5"),
            "content": [{"type": "text", "text": REPLIES[lang]}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 120, "output_tokens": 40},
        }
    )


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_route("*", "/bot{token}/{method}", tg_method)
    return app


def build_anthropic_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/v1/messages", anthropic_messages)
    return app

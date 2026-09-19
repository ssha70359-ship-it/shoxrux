"""Botni haqiqiy jarayon sifatida ishga tushirib, u bilan suhbatlashadi.

Ishga tushirish (loyiha ildizidan):

    python scripts/demo.py

Haqiqiy BOT_TOKEN ham, ANTHROPIC_API_KEY ham kerak emas.

Bot kodi o'zgartirilmaydi: main.py alohida jarayonda, o'zining polling
sikli bilan ishlaydi. Faqat ikkita tashqi xizmat lokal soxta serverlarga
almashtirilgan (Telegram va Anthropic) — ikkalasi ham oddiy HTTP.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fake_services as ft
from aiohttp import web

PROJECT = Path(__file__).resolve().parent.parent
# Demo shu skriptni ishga tushirgan Python bilan ishlaydi
PYTHON = sys.executable
LAUNCHER = Path(__file__).resolve().parent / "_launcher.py"

ME = 555  # bu foydalanuvchi ham admin bo'lishi uchun ADMIN_ID ga qo'shiladi
TELEGRAM_PORT = 8081
ANTHROPIC_PORT = 8082
_update_id = 0


def _open_log(data_dir: Path):
    """Bot jarayonining logi uchun fayl ochadi.

    Alohida (async bo'lmagan) funksiyada: fayl ochish bloklovchi amal,
    uni event loop ichida bajarmaslik ma'qul.
    """
    return (data_dir / "demo-bot.log").open("w")


def _uid() -> int:
    global _update_id
    _update_id += 1
    return _update_id


def user_message(text: str, user_id: int = ME, language_code: str = "uz") -> dict:
    return {
        "update_id": _uid(),
        "message": {
            "message_id": _uid(),
            "date": int(time.time()),
            "chat": {"id": user_id, "type": "private", "first_name": "Shoxrux"},
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "Shoxrux",
                "username": "shoxrux",
                "language_code": language_code,
            },
            "text": text,
        },
    }


def button_press(data: str, user_id: int = ME) -> dict:
    return {
        "update_id": _uid(),
        "callback_query": {
            "id": str(_uid()),
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "Shoxrux",
                "username": "shoxrux",
                "language_code": "uz",
            },
            "chat_instance": "demo",
            "data": data,
            "message": {
                "message_id": 900,
                "date": int(time.time()),
                "chat": {"id": user_id, "type": "private"},
                "text": "oldingi xabar",
                "from": {"id": 7000001, "is_bot": True, "first_name": "Bot"},
            },
        },
    }


# ------------------------------------------------------------- chiqarish

RESET, DIM, BOLD = "\033[0m", "\033[2m", "\033[1m"
BLUE, GREEN, YELLOW = "\033[34m", "\033[32m", "\033[33m"


def show_keyboard(markup: dict | None) -> None:
    if not markup:
        return
    if "keyboard" in markup:
        rows = [" | ".join(b["text"] for b in row) for row in markup["keyboard"]]
        print(f"      {DIM}[pastdagi tugmalar] {'  ||  '.join(rows)}{RESET}")
    elif "inline_keyboard" in markup:
        for row in markup["inline_keyboard"]:
            cells = []
            for b in row:
                cells.append(f"( {b['text']} )" + (f" -> {b['url']}" if b.get("url") else ""))
            print(f"      {DIM}{'  '.join(cells)}{RESET}")


async def drain(label: str, wait: float = 2.5) -> None:
    """Bot javoblarini kutib, ekranga chiqaradi."""
    ft.SENT.clear()
    deadline = time.time() + wait
    seen = 0
    while time.time() < deadline:
        await asyncio.sleep(0.15)
        if len(ft.SENT) > seen:
            deadline = time.time() + 1.0  # yana kelishi mumkin
            seen = len(ft.SENT)

    for item in ft.SENT:
        tag = "tahrirlandi" if item["kind"] == "edit" else "javob"
        text = item["text"]
        print(f"   {GREEN}BOT{RESET} {DIM}({tag}){RESET}:")
        for line in text.split("\n"):
            print(f"      {line}")
        show_keyboard(
            item["markup"]
            if isinstance(item["markup"], dict)
            else json.loads(item["markup"])
            if item["markup"]
            else None
        )
        print()


async def say(text: str, label: str | None = None, **kw) -> None:
    print(f"   {BLUE}SIZ{RESET}: {BOLD}{text}{RESET}")
    await ft.UPDATES.put(user_message(text, **kw))
    await drain(label or text)


async def press(data: str, label: str) -> None:
    print(f"   {BLUE}SIZ{RESET}: {BOLD}[tugma: {label}]{RESET}")
    await ft.UPDATES.put(button_press(data))
    await drain(label)


def step(title: str) -> None:
    print(f"\n{YELLOW}{'━' * 70}{RESET}")
    print(f"{YELLOW}▸ {title}{RESET}")
    print(f"{YELLOW}{'━' * 70}{RESET}\n")


# ------------------------------------------------------------------ main


async def main() -> None:
    # Soxta Telegram
    tg = web.AppRunner(ft.build_app())
    await tg.setup()
    await web.TCPSite(tg, "127.0.0.1", TELEGRAM_PORT).start()

    # Soxta Anthropic
    an = web.AppRunner(ft.build_anthropic_app())
    await an.setup()
    await web.TCPSite(an, "127.0.0.1", ANTHROPIC_PORT).start()

    print(f"{DIM}Soxta Telegram  -> http://127.0.0.1:{TELEGRAM_PORT}{RESET}")
    print(f"{DIM}Soxta Anthropic -> http://127.0.0.1:{ANTHROPIC_PORT}{RESET}")

    # Toza baza
    data_dir = PROJECT / "data"
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Barcha sozlamalarni shu yerda beramiz. Haqiqiy muhit o'zgaruvchilari
    # `.env` faylidan ustun turadi, shuning uchun demo `.env` bo'lmasa ham
    # (toza klonda ham) ishlaydi va mavjud `.env` ga tegmaydi.
    env = {
        **os.environ,
        "BOT_TOKEN": "123456789:DEMO-token-hech-qayerga-yuborilmaydi",
        "ADMIN_ID": str(ME),
        "AI_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "sk-ant-demo-kalit-ishlatilmaydi",
        # anthropic SDK bu o'zgaruvchini o'zi o'qiydi — so'rovlar lokal
        # soxta serverga ketadi, haqiqiy API ga emas
        "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{ANTHROPIC_PORT}",
        "DEMO_TELEGRAM_PORT": str(TELEGRAM_PORT),
        "COMPANY_NAME": "Sunrise Digital",
        "COMPANY_FIELD": "veb-sayt va mobil ilova ishlab chiqish",
        "COMPANY_INFO": "Ish vaqti: Du-Sha 09:00-18:00. Toshkent, Amir Temur 15.",
        "BOT_PERSONA_NAME": "Aziza",
        "OPERATOR_USERNAME": "@sunrise_manager",
        "OPERATOR_PHONE": "+998901234567",
        "DEFAULT_LANGUAGE": "uz",
        "DB_PATH": "data/demo.db",
        "THROTTLE_RATE": "0",
        "LOG_LEVEL": "INFO",
        "PYTHONUNBUFFERED": "1",
    }
    log = _open_log(data_dir)
    bot = await asyncio.create_subprocess_exec(
        PYTHON,
        str(LAUNCHER),
        cwd=str(PROJECT),
        env=env,
        stdout=log,
        stderr=asyncio.subprocess.STDOUT,
    )

    try:
        await asyncio.sleep(4)  # bot ishga tushishini kutamiz
        if bot.returncode is not None:
            print(f"Bot ishga tushmadi — {data_dir / 'demo-bot.log'} ga qarang")
            return

        print(f"{GREEN}✓ Bot ishga tushdi (PID {bot.pid}){RESET}")

        step("1. /start — tanishuv va asosiy menyu")
        await say("/start")

        step("2. Savol beramiz — Claude javob beradi")
        await say("Korporativ sayt qancha turadi?")

        step("3. Kontekstni tekshiramiz — qisqa savol")
        await say("Muddati-chi?")

        step("4. Tilni rus tiliga o'zgartiramiz")
        await say("🌐 Tilni o'zgartirish")
        await press("lang:ru", "🇷🇺 Русский")

        step("5. Endi bot ruscha javob beradi")
        await say("Сколько стоит сайт?")

        step("6. Bog'lanish bo'limi")
        await say("📞 Связаться")

        step("7. Suhbatni tozalash")
        await say("📜 Очистить диалог")

        step("8. Admin panel (555 — admin)")
        await say("/admin")
        await press("admin:stats", "📊 Статистика")

        step("9. Ommaviy xabar — matn so'raladi")
        await press("admin:broadcast", "📣 Рассылка")
        await say("Assalomu alaykum! Yangi chegirmalar boshlandi.")

        step("10. Bekor qilamiz")
        await press("bcast:cancel", "❌ Отменить")

        step("11. Noma'lum buyruq")
        await say("/bunday_buyruq_yoq")

        step("12. Claude'ga qanday so'rov ketdi")
        if ft.REQUESTS:
            first = ft.REQUESTS[0]
            print(f"   model        : {first.get('model')}")
            print(f"   max_tokens   : {first.get('max_tokens')}")
            print(f"   output_config: {first.get('output_config', '(yuborilmadi)')}")
            print(f"   system       : {len(first.get('system', ''))} belgi")
            print(f"   messages     : {len(first.get('messages', []))} ta")
        else:
            print("   (so'rov yuborilmadi)")

    finally:
        if bot.returncode is None:
            bot.terminate()
            try:
                await asyncio.wait_for(bot.wait(), timeout=10)
            except TimeoutError:
                bot.kill()
        log.close()
        await tg.cleanup()
        await an.cleanup()
        print(f"\n{DIM}Bot to'xtatildi. Bot logi: {data_dir / 'demo-bot.log'}{RESET}")


asyncio.run(main())

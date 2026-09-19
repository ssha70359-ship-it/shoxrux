# 🤖 AI-konsultant bot (aiogram 3.x + Anthropic Claude)

Telegram bot: kompaniyaning xushfe'l onlayn konsultanti. Claude AI bilan
suhbatlashadi, kontekstni eslab qoladi, uch tilda ishlaydi va admin paneliga
ega. To'liq asinxron (`async/await`), modulli tuzilma.

---

## ⚠️ Model haqida muhim eslatma

Siz so'ragan ikkala model ham **endi ishlamaydi**:

| Model | Holati |
|---|---|
| `claude-3-5-sonnet-20241022` | **To'xtatilgan** (2025-10-28) — API xato qaytaradi |
| `claude-3-haiku-20240307` | **To'xtatilgan** (2026-04-19) |

Buning o'rniga joriy modellar ishlatiladi (`.env` dagi `ANTHROPIC_MODEL`):

| Model | Kontekst | Narx (input/output, 1M token) | Qachon |
|---|---|---|---|
| `claude-haiku-4-5` *(sukut bo'yicha)* | 200K | $1 / $5 | Eng arzon va tez — konsultant-bot uchun yetarli |
| `claude-sonnet-5` | 1M | $2 / $10 | Murakkabroq savollar uchun |
| `claude-opus-5` | 1M | $5 / $25 | Eng kuchli |

Model ID lariga sana qo'shilmaydi — jadvaldagi satr to'liq ID.

---

## 📂 Loyiha tuzilmasi

```
ai-consultant-bot/
├── main.py                       # Entry point: Bot, Dispatcher, ishga tushirish
├── config.py                     # .env sozlamalari (pydantic-settings)
├── requirements.txt              # Kutubxonalar
├── requirements.lock.txt         # Sinovdan o'tgan aniq versiyalar
├── requirements-dev.txt          # pytest, ruff (faqat ishlab chiqish uchun)
├── pyproject.toml                # ruff va pytest sozlamalari
├── .env.example                  # .env uchun namuna
├── .gitignore
├── README.md
│
├── scripts/                      # Demo (haqiqiy token kerak emas)
│   ├── demo.py                   #   botni ishga tushirib, u bilan suhbatlashadi
│   ├── fake_services.py          #   soxta Telegram va Anthropic serverlari
│   └── _launcher.py              #   aiogram sessiyasini lokal serverga qaratadi
│
├── tests/                        # 86 ta test (pytest)
│   ├── conftest.py               #   fixture'lar: soxta bot, stub AI, baza
│   ├── test_database.py          #   sxema, migratsiya, tarix, statistika
│   ├── test_handlers.py          #   menyu, til, AI suhbat, xatolar
│   ├── test_admin.py             #   kirish huquqi, statistika, broadcast
│   ├── test_services.py          #   Claude, System Prompt, sozlamalar
│   ├── test_locales.py           #   tarjima kalitlari, fallback
│   └── test_utils.py             #   matn bo'laklash, HTML tozalash
│
├── data/                         # SQLite fayli shu yerda (gitga tushmaydi)
│   └── bot.db
│
├── database/                     # Ma'lumotlar bazasi qatlami
│   ├── db.py                     #   aiosqlite ulanishi, sxema, migratsiya
│   ├── models.py                 #   User, ChatMessage, Stats (dataclass)
│   └── repository.py             #   barcha SQL so'rovlar
│
├── handlers/                     # Telegram yangilanishlarini qabul qilish
│   ├── __init__.py               #   routerlar tartibi (muhim!)
│   ├── start.py                  #   /start, /menu, /help, /language, til tanlash
│   ├── ai_chat.py                #   Claude bilan suhbat, /reset
│   └── admin.py                  #   /admin, statistika, broadcast (FSM)
│
├── keyboards/
│   ├── reply.py                  #   doimiy menyu (5 tugma, tilga qarab)
│   └── inline.py                 #   til tanlash, admin panel, tasdiqlash
│
├── services/                     # Biznes mantiq / tashqi xizmatlar
│   ├── ai_client.py              #   umumiy interfeys + factory
│   ├── claude_service.py         #   Anthropic Claude (asosiy)
│   ├── openai_service.py         #   OpenAI (muqobil, ixtiyoriy)
│   └── prompts.py                #   System Prompt + til qoidalari
│
├── locales/                      # Ko'p tillilik
│   ├── __init__.py               #   t() funksiyasi va fallback
│   ├── uz.py  ru.py  en.py       #   matnlar (38 ta kalit, uchchalasida bir xil)
│
├── middlewares/
│   ├── deps.py                   #   DI: repo/ai/lang ni handlerga uzatish
│   └── throttling.py             #   anti-spam (xabar + tugma)
│
└── utils/
    ├── logger.py                 #   loglash sozlamasi
    └── text.py                   #   uzun matnni bo'laklash, HTML tozalash
```

**Qatlamlar qoidasi:** `handlers` → `services` / `database`. Handler ichida SQL
yozilmaydi va API chaqirilmaydi.

---

## 🚀 Ishga tushirish

```bash
cd ai-consultant-bot

# 1. Virtual muhit
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Kutubxonalar
pip install -r requirements.txt
# yoki aniq, sinovdan o'tgan versiyalar bilan:
# pip install -r requirements.lock.txt

# 3. Sozlamalar
cp .env.example .env
nano .env                          # BOT_TOKEN, ANTHROPIC_API_KEY, ADMIN_ID

# 4. Ishga tushirish
python main.py
```

Baza fayli va `data/` papkasi birinchi ishga tushirishda avtomatik yaratiladi.
Bot oldingi versiyada ishlagan bo'lsa, eski jadvallar **avtomatik ko'chiriladi**
(`language` → `selected_language`, `created_at` → `joined_at`), ma'lumot
yo'qolmaydi.

---

## ⚙️ `.env` fayl formati

| O'zgaruvchi | Majburiy | Sukut bo'yicha | Izoh |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | — | @BotFather dan olingan token |
| `ADMIN_ID` | — | — | Admin ID(lar), vergul bilan: `111,222` |
| `AI_PROVIDER` | — | `anthropic` | `anthropic` yoki `openai` |
| `ANTHROPIC_API_KEY` | ✅ | — | Claude API kaliti |
| `ANTHROPIC_MODEL` | — | `claude-haiku-4-5` | Yuqoridagi jadvalga qarang |
| `AI_EFFORT` | — | `low` | `low`…`max` — javob chuqurligi. Haiku'da ishlamaydi (quyiga qarang) |
| `OPENAI_API_KEY` | `openai` uchun | — | Muqobil provayder |
| `OPENAI_MODEL` | — | `gpt-4o-mini` | |
| `AI_MAX_TOKENS` | — | `1024` | Javob uzunligi chegarasi |
| `COMPANY_NAME` | — | `Kompaniya` | System Prompt'ga qo'shiladi |
| `COMPANY_FIELD` | — | `xizmat ko'rsatish` | Bot qaysi soha bilan cheklanadi |
| `COMPANY_INFO` | — | — | Ish vaqti, telefon, manzil |
| `BOT_PERSONA_NAME` | — | `Konsultant` | Botning ismi |
| `OPERATOR_USERNAME` | — | — | "Operatorga yozish" tugmasi havolasi |
| `OPERATOR_PHONE` | — | — | Telefon (username bo'lmasa) |
| `DEFAULT_LANGUAGE` | — | `uz` | `uz` / `ru` / `en` |
| `HISTORY_LIMIT` | — | `10` | Kontekstdagi oxirgi xabarlar soni |
| `DB_PATH` | — | `data/bot.db` | SQLite fayl yo'li |
| `THROTTLE_RATE` | — | `1.0` | Anti-spam, soniya (`0` — o'chirilgan) |
| `BROADCAST_RATE` | — | `20` | Sekundiga nechta xabar (Telegram limiti ~30) |
| `LOG_LEVEL` | — | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

> ⚠️ `.env` fayli `.gitignore` da — tokenlar hech qachon repozitoriyga tushmaydi.

> 💡 `AI_EFFORT` ataylab `CLAUDE_EFFORT` deb nomlanmagan: `CLAUDE_*` prefiksi
> Claude Code kabi vositalarning muhit o'zgaruvchilari bilan to'qnashadi, haqiqiy
> muhit o'zgaruvchisi esa `.env` faylidan **ustun turadi** — ya'ni sozlamangiz
> jimgina e'tiborsiz qolardi.

---

## 🧠 Claude integratsiyasi

`services/claude_service.py` — Messages API ustidagi qobiq:

```python
response = await self._client.messages.create(
    model=self._model,
    system=system_prompt,  # Claude'da system ALOHIDA parametr
    messages=messages,  # ichida faqat user/assistant
    max_tokens=self._max_tokens,
    output_config={"effort": "low"},
)
```

**Muhim tafsilotlar:**

- **`system` alohida parametr.** OpenAI'da u `messages[0]`, Claude'da esa
  top-level maydon. Ikki API o'rtasidagi asosiy farq shu.
- **`effort`** javob chuqurligini boshqaradi. **Haiku modellari uni
  qo'llab-quvvatlamaydi** (API 400 qaytaradi), shuning uchun model nomida
  `haiku` bo'lsa parametr avtomatik o'tkazib yuboriladi va ishga tushganda
  logga bir qatorlik eslatma yoziladi. Sukutdagi model Haiku bo'lgani uchun
  `AI_EFFORT` odatda e'tiborsiz qoladi — u Sonnet yoki Opus'ga
  o'tganingizda ishlay boshlaydi (konsultant-bot uchun `low` yetarli).
- **`stop_reason == "refusal"`** tekshiriladi: model javob berishdan bosh
  tortsa, foydalanuvchiga tushunarli xabar chiqadi.
- **Javob bloklari.** `response.content` bir nechta blokdan iborat bo'lishi
  mumkin (masalan `thinking`), shuning uchun faqat `type == "text"` bloklari
  yig'iladi.

Provayderni almashtirish uchun `.env` da `AI_PROVIDER=openai` yozsangiz kifoya —
ikkala servis bir xil `ask(system_prompt, history) -> str` interfeysini bajaradi.

---

## 🌐 Ko'p tillilik

Uch til: 🇺🇿 O'zbekcha, 🇷🇺 Русский, 🇬🇧 English.

**Til qanday tanlanadi:**

1. Yangi foydalanuvchi uchun **Telegram interfeysi tili** olinadi
   (`language_code` `uz`/`ru`/`en` bo'lsa), aks holda `DEFAULT_LANGUAGE`.
2. Foydalanuvchi `🌐 Tilni o'zgartirish` yoki `/language` orqali o'zgartiradi.
3. Tanlov `users.selected_language` ga yoziladi va **hech qachon ustidan
   yozilmaydi** — profil yangilanganda ham saqlanib qoladi.

**Til nimalarga ta'sir qiladi:**

- Bot interfeysi — barcha matnlar va tugma yozuvlari (`locales/`).
- **Claude javoblari** — System Prompt oxiriga aniq ko'rsatma qo'shiladi:

  ```
  ЯЗЫК ОТВЕТА: Всегда отвечай на РУССКОМ языке, даже если пользователь
  пишет на другом языке.
  ```

  "Foydalanuvchi tilida javob ber" degan mavhum ko'rsatmadan ko'ra, tilni
  aniq aytish ishonchliroq ishlaydi.

**Tarjima yo'q bo'lsa** `t()` o'zbekchaga qaytadi va logga ogohlantirish
yozadi — bot hech qachon xato bermaydi.

Tugma filtrlari **uchala tildagi** yozuvni qabul qiladi (`all_button_texts`),
shuning uchun til almashtirilgandan keyin ekranda qolib ketgan eski klaviatura
ham ishlashda davom etadi.

---

## 🗄 Baza sxemasi

```sql
users (
    user_id           INTEGER PRIMARY KEY,   -- Telegram id
    username          TEXT,
    full_name         TEXT,
    selected_language TEXT NOT NULL DEFAULT 'uz',
    joined_at         TEXT NOT NULL DEFAULT (datetime('now')),
    last_active_at    TEXT NOT NULL DEFAULT (datetime('now')),  -- statistika uchun
    is_blocked        INTEGER NOT NULL DEFAULT 0                -- broadcast uchun
)

messages (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER -> users.user_id ON DELETE CASCADE,
    role      TEXT CHECK (role IN ('user','assistant')),
    content   TEXT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
)

INDEX idx_messages_user_id   ON messages (user_id, id DESC)
INDEX idx_messages_timestamp ON messages (timestamp)
```

`PRAGMA journal_mode=WAL` yoqilgan. Ikkita ustun sizning ro'yxatingizda yo'q
edi, lekin zarur bo'ldi: `is_blocked` — botni bloklaganlarga qayta urinmaslik
uchun, `last_active_at` — statistika `/reset` dan keyin ham to'g'ri qolishi
uchun.

---

## 💬 Buyruqlar va menyu

**Asosiy menyu (reply klaviatura):**

```
┌──────────────────────┬────────────────────────┐
│ 🤖 AI bilan suhbat   │ 📜 Suhbatni tozalash    │
├──────────────────────┼────────────────────────┤
│ 🌐 Tilni o'zgartirish│ ℹ️ Bot haqida           │
├──────────────────────┴────────────────────────┤
│ 📞 Bog'lanish                                  │
└───────────────────────────────────────────────┘
```

| Buyruq | Vazifasi |
|---|---|
| `/start` | Tanishuv + menyu |
| `/menu` | Menyuni qayta ko'rsatish |
| `/language` | Tilni o'zgartirish |
| `/reset` | Suhbat tarixini tozalash |
| `/help` | Bot haqida va buyruqlar |
| `/admin` | 🔒 Admin panel |
| `/stats` | 🔒 Statistika |
| `/broadcast` | 🔒 Ommaviy xabar |

Adminlar uchun kengaytirilgan buyruqlar ro'yxati `BotCommandScopeChat` orqali
**faqat ularning chatida** ko'rsatiladi.

---

## 🛠 Admin panel

Kirish `.env` dagi `ADMIN_ID` bo'yicha. Filtr **butun routerga** qo'yilgan:

```python
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())
```

Shu tufayli admin bo'lmagan odam uchun bu handlerlar umuman mavjud emasdek
bo'ladi va xabar keyingi routerga o'tadi — u yerda "noma'lum buyruq" javobini
oladi. Ya'ni **botda admin paneli borligi oshkor bo'lmaydi**.

### 📊 Statistika

Jami foydalanuvchilar, bugun qo'shilganlar, **bugun faol bo'lganlar**,
botni bloklaganlar, saqlangan xabarlar va tillar bo'yicha taqsimot.

> **Faollik qayerdan olinadi.** `users.last_active_at` dan — `messages`
> jadvalidan emas. Sabab: foydalanuvchi `/reset` bosганda o'z tarixini
> o'chiradi, agar statistika xabarlardan hisoblanganda edi, admin
> ko'rsatkichlari ham nolga tushib ketardi. `last_active_at` esa har bir
> xabar va tugma bosishda yangilanadi (DI middleware orqali), shuning
> uchun tarixga bog'liq emas.
>
> "Saqlangan xabarlar" esa ataylab ayni damdagi tarix hajmini ko'rsatadi
> va `/reset` da kamayadi — matnda ham shunday deb yozilgan.

### 📣 Ommaviy xabar (broadcast)

FSM orqali uch bosqich:

```
/broadcast  ──►  matnni kutish  ──►  ko'rib chiqish + tasdiqlash  ──►  yuborish
                       │                        │
                   /cancel                  ❌ Bekor
```

- Matn `message.html_text` orqali olinadi — **formatlash saqlanadi**
  (qalin, kursiv, havola).
- Yuborishdan oldin xabar ko'rinishi va qabul qiluvchilar soni ko'rsatiladi.
- Yuborish `BROADCAST_RATE` (sekundiga 20) tezligida, har biridan keyin pauza.
- `TelegramForbiddenError` — foydalanuvchi bloklagan → bazada `is_blocked=1`,
  keyingi safar ro'yxatga kirmaydi.
- `TelegramRetryAfter` — Telegram "sekinroq" desa, kutib qayta urinadi.
- Bitta xato butun tarqatishni to'xtatmaydi; oxirida hisobot chiqadi:
  yetkazildi / bloklagan / xatolik.

---

## ▶️ Demo — botni ko'rish

Haqiqiy `BOT_TOKEN` ham, `ANTHROPIC_API_KEY` ham kerak emas. `.env` fayli
bo'lmasa ham ishlaydi va mavjud `.env` ga tegmaydi:

```bash
python scripts/demo.py
```

Skript nima qiladi:

1. Ikkita lokal soxta server ko'taradi — Telegram Bot API (`:8081`) va
   Anthropic API (`:8082`).
2. `main.py` ni **alohida jarayonda**, o'zining polling sikli bilan ishga
   tushiradi.
3. Bot bilan suhbat o'tkazadi va yozishmani ekranga chiqaradi: `/start`,
   savol-javob, tilni almashtirish, bog'lanish, tarixni tozalash, admin
   panel, ommaviy xabar.

Bot kodiga umuman tegilmaydi — polling, routerlar, middleware'lar, FSM,
SQLite va `ClaudeService`ning so'rov yasashi/javobni tahlil qilishi
hammasi haqiqiy. Faqat ikkita tashqi xizmat lokal HTTP serverlarga
almashtirilgan (Telegram'ning o'zi ham "local Bot API server" ni
qo'llab-quvvatlaydi, ya'ni bu sun'iy holat emas).

Bot logi `data/demo-bot.log` ga yoziladi.

---

## 🧪 Testlar

```bash
pip install -r requirements-dev.txt

pytest                      # barcha testlar
pytest -v                   # har bir test nomi bilan
pytest tests/test_admin.py  # bitta fayl
pytest -k broadcast         # nomida "broadcast" bo'lganlari

ruff check .                # linter
ruff check . --fix          # avtomatik tuzatish
ruff format .               # formatlash
```

Testlar **haqiqiy `Dispatcher`** orqali ishlaydi: xabar va tugma bosishlari
`dp.feed_update()` bilan yuboriladi, faqat ikki narsa almashtirilgan —
Telegram API (`MockBot`, tarmoqqa chiqmaydi) va AI (`StubAI`, pul sarflamaydi).
Ya'ni routerlar tartibi, middleware'lar, FSM holatlari va filtrlar
haqiqiy ish rejimida tekshiriladi.

Baza har bir test uchun `tmp_path` da yangidan yaratiladi.

> ⚠️ `tests/conftest.py` muhit o'zgaruvchilarini **import'lardan oldin**
> o'rnatadi, chunki `config.settings` modul yuklanganda bir marta yaratiladi.
> Shu sababli testlar mashinangizdagi `.env` ga bog'liq emas.

**Nimalar tekshiriladi:**

| Fayl | Testlar |
|---|---|
| `test_database.py` | Sxema, eski bazadan migratsiya, `ON DELETE CASCADE`, tarix tartibi va ajratilishi, statistika va faollikning `/reset` dan omon qolishi, tilning ustidan yozilmasligi |
| `test_handlers.py` | Menyu, til avtomatik aniqlash va almashtirish, AI konteksti, uzun javob bo'laklanishi, noma'lum buyruq, AI xatolari |
| `test_admin.py` | Admin bo'lmaganga panel ko'rinmasligi, statistika (`/reset` dan keyin ham), broadcast oqimi (yuborish, bloklaganni aniqlash, bekor qilish, FSM tozalanishi) |
| `test_services.py` | System Prompt tili, provayder factory, Haiku uchun `effort` o'tkazib yuborilishi, sozlamalar validatsiyasi |
| `test_locales.py` | Uchala tilda kalitlar bir xilligi, fallback |
| `test_utils.py` | Matn bo'laklash chegaralari, HTML tozalash |

---

## ⚙️ CI (GitHub Actions)

`.github/workflows/bot-ci.yml` — har push va PR'da ishlaydi, lekin faqat
`ai-consultant-bot/**` o'zgarganda (repozitoriya ildizidagi Node.js loyihasiga
tegmaydi).

| Qadam | Nima qiladi |
|---|---|
| `ruff check` | Linter: ishlatilmagan import, import tartibi, eskirgan sintaksis, async xatolari |
| `ruff format --check` | Formatlash bir xilligini tekshiradi (fayllarni o'zgartirmaydi) |
| `python -m compileall` | Barcha fayllar sintaktik to'g'ri ekanini tasdiqlaydi |
| `pytest -v` | 86 ta test |

Python 3.11 va 3.12 da parallel ishlaydi (`StrEnum` va `X | None` sintaksisi
3.11+ talab qiladi). Bitta branchga ketma-ket push bo'lsa, eski ishlar
avtomatik bekor qilinadi.

---

## 🛡 Xatolarni boshqarish

| Holat | Bot nima qiladi |
|---|---|
| API limiti (`RateLimitError`) | "So'rovlar ko'p, bir daqiqadan so'ng urinib ko'ring" |
| API nosozligi (5xx) | "AI xizmatida vaqtinchalik nosozlik" |
| `stop_reason == "refusal"` | "Boshqacha ifodalang" |
| Kutilmagan xato | Traceback logga, foydalanuvchiga umumiy xabar |
| Javob 4096 belgidan uzun | Qator chegarasidan bo'laklab yuboriladi |
| Javobda HTML buzuvchi belgi | Oddiy matn sifatida qayta yuboriladi |
| Noma'lum buyruq | "Bunday buyruq yo'q, /help" |
| Rasm/stiker | "Faqat matnli xabarlarni tushunaman" |

Barcha xato matnlari ham foydalanuvchi tilida chiqadi.

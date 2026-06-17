# Docker Deployment Guide

Doc `README.md` va `docs/agent-handoff.md` truoc neu ban la agent/developer moi tiep quan du an.

Huong dan nay dung de clone repo tren may moi va chay bot bang Docker, khong can cai Python tren host.

## 1. Yeu cau

Can co san:

- Git
- Docker Desktop hoac Docker Engine
- Telegram bot token
- Google Sheet ID
- Google service account JSON

Kiem tra Docker:

```powershell
docker --version
docker compose version
```

Neu `docker --version` chay duoc nhung `docker compose ...` bao loi pipe `dockerDesktopLinuxEngine`, Docker CLI da co nhung Docker Desktop engine chua bat. Mo Docker Desktop roi chay lai lenh.

## 2. Clone repo

```powershell
git clone git@github-personal:Khiemdept226/LearnJapanese.git
cd LearnJapanese
```

Neu repo duoc clone vao workspace cha, hay vao dung thu muc co `docker-compose.yml`:

```powershell
cd LearnJapanese
```

## 3. Tao file `.env`

Copy file mau:

```powershell
Copy-Item .env.example .env
```

Mo `.env` va dien cac bien chinh:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google-service-account.json

TIMEZONE=Asia/Bangkok
DAILY_SEND_TIME=07:30
DATABASE_PATH=data/learningjp.sqlite3

FLASHCARD_ENABLED=true
FLASHCARD_DAILY_TIME=20:30
FLASHCARD_DAILY_NEW_LIMIT=5
FLASHCARD_DAILY_REVIEW_LIMIT=20
FLASHCARD_LEVEL=N4
FLASHCARD_TIMEZONE=Asia/Bangkok
```

Ghi chu:

- `TELEGRAM_BOT_TOKEN`: lay tu BotFather.
- `GOOGLE_SHEET_ID`: phan ID trong URL Google Sheet.
- `DATABASE_PATH`: giu mac dinh neu dung Docker Compose trong repo nay.
- Flashcard hien co preset mac dinh `jlpt_sprint` trong code cho dot thi JLPT 2026-07-05. Env limit la fallback chung.

Khong commit `.env` len git.

## 4. Them Google credential

Tao thu muc credential:

```powershell
New-Item -ItemType Directory -Force credentials
```

Dat file service account vao dung path:

```text
credentials/google-service-account.json
```

Google Sheet phai share quyen read cho email service account.

## 5. Build Docker image

```powershell
docker compose build
```

Lan dau co the lau vi phai tai Python image va cai dependencies.

Neu can xem chi tiet buoc build:

```powershell
docker compose build --progress=plain
```

## 6. Import flashcard N4

Nguon khuyen dung la Google Sheet worksheet `flashcards` trong spreadsheet da cau hinh bang `GOOGLE_SHEET_ID`.

Header bat buoc cua worksheet:

```text
card_id
level
source
source_position
word
reading
meaning
hanviet
example_jp
example_vi
tags
status
```

Chay dry-run tu Sheet truoc:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source sheet --dry-run
```

Ket qua mong doi:

```text
Source: sheet
Fetched: 276
Ready: 276
Imported: 0
Skipped: 0
Warnings: <so warning tuy du lieu sheet>
```

Import that tu Sheet vao SQLite:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source sheet
```

PDF van la fallback:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source pdf --dry-run
docker compose run --rm bot python tools/import_flashcards.py --source pdf
```

Lenh PDF cu van hoat dong:

```powershell
docker compose run --rm bot python tools/import_n4_pdf.py --dry-run
```

Neu gap `sqlite3.OperationalError: disk I/O error`, dung bot truoc va xoa journal tam:

```powershell
docker compose down
Remove-Item .\data\learningjp.sqlite3-journal -Force -ErrorAction SilentlyContinue
docker compose run --rm bot python tools/import_flashcards.py --source sheet
```
## 7. Chay tests

May hien tai khong cai Python local theo `docs/runtime-environment-memo.md`. Dung Docker de test khi Docker engine dang chay.

```powershell
docker compose run --rm bot pytest -q
```

Ket qua mong doi:

```text
17 passed
```

Kiem tra compile nhanh:

```powershell
docker compose run --rm bot python -m py_compile src/bot.py src/flashcards.py src/flashcard_handlers.py src/flashcard_scheduler.py tools/import_n4_pdf.py
```

Lenh compile thanh cong se khong in gi va exit code 0.

## 8. Start bot

```powershell
docker compose up -d
```

Xem log:

```powershell
docker compose logs -f bot
```

Dung bot:

```text
/start
/flash_start
/flash
```

Sau `/flash`, bot hien nut bam:

```text
Hiện đáp án
Quên / Khó / Nhớ / Dễ
Học tiếp / Thống kê
```

Doi muc tieu hoc:

```text
/flash_goal
```

Chon `Nước rút JLPT` neu muon hoc nhanh cho dot thi gan.

## 9. Lenh van hanh hay dung

Dung bot:

```powershell
docker compose down
```

Restart bot:

```powershell
docker compose restart bot
```

Rebuild va chay lai sau khi pull code moi:

```powershell
git pull
docker compose up -d --build
```

Xem container dang chay:

```powershell
docker compose ps
```

Xem log gan nhat:

```powershell
docker compose logs --tail=100 bot
```

## 10. Backup va restore tien do hoc

Tien do user, flashcard review, va lich su bot nam trong:

```text
data/learningjp.sqlite3
```

Backup:

```powershell
Copy-Item .\data\learningjp.sqlite3 .\data\learningjp.backup.sqlite3
```

Restore:

```powershell
docker compose down
Copy-Item .\data\learningjp.backup.sqlite3 .\data\learningjp.sqlite3 -Force
docker compose up -d
```

Nen backup file DB truoc khi chuyen may, deploy server moi, hoac sua schema lon.

## 11. Troubleshooting

### Docker build lau

Chay:

```powershell
docker compose build --progress=plain
```

Neu ket o buoc pip install, kiem tra mang hoac thu build lai.

### Bot khong doc duoc Google Sheet

Kiem tra:

- `.env` co dung `GOOGLE_SHEET_ID`.
- File `credentials/google-service-account.json` ton tai.
- Google Sheet da share quyen read cho email service account.

### Bot khong phan hoi Telegram

Kiem tra log:

```powershell
docker compose logs -f bot
```

Kiem tra token:

```env
TELEGRAM_BOT_TOKEN=...
```

Neu vua sua `.env`, restart bot:

```powershell
docker compose restart bot
```

### Import PDF thanh cong nhung bot bao chua co the

Kiem tra DB path trong `.env`:

```env
DATABASE_PATH=data/learningjp.sqlite3
```

Kiem tra so the:

```powershell
docker compose run --rm bot python -c "import sqlite3; c=sqlite3.connect('/app/data/learningjp.sqlite3'); print(c.execute('select count(*) from flashcards').fetchone()[0]); c.close()"
```

Ket qua nen la `219` hoac lon hon neu sau nay import them bo moi.



## Learning items deck model

Flashcard learning now uses new canonical SQLite tables while keeping old tables for fallback:

```text
decks
learning_items
user_learning_reviews
user_learning_sessions
user_learning_settings
```

Do not drop legacy tables during rollout:

```text
flashcards
user_flashcard_reviews
user_flashcard_sessions
user_flashcard_settings
```

Google Sheet uses one spreadsheet from `GOOGLE_SHEET_ID`. Keep existing daily lesson sheet and legacy `flashcards` worksheet. Add these worksheets for the long-term deck model:

### `deck_catalog`

Columns:

```text
deck_id
title
level
item_type
worksheet_name
source
status
description
```

Example active decks:

```text
n4_vocab_core | N4 Core Vocabulary | N4 | vocab | vocab_n4_core | manual | active | Core N4 vocabulary
n4_kanji_core | N4 Core Kanji | N4 | kanji | kanji_n4_core | manual | active | Core N4 kanji
n4_grammar_core | N4 Core Grammar | N4 | grammar | grammar_n4_core | manual | active | Core N4 grammar
n4_kaiwa_daily | N4 Daily Kaiwa | N4 | kaiwa | kaiwa_n4_daily | manual | active | Daily N4 conversation
```

### `vocab_n4_core`

Columns:

```text
item_id
level
deck_id
source_position
word
reading
meaning
hanviet
example_jp
example_vi
tags
status
```

### `kanji_n4_core`

Columns:

```text
item_id
level
deck_id
source_position
kanji
onyomi
kunyomi
hanviet
meaning
examples
memo
related_words
tags
status
```

`related_words` uses one entry per line in `word|reading|meaning_vi` format, for example:

```text
回す|まわす|xoay, vặn, chuyển
回る|まわる|xoay quanh, đi vòng quanh
回収|かいしゅう|thu hồi, thu gom
次回|じかい|lần sau, lần tiếp theo
遠回り|とおまわり|đi đường vòng, vòng vo
```

### `grammar_n4_core`

Columns:

```text
item_id
level
deck_id
source_position
pattern
meaning
usage
example_jp
example_vi
tags
status
```

### `kaiwa_n4_daily`

Columns:

```text
item_id
level
deck_id
source_position
title
dialogue_jp
dialogue_vi
vocab
grammar
shadowing
quiz
quiz_answer
tags
status
```

Only `deck_catalog.status=active` decks and item rows with `status=ready` are imported.

Learning item commands:

```text
/flash_settings
/flash_level N4
/flash_type vocab|kanji|grammar|kaiwa
/flash_deck n4_vocab_core
/flash_tags food,verb
```

Migration and import:

```powershell
docker compose run --rm bot python tools/migrate_flashcards_to_learning_items.py --default-deck-id n4_vocab_core
docker compose run --rm bot python tools/import_flashcards.py --model learning --all-decks --dry-run
docker compose run --rm bot python tools/import_flashcards.py --model learning --all-decks
```

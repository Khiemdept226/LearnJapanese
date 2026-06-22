# LearnJapanese

Telegram bot hoc tieng Nhat cho nguoi Viet. Du an hien co 2 luong chinh:

- Daily lessons: bot doc bai hoc tu Google Sheet va gui/xu ly cac lenh hoc moi ngay.
- N4 flashcards: bot hoc tu vung bang SQLite + SRS nhe, co import du lieu tu Google Sheet hoac PDF fallback.

Tai lieu nay la cua vao cho nguoi moi hoac AI agent khac. Doc file nay truoc, sau do doc cac file trong phan "Tai lieu nen doc".

## Trang thai hien tai

- Source code bot da co trong `src/`.
- May hien tai khong cai Python local. Khong gia dinh lenh `python` tren host chay duoc.
- Cach chay/test uu tien la Docker. Neu Docker Desktop chua bat engine, `docker compose ...` se loi ket noi pipe.
- Co the dev/sua code tai repo nay, nhung verification bang test can Docker hoac may khac co Python.
- Git repo chinh nam o `F:\PersonalProject\LearningLanguage\LearnJapanese`.

## Kien truc nhanh

```text
Telegram user
  -> python-telegram-bot handlers
  -> SQLite progress/review state
  -> Google Sheet lessons/flashcard source when needed
```

Thu muc quan trong:

```text
src/
  bot.py                    # entrypoint, dang ky handlers va schedulers
  config.py                 # env config
  db.py                     # SQLite users, sent lesson history, settings
  sheets.py                 # Google Sheet lesson reader
  handlers.py               # lesson commands
  scheduler.py              # daily lesson dispatch
  flashcards.py             # flashcard DB, SRS, stats, sessions
  flashcard_handlers.py     # Telegram flashcard commands/callbacks
  flashcard_scheduler.py    # daily flashcard reminder
  flashcard_sources/        # sheet/pdf adapters + validation

tools/
  import_flashcards.py      # import learning deck sheets, legacy Sheet/PDF fallback
  import_n4_pdf.py          # legacy PDF importer/parser

tests/                      # pytest tests, run in Docker or Python env
docs/                       # specs, deployment guide, source data notes
data/                       # SQLite DB, ignored/runtime data
credentials/                # Google service account JSON, ignored secret
```

## Bot commands

Daily lesson commands:

```text
/start      dang ky user va gioi thieu bot
/today      xem bai hien tai
/dich       xem ban dich
/tuvung     xem tu vung cua bai
/nguphap    xem ngu phap
/quiz       xem cau hoi
/dapan      xem dap an quiz
/shadowing  luyen noi
/next       chuyen bai tiep theo
/review     xem bai cu gan nhat da gui
```

Flashcard commands:

```text
/flash_start   bat dau flashcard N4
/flash         lay the uu tien: due truoc, new sau
/flash_new     chi lay the moi
/flash_review  chi lay the den han
/flash_stats   xem thong ke
/flash_goal    chon muc tieu hoc
/flash_reset   reset tien do flashcard cua user
/show          hien dap an
/again /hard /good /easy  cham diem the hien tai
```

Flashcard co inline buttons cho show answer, grade, next, stats, goal preset, reset confirm.

Typed learning lane commands:

```text
/neword          hoc tu moi
/vocab           alias cua /neword
/kanji           hoc kanji
/grammar         hoc ngu phap
/mix             hoc xen ke tu moi, kanji, ngu phap
/stats           thong ke tong
/stats_neword    thong ke tu moi
/stats_kanji     thong ke kanji
/stats_grammar   thong ke ngu phap
/goal_neword     chon goal tu moi
/goal_kanji      chon goal kanji
/goal_grammar    chon goal ngu phap
```

See `docs/learning-lanes-usage.md` for workflow and examples.

## Du lieu

Daily lessons doc tu Google Sheet dau tien (`sheet1`) trong spreadsheet `GOOGLE_SHEET_ID`. Schema goc nam trong `docs/mvp-telegram-google-sheet.md`.

Learning items mac dinh import tu `deck_catalog` va cac worksheet deck active (`vocab_n4_core`, `kanji_n4_core`, `grammar_n4_core`, `kaiwa_n4_daily`). Xem phan "Learning items deck model" ben duoi de biet schema tung worksheet.

Worksheet legacy `flashcards` chi dung cho fallback hoac migrate du lieu cu. Header legacy can co:

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

Chi row `status=ready` duoc import. PDF N4 van giu lam fallback legacy qua `tools/import_flashcards.py --model legacy --source pdf`.

## Runtime va config

File `.env` can co cac bien chinh:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google-service-account.json
GOOGLE_SERVICE_ACCOUNT_JSON=
TIMEZONE=Asia/Bangkok
DAILY_SEND_TIME=07:30
DATABASE_PATH=data/learningjp.sqlite3

FLASHCARD_ENABLED=true
FLASHCARD_DAILY_TIME=20:30
FLASHCARD_LEVEL=N4
FLASHCARD_TIMEZONE=Asia/Bangkok
FLASHCARD_IMPORT_SOURCE=sheet
FLASHCARD_SHEET_NAME=flashcards
```

Credential Google co 2 cach:

- File local: `credentials/google-service-account.json`
- Env JSON: `GOOGLE_SERVICE_ACCOUNT_JSON`

Khong commit `.env`, DB runtime, hoac credential.

## Lenh van hanh

Build Docker image:

```powershell
docker compose build
```

Chay bot:

```powershell
docker compose up -d
```

Xem log:

```powershell
docker compose logs -f bot
```

Run tests trong Docker:

```powershell
docker compose run --rm bot pytest -q
```

Import learning decks tu Google Sheet dry-run:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --model learning --all-decks --dry-run
```

Import learning decks that:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --model learning --all-decks
```

Legacy Sheet/PDF fallback:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --model legacy --source sheet --dry-run
docker compose run --rm bot python tools/import_flashcards.py --model legacy --source sheet
docker compose run --rm bot python tools/import_flashcards.py --model legacy --source pdf --dry-run
docker compose run --rm bot python tools/import_flashcards.py --model legacy --source pdf
```

## Tai lieu nen doc

- `docs/agent-handoff.md`: huong dan nhanh cho AI agent tiep quan du an.
- `docs/runtime-environment-memo.md`: quy uoc runtime tren may hien tai.
- `docs/docker-deployment-guide.md`: setup/deploy bang Docker.
- `docs/mvp-telegram-google-sheet.md`: thiet ke MVP daily lessons.
- `docs/flashcard-import-source-plan.md`: thiet ke import flashcards Sheet/PDF.
- `docs/superpowers/specs/`: specs da viet truoc do.
- `docs/superpowers/plans/`: implementation plans da dung truoc do.

## Nguyen tac khi sua tiep

- Doc `docs/agent-handoff.md` truoc khi sua lon.
- Khong yeu cau cai Python tren may hien tai.
- Dung Docker de test neu Docker Desktop engine dang chay.
- Giu progress user trong SQLite, tranh schema migration lon neu khong can.
- Sheet/PDF import chi sync card master data; tien do hoc nam trong SQLite review/session tables.
- Khi sua logic flashcard, chay targeted tests lien quan truoc, sau do full `pytest` trong Docker.

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

# Agent Handoff: LearnJapanese

File nay danh cho AI agent hoac developer moi tiep quan du an. Muc tieu la hieu nhanh context, khong lap lai cac sai lam runtime, va biet file nao can doc truoc.

## Doc theo thu tu nay

1. `README.md`
2. `docs/runtime-environment-memo.md`
3. `docs/docker-deployment-guide.md`
4. `docs/mvp-telegram-google-sheet.md`
5. `docs/flashcard-import-source-plan.md`
6. Code trong `src/` va `tools/` theo task can lam
7. Tests lien quan trong `tests/`

## Dieu can nho ngay

- May hien tai khong cai Python local. Dung Docker hoac may khac co Python de test.
- Khong goi user cai Python neu task khong bat buoc. Quy uoc da chot la khong cai Python tren host nay.
- Docker Desktop co the chua bat engine. Neu `docker compose` loi pipe `dockerDesktopLinuxEngine`, do la Docker engine chua chay.
- `.env` va `credentials/` la secret/runtime local, khong commit.
- Git worktree co the co file user tao. Kiem tra `git status --short` truoc khi sua.

## Muc tieu du an

Bot Telegram ho tro hoc tieng Nhat cho nguoi Viet:

- Daily lessons: moi ngay gui bai hoc tu Google Sheet, co dich/tu vung/ngu phap/quiz/shadowing.
- Flashcards N4: hoc tu vung bang SRS nhe, co inline buttons, stats, goal presets, reset progress.
- Import flashcards: uu tien Google Sheet worksheet `flashcards`, PDF N4 la fallback.

## Luong runtime

`src/bot.py` la entrypoint:

1. `validate_config()` doc `.env`.
2. `init_db()` tao bang core va flashcard tables.
3. Tao `python-telegram-bot` Application.
4. Dang ky lesson handlers va flashcard handlers.
5. Dang ky daily lesson scheduler.
6. Neu `FLASHCARD_ENABLED=true`, dang ky daily flashcard reminder.
7. Chay polling.

## Modules chinh

| File | Vai tro |
|---|---|
| `src/config.py` | Doc env config. |
| `src/db.py` | SQLite users, sent lessons, settings; goi init flashcards. |
| `src/sheets.py` | Google Sheets client va lesson reader. |
| `src/handlers.py` | Daily lesson Telegram commands. |
| `src/scheduler.py` | Gui lesson hang ngay cho users. |
| `src/flashcards.py` | Flashcard schema, upsert, SRS grade, stats, sessions, settings. |
| `src/flashcard_handlers.py` | Flashcard commands, inline callbacks, message formatting. |
| `src/flashcard_scheduler.py` | Flashcard daily reminder va pick card. |
| `src/flashcard_sources/validation.py` | Normalize/validate rows tu Sheet/PDF. |
| `src/flashcard_sources/sheet_source.py` | Load flashcard rows tu worksheet `flashcards`. |
| `src/flashcard_sources/pdf_source.py` | Wrap legacy PDF parser thanh source adapter. |
| `tools/import_flashcards.py` | CLI import Sheet/PDF vao SQLite. |
| `tools/import_n4_pdf.py` | Legacy parser/importer cho PDF N4. |

## SQLite data model nhanh

Core lesson tables:

- `users`: Telegram user, chat id, current lesson order.
- `sent_lessons`: lesson da gui.
- `settings`: key/value chung.

Flashcard tables:

- `flashcards`: master card data, unique by `(level, source, word, reading)`.
- `user_flashcard_reviews`: SRS state per user/card.
- `user_flashcard_sessions`: current pending card per user.
- `user_flashcard_settings`: goal preset/limits per user.

Import Sheet/PDF chi ghi `flashcards`. Tien do hoc cua user nam o 3 bang user flashcard, nen can can than khi sua schema.

## Google Sheet assumptions

Daily lessons:

- Dung `GOOGLE_SHEET_ID`.
- `src/sheets.py` doc `sheet1`.
- Chi lesson `status=ready`.
- `order` la thu tu gui.

Flashcards:

- Dung cung `GOOGLE_SHEET_ID`.
- Worksheet mac dinh: `FLASHCARD_SHEET_NAME=flashcards`.
- Chi row `status=ready`.
- Validation skip row thieu `level`, `source_position`, `word`, hoac `meaning`.
- Optional warning cho `reading`, `example_jp`, `example_vi`, `tags`.

## Lenh verification dung duoc khi Docker engine chay

Targeted tests:

```powershell
docker compose run --rm bot pytest tests/test_flashcards.py tests/test_flashcard_handlers.py -q
```

Import tests:

```powershell
docker compose run --rm bot pytest tests/test_flashcard_validation.py tests/test_flashcard_sheet_source.py tests/test_flashcard_pdf_source.py tests/test_import_flashcards.py -q
```

Full tests:

```powershell
docker compose run --rm bot pytest -q
```

Compile quick check:

```powershell
docker compose run --rm bot python -m py_compile src/bot.py src/flashcards.py src/flashcard_handlers.py src/flashcard_scheduler.py tools/import_flashcards.py tools/import_n4_pdf.py
```

## Viec nen tranh

- Dung `python` tren host hien tai de test. Host khong co Python theo quy uoc du an.
- Commit `.env`, `credentials/google-service-account.json`, DB runtime, hoac cache files.
- Reset/revert thay doi user tao neu khong duoc yeu cau.
- Doi unique key flashcards neu chua co migration va ly do ro.
- Xoa PDF import; no la fallback co chu dich.

## Roadmap gan

Nhung huong mo rong da duoc nhac trong docs/code:

- Lam sach/cap nhat Vietnamese text neu gap mojibake do terminal encoding.
- Them multi-level lesson/flashcard (`N5`, `N4`, `N3`) neu can.
- Nang flashcard schema bang `card_id`, `tags` trong DB sau khi Sheet on dinh.
- Cai thien inline UX cho daily lessons.
- Them OpenRouter/free AI fallback neu user muon hoi tu do.

## Khi bat dau task moi

1. Chay `git status --short`.
2. Doc file lien quan trong `src/`, `tools/`, `tests/`.
3. Neu task lien quan docs/runtime, doc `README.md` va file nay.
4. Sua nho, scoped theo module hien co.
5. Neu can verification ma Docker engine chua chay, bao ro chua chay duoc test vi Docker engine offline.

# Flashcard Import Source Plan

Muc tieu: giu ca 2 huong import tu vung flashcard:

- PDF: dung file PDF N4 hien tai de import nhanh hoac fallback.
- Sheet: dung tab Google Sheet/Excel-like de quan ly du lieu sach, de sua tay.

Bot van hoc tu SQLite nhu hien tai. PDF/Sheet chi la nguon sync du lieu the vao bang `flashcards`, khong luu tien do hoc.

## Trang thai hien tai

Ke hoach nay da duoc trien khai trong code hien tai:

- `src/flashcard_sources/validation.py`
- `src/flashcard_sources/sheet_source.py`
- `src/flashcard_sources/pdf_source.py`
- `tools/import_flashcards.py`
- tests lien quan trong `tests/`

SQLite hien tai van khong luu `card_id` va `tags`, nhung da co them cot `hanviet` trong bang `flashcards`.

## 1. Van de hien tai

PDF khong phai du lieu co cau truc. Khi extract text tu PDF, parser phai doan:

- dong nao la tu moi
- dong nao la cach doc
- dong nao la nghia
- dong nao la vi du tieng Nhat
- dong nao la dich tieng Viet
- dong nao la furigana can bo

Vi vay import tu PDF co rui ro sai vi du, thieu chu Han, hoac noi dong khong dung.

Google Sheet thi co schema ro rang hon, tuong tu cach bot dang doc lesson hien tai trong `src/sheets.py`.

## 2. Huong thiet ke

Them co che chon nguon import bang config hoac CLI option.

Config de xuat:

```env
FLASHCARD_IMPORT_SOURCE=sheet

# PDF source
FLASHCARD_PDF_PATH=docs/20250312140417_Tài liệu flash N4.pdf
FLASHCARD_PDF_LEVEL=N4
FLASHCARD_PDF_SOURCE=n4_pdf

# Sheet source
FLASHCARD_SHEET_NAME=flashcards
FLASHCARD_SHEET_LEVEL=N4
```

Doi source khi chay CLI:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source pdf
docker compose run --rm bot python tools/import_flashcards.py --source sheet
```

Neu khong truyen `--source`, tool doc tu:

```env
FLASHCARD_IMPORT_SOURCE=sheet
```

## 3. Kien truc de xuat

Them source adapters:

```text
src/flashcard_sources/
  __init__.py
  pdf_source.py
  sheet_source.py
  validation.py

tools/import_flashcards.py
```

Giu file legacy:

```text
tools/import_n4_pdf.py
```

`import_n4_pdf.py` co the giu lai de debug/fallback, hoac chuyen thanh wrapper goi:

```text
python tools/import_flashcards.py --source pdf
```

## 4. Interface chung

Moi source adapter nen tra ve list dict cung schema:

```python
{
    "card_id": "N4-0001",
    "level": "N4",
    "source": "n4_pdf",
    "source_position": 1,
    "word": "石",
    "reading": "いし",
    "meaning": "Đá",
    "hanviet": "Thach",
    "example_jp": "一番大きいピラミッドをつくるのに石が270万個も使われました。",
    "example_vi": "270 vạn khối đá đã được sử dụng...",
    "tags": "noun,kanji",
    "status": "ready",
}
```

SQLite hien tai da co cot `hanviet`, nhung chua bat buoc `card_id` va `tags`. Co 2 lua chon:

### Option A: Khong doi schema SQLite ngay

Map vao bang hien tai:

```text
level
source
source_position
word
reading
meaning
hanviet
example_jp
example_vi
```

`card_id`, `tags`, `status` chi dung trong sync/validation.

Uu diem: it rui ro, khong dung tien do hoc hien tai.

### Option B: Them cot `card_id`, `tags`

Them migration nhe:

```text
ALTER TABLE flashcards ADD COLUMN card_id TEXT
ALTER TABLE flashcards ADD COLUMN tags TEXT
```

Sau do unique nen chuyen dan sang:

```text
UNIQUE(level, source, card_id)
```

Uu diem: quan ly the on dinh hon.
Nhuoc diem: can migration can than de khong anh huong DB da hoc.

Khuyen dung Option A truoc. Khi on dinh moi them `card_id`/`tags` vao DB.

## 5. Google Sheet schema

Tao tab:

```text
flashcards
```

Header:

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

Vi du row:

| card_id | level | source | source_position | word | reading | meaning | hanviet | example_jp | example_vi | tags | status |
|---|---|---|---:|---|---|---|---|---|---|---|---|
| N4-0001 | N4 | n4_pdf | 1 | 石 | いし | Đá | Thach | 一番大きいピラミッドをつくるのに石が270万個も使われました。 | 270 vạn khối đá đã được sử dụng để xây lên Kim tự tháp lớn nhất. | noun,kanji | ready |

Chi sync row:

```text
status = ready
```

## 6. Import flow moi

```text
import_flashcards.py
-> doc source tu CLI/env
-> source=pdf: goi pdf_source.load_flashcards()
-> source=sheet: goi sheet_source.load_flashcards()
-> validation.validate_rows()
-> flashcards.upsert_flashcards()
-> print summary
```

Output thong nhat:

```text
Source: sheet
Fetched: 219
Ready: 219
Imported: 219
Skipped: 0
Warnings: 0
```

Dry-run:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source sheet --dry-run
```

Import that:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source sheet
```

PDF fallback:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source pdf --dry-run
docker compose run --rm bot python tools/import_flashcards.py --source pdf
```

## 7. Validation rules

Skip row va bao warning neu:

- thieu `word`
- thieu `meaning`
- `source_position` khong phai so
- `level` rong
- `status` khac `ready`

Warning nhung van import neu:

- thieu `reading`
- thieu `example_jp`
- thieu `example_vi`
- thieu `tags`

Duplicate handling:

- Trong phase dau, dung unique hien tai: `level + source + word + reading`.
- Neu cung key xuat hien nhieu lan trong source, lay row sau cung va warning duplicate.

## 8. File can sua/them khi trien khai

Them:

```text
src/flashcard_sources/__init__.py
src/flashcard_sources/pdf_source.py
src/flashcard_sources/sheet_source.py
src/flashcard_sources/validation.py
tools/import_flashcards.py
tests/test_flashcard_sheet_source.py
tests/test_import_flashcards.py
```

Sua:

```text
src/config.py
.env.example
tools/import_n4_pdf.py
docs/docker-deployment-guide.md
```

Co the sua sau neu chon them schema:

```text
src/flashcards.py
```

## 9. TDD plan

### Task 1: Validation layer

Tests:

- valid row duoc normalize dung schema.
- row thieu `word` bi skip.
- row `status=draft` bi skip.
- `source_position` string `"1"` duoc convert thanh int.

### Task 2: Sheet source

Tests:

- input records tu gspread `get_all_records()` duoc normalize thanh flashcard rows.
- chi lay `status=ready`.
- sort theo `source_position`.

### Task 3: PDF source adapter

Tests:

- sample PDF text hien tai van parse ra `石`, `経験`, `店員`.
- adapter tra ve cung schema voi sheet source.

### Task 4: Unified import CLI

Tests:

- `--source sheet` goi sheet source.
- `--source pdf` goi pdf source.
- `--dry-run` khong ghi SQLite.
- summary output dung.

### Task 5: Docs

Update:

- `docs/docker-deployment-guide.md`
- them section import tu Sheet.
- giu section import tu PDF nhu fallback.

## 10. Rollout de xuat

1. Tao tab `flashcards` trong Google Sheet.
2. Paste header schema.
3. Dua du lieu N4 tu PDF/parser hien tai len sheet.
4. Sua tay cac row loi trong sheet.
5. Chay:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source sheet --dry-run
```

6. Neu summary sach, chay import that:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source sheet
```

7. Bot van chay nhu cu:

```powershell
docker compose up -d
```

## 11. Quyet dinh khuyen dung

Khong bo PDF.

Mac dinh nen dung:

```env
FLASHCARD_IMPORT_SOURCE=sheet
```

PDF giu lam fallback:

```powershell
docker compose run --rm bot python tools/import_flashcards.py --source pdf
```

Cach nay vua co du lieu sach de hoc hang ngay, vua khong mat kha nang import nhanh tu PDF khi can.

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
tags
status
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

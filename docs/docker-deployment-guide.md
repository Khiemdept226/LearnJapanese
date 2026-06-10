# Docker Deployment Guide

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

Chay dry-run truoc:

```powershell
docker compose run --rm bot python tools/import_n4_pdf.py --dry-run
```

Ket qua mong doi:

```text
Parsed: 219
Imported: 0
First card: 石 いし Đá
```

Import that vao SQLite:

```powershell
docker compose run --rm bot python tools/import_n4_pdf.py
```

Ket qua mong doi:

```text
Parsed: 219
Imported: 219
First card: 石 いし Đá
```

Neu gap `sqlite3.OperationalError: disk I/O error`, dung bot truoc va xoa journal tam:

```powershell
docker compose down
Remove-Item .\data\learningjp.sqlite3-journal -Force -ErrorAction SilentlyContinue
docker compose run --rm bot python tools/import_n4_pdf.py
```

## 7. Chay tests

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

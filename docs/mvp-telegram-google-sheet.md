# MVP: Telegram Bot Hoc Tieng Nhat Tu Google Sheet

## 1. Muc tieu

Xay mot Telegram bot giup hoc tieng Nhat moi ngay ma khong can AI API realtime.

Bot se:

- Doc noi dung bai hoc tu Google Sheet.
- Gui 1 bai hoi thoai moi ngay cho nguoi hoc.
- Cho nguoi hoc dung lenh de xem dich, tu vung, ngu phap, quiz, dap an.
- Luu tien do hoc cua tung Telegram user.

Nguon tao noi dung:

```text
YouTube / bai hoc co san -> NotebookLM / Gemini Pro -> tao bai hoc truoc -> luu Google Sheet
Telegram bot -> doc Sheet -> gui va tra loi theo menu
```

## 2. Pham vi MVP

Co trong MVP:

- Dang ky user bang `/start`.
- Gui bai hom nay bang `/today`.
- Gui bai moi moi ngay theo lich.
- Cac lenh hoc:
  - `/dich`
  - `/tuvung`
  - `/nguphap`
  - `/quiz`
  - `/dapan`
  - `/next`
  - `/review`
- Luu user, bai hien tai, lich su bai da gui bang SQLite.

Chua co trong MVP:

- Chat AI tu do.
- Tao bai hoc tu dong bang API.
- Thanh toan/user subscription.
- Dashboard web.
- Multi-language UI nang cao.

## 3. Stack de xuat

Ngon ngu:

```text
Python 3.11+
```

Thu vien:

```text
python-telegram-bot
APScheduler
gspread
google-auth
python-dotenv
```

Database:

```text
SQLite
```

Ly do chon Python:

- Bot logic gon.
- Doc Google Sheet de.
- Scheduler de.
- De mo rong neu sau nay xu ly text tieng Nhat, CSV, export.

## 4. Cau truc thu muc

```text
LearningJP/
  docs/
    mvp-telegram-google-sheet.md
  src/
    bot.py
    config.py
    db.py
    sheets.py
    scheduler.py
    handlers.py
  data/
    learningjp.sqlite3
  credentials/
    google-service-account.json
  .env
  requirements.txt
  README.md
```

Mo ta:

| File | Vai tro |
|---|---|
| `src/bot.py` | entrypoint chay Telegram bot |
| `src/config.py` | doc bien moi truong |
| `src/db.py` | SQLite: user, progress, sent history |
| `src/sheets.py` | doc lesson tu Google Sheet |
| `src/scheduler.py` | gui bai hoc hang ngay |
| `src/handlers.py` | xu ly command Telegram |
| `data/learningjp.sqlite3` | database local |
| `credentials/google-service-account.json` | credential Google Sheets |
| `.env` | token va config rieng |

## 5. Google Sheet Schema

Tao Google Sheet ten vi du:

```text
LearningJP Lessons
```

Sheet/tab dau tien nen dat ten:

```text
lessons
```

Header dong 1:

| Column | Bat buoc | Vi du | Ghi chu |
|---|---:|---|---|
| `lesson_id` | yes | `N5-001` | Ma bai duy nhat |
| `level` | yes | `N5` | N5/N4/N3 |
| `title` | yes | `Chao hoi buoi sang` | Tieu de ngan |
| `dialogue_jp` | yes | `A: おはようございます...` | Hoi thoai tieng Nhat |
| `dialogue_vi` | yes | `A: Chao buoi sang...` | Ban dich tieng Viet |
| `vocab` | yes | `おはよう = chao buoi sang` | Co the xuong dong |
| `grammar` | yes | `は: tro tu chu de` | Giai thich ngu phap |
| `quiz` | yes | `今日は寒いですか？` | Cau hoi luyen tap |
| `quiz_answer` | yes | `はい、寒いです。` | Dap an |
| `shadowing` | no | `今日は寒いですね。` | Cau doc lap lai |
| `status` | yes | `ready` | Chi gui bai `ready` |
| `order` | yes | `1` | Thu tu gui bai |

Nguyen tac:

- Chi bot doc lesson co `status = ready`.
- `order` dung de gui bai tiep theo.
- Khong sua `lesson_id` sau khi da gui.

## 6. Prompt tao bai bang Gemini Pro

Dung prompt nay de tao tung batch 7-30 bai:

```text
Hay tao 30 bai hoi thoai tieng Nhat cap do N5 cho nguoi Viet hoc moi ngay.

Moi bai gom:
- lesson_id: N5-001 den N5-030
- level
- title
- dialogue_jp: hoi thoai 4-6 cau, tu nhien, dung kanji it, co kana
- dialogue_vi: dich tieng Viet tu nhien
- vocab: 5-8 tu/cum tu quan trong, moi dong dang "JP = VI"
- grammar: 1-2 diem ngu phap, giai thich ngan bang tieng Viet
- quiz: 2 cau hoi ngan bang tieng Nhat hoac tieng Viet
- quiz_answer: dap an
- shadowing: 2 cau nen luyen doc lai
- status: ready
- order: so thu tu

Tra ve dang bang de copy vao Google Sheet.
Chu de bai hoc nen gan voi doi song: chao hoi, an uong, cong viec, mua sam, hoi duong, thoi tiet, lich hen.
```

## 6.1. Tao nguon hoc tu YouTube + NotebookLM/Gemini

Co the dung YouTube lam nguon dau vao thay vi de Gemini tao bai tu dau.

Workflow:

```text
YouTube link
  -> NotebookLM / Gemini Pro doc va tom tat video
  -> Rut chu de, tu vung, ngu phap, mau cau
  -> Gemini Pro format thanh bang dung schema
  -> Copy vao Google Sheet
  -> Telegram bot gui moi ngay
```

Khi nao nen dung cach nay:

- Video co transcript/caption ro.
- Video la hoi thoai tieng Nhat doi song.
- Video la bai giang ngu phap, tu vung, nghe hieu.
- Muon bai hoc bam theo nguon that thay vi noi dung tao moi hoan toan.

Luu y:

- Khong chep nguyen van dai tu video.
- Nen bien noi dung thanh bai hoc moi: hoi thoai ngan, tu vung, grammar, quiz.
- Video qua dai nen chia thanh nhieu source hoac tao it bai hon.
- Neu transcript sai, can sua lai truoc khi dua vao Sheet.
- Nen review thu cong truoc khi dat `status = ready`.

Prompt cho 1 video/source:

```text
Du tren video/source nay, hay tao bai hoc tieng Nhat cho nguoi Viet.

Yeu cau:
- Khong chep nguyen van dai tu video.
- Tom tat y chinh cua video.
- Rut ra tu vung, mau cau, ngu phap huu ich.
- Tao lai mot doan hoi thoai ngan moi dua tren chu de video.
- Cap do: N5
- Output theo bang voi cac cot:

lesson_id | level | title | dialogue_jp | dialogue_vi | vocab | grammar | quiz | quiz_answer | shadowing | status | order

Moi bai 1 dong.
Tao 5 bai hoc tu source nay.
status luon la ready.
order bat dau tu 1.
```

Prompt cho nhieu video/source trong NotebookLM:

```text
Tong hop cac source YouTube trong notebook nay thanh 30 bai hoc tieng Nhat cap do N5 cho nguoi Viet.

Moi bai phai co:
- lesson_id: N5-001 den N5-030
- level
- title
- dialogue_jp: hoi thoai 4-6 cau, tu nhien, phu hop N5
- dialogue_vi: dich tieng Viet tu nhien
- vocab: 5-8 tu/cum tu quan trong, moi dong dang "JP = VI"
- grammar: 1-2 diem ngu phap, giai thich ngan bang tieng Viet
- quiz: 2 cau hoi ngan
- quiz_answer: dap an
- shadowing: 2 cau nen luyen doc lai
- status: ready
- order: so thu tu

Khong chep nguyen van dai tu video. Hay viet lai thanh bai hoc moi, tu nhien, de hoc moi ngay.
Xuat thanh bang Google Sheet-ready voi dung cac cot:
lesson_id | level | title | dialogue_jp | dialogue_vi | vocab | grammar | quiz | quiz_answer | shadowing | status | order
```

Quy trinh review truoc khi dua vao bot:

1. Copy bang tu Gemini/NotebookLM vao Google Sheet.
2. Doc nhanh tung row, sua loi tieng Nhat hoac loi dich.
3. De `status = draft` voi bai chua chac.
4. Chi bai da kiem tra moi dat `status = ready`.
5. Bot chi gui cac bai `ready`.

## 7. Telegram Commands

| Command | Hanh vi |
|---|---|
| `/start` | Tao user neu chua co, gui huong dan ngan |
| `/today` | Gui lai bai hien tai |
| `/dich` | Gui `dialogue_vi` cua bai hien tai |
| `/tuvung` | Gui `vocab` cua bai hien tai |
| `/nguphap` | Gui `grammar` cua bai hien tai |
| `/quiz` | Gui `quiz` cua bai hien tai |
| `/dapan` | Gui `quiz_answer` cua bai hien tai |
| `/shadowing` | Gui `shadowing` cua bai hien tai |
| `/next` | Chuyen sang bai tiep theo va gui bai |
| `/review` | Gui mot bai cu gan nhat de on lai |

Tin nhan bai hoc mau:

```text
Bai hom nay: N5-001 - Chao hoi buoi sang

A: おはようございます。
B: おはようございます。今日は寒いですね。
A: そうですね。

Chon lenh:
/dich - ban dich
/tuvung - tu vung
/nguphap - ngu phap
/quiz - cau hoi
/shadowing - luyen noi
```

## 8. Database Schema

Bang `users`:

| Column | Type | Ghi chu |
|---|---|---|
| `telegram_user_id` | INTEGER PRIMARY KEY | ID Telegram |
| `chat_id` | INTEGER | chat ID de gui tin |
| `username` | TEXT | username neu co |
| `current_lesson_order` | INTEGER | bai hien tai |
| `created_at` | TEXT | ISO datetime |
| `updated_at` | TEXT | ISO datetime |

Bang `sent_lessons`:

| Column | Type | Ghi chu |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | row id |
| `telegram_user_id` | INTEGER | user |
| `lesson_id` | TEXT | lesson da gui |
| `sent_at` | TEXT | ISO datetime |

Bang `settings`:

| Column | Type | Ghi chu |
|---|---|---|
| `key` | TEXT PRIMARY KEY | ten setting |
| `value` | TEXT | gia tri |

## 9. Scheduler

MVP dung polling + scheduler trong cung process.

Lich gui:

```text
Moi ngay 07:30 Asia/Bangkok
```

Logic:

1. Lay danh sach user da `/start`.
2. Voi moi user, lay `current_lesson_order`.
3. Lay lesson co `order = current_lesson_order` va `status = ready`.
4. Gui lesson vao Telegram.
5. Ghi `sent_lessons`.
6. Tang `current_lesson_order` len 1.

Neu het bai:

- Gui thong bao het bai.
- Goi y dung `/review`.
- Khong tang nua.

## 10. Env Config

File `.env`:

```text
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google-service-account.json
TIMEZONE=Asia/Bangkok
DAILY_SEND_TIME=07:30
DATABASE_PATH=data/learningjp.sqlite3
```

Khong commit `.env` va `credentials/google-service-account.json`.

## 11. Setup Telegram Bot

1. Mo Telegram, chat voi `@BotFather`.
2. Chay `/newbot`.
3. Dat ten bot.
4. Lay `TELEGRAM_BOT_TOKEN`.
5. Dua token vao `.env`.

## 12. Setup Google Sheet API

1. Tao Google Cloud project.
2. Enable Google Sheets API.
3. Tao Service Account.
4. Tao JSON key.
5. Luu file vao:

```text
credentials/google-service-account.json
```

6. Mo Google Sheet.
7. Share Sheet cho email service account, quyen Viewer hoac Editor.
8. Copy Sheet ID vao `.env`.

Sheet ID nam trong URL:

```text
https://docs.google.com/spreadsheets/d/<GOOGLE_SHEET_ID>/edit
```

## 13. Luong xu ly command

`/start`:

```text
if user not exists:
  create user with current_lesson_order = first ready lesson order
send welcome + /today hint
```

`/today`:

```text
lesson = get current lesson from db + sheet
send dialogue_jp + command menu
```

`/dich`, `/tuvung`, `/nguphap`, `/quiz`, `/dapan`, `/shadowing`:

```text
lesson = get current lesson
send corresponding field
```

`/next`:

```text
increment current_lesson_order
send new lesson
```

`/review`:

```text
pick latest sent lesson before current lesson
send dialogue_jp + menu
```

## 14. Error Handling

Google Sheet loi:

- Gui tin ngan: `Hien tai khong doc duoc bai hoc. Thu lai sau.`
- Log error vao console.

Lesson thieu field:

- Bo qua lesson neu field bat buoc rong.
- Nen co script validate Sheet sau nay.

User chua `/start` ma goi command:

- Tao user tu dong.
- Gui bai dau tien.

Scheduler gui loi cho mot user:

- Log user id va loi.
- Tiep tuc user tiep theo.

## 15. Test MVP

Manual test:

1. Chay bot local.
2. Gui `/start`.
3. Gui `/today`.
4. Gui `/dich`, `/tuvung`, `/nguphap`, `/quiz`, `/dapan`.
5. Gui `/next`.
6. Tam thoi dat scheduler chay sau 1-2 phut de test daily send.
7. Tat bot, bat lai, kiem tra user progress van con.

Test data toi thieu:

- 3 lesson `ready`.
- 1 lesson `draft` de dam bao bot khong gui.
- 1 user Telegram.

## 16. Roadmap Sau MVP

Mo rong 1: Nut bam inline keyboard

- Thay vi go lenh, hien button:
  - Dich
  - Tu vung
  - Ngu phap
  - Quiz
  - Next

Mo rong 2: OpenRouter free fallback

- Khi user hoi tu do, goi OpenRouter free model.
- Neu het quota, tra loi: `Ban co the dung /nguphap hoac /tuvung de xem noi dung co san.`

Mo rong 3: Multi-level

- User chon level bang `/level N5` hoac `/level N4`.
- Bot gui lesson theo level.

Mo rong 4: Spaced repetition

- Luu tu vung sai/dung.
- Gui lai tu can on sau 1, 3, 7 ngay.

## 17. Tieu chi MVP thanh cong

MVP thanh cong khi:

- Bot gui duoc 1 bai hoc moi ngay.
- User doc duoc bai hien tai bang `/today`.
- User xem duoc dich, tu vung, ngu phap, quiz, dap an.
- Bot khong can AI API.
- Progress user khong mat khi restart bot.

# Memo: Runtime Environment

## Quyet dinh hien tai

Khong cai Python local tren may hien tai.

Ly do:

- May nay duoc dung nhu workspace chinh de doc/sua repo, khong phai Python runtime chinh.
- Tranh lam nang moi truong host va tranh phu thuoc vao Python global.
- Du an da co `Dockerfile`, `docker-compose.yml`, `requirements.txt`, source code, tests, va docs deploy.
- Neu can test/chay that tren may nay, uu tien Docker. Neu can debug nhanh bang Python local, dung may nha co Python.

## Trang thai du an hien tai

Khac voi memo cu, repo bay gio da co source code bot day du:

- `src/bot.py`: entrypoint Telegram bot.
- `src/handlers.py`: daily lesson commands.
- `src/flashcard_handlers.py`: flashcard commands va callback buttons.
- `src/flashcards.py`: SQLite flashcard/SRS logic.
- `tools/import_flashcards.py`: import flashcards tu Sheet/PDF.
- `tests/`: pytest suite.

Do do, khong nen coi repo nay la "chi co tai lieu" nua.

## Cach chay khuyen dung tren may hien tai

Dung Docker khi Docker Desktop/Engine dang chay:

```powershell
docker compose build
docker compose run --rm bot pytest -q
docker compose up -d
```

Neu gap loi dang nay:

```text
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified
```

Nghia la Docker CLI co, nhung Docker Desktop engine chua chay. Bat Docker Desktop roi chay lai lenh.

## Cach chay tren may nha co Python

Dung khi can dev nhanh/debug truc tiep:

```powershell
git clone git@github-personal:Khiemdept226/LearnJapanese.git
cd LearnJapanese
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
python src/bot.py
```

Can file `.env` va Google credential hop le truoc khi chay bot.

## Config runtime

Bot doc `.env` bang `python-dotenv`. Cac bien quan trong:

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

Credential Google co the nam o file `credentials/google-service-account.json` hoac env `GOOGLE_SERVICE_ACCOUNT_JSON`.

## Verification policy

- Khong chay `python` tren host hien tai de verify vi host khong co Python theo quy uoc.
- Neu Docker engine dang chay, dung `docker compose run --rm bot pytest -q`.
- Neu Docker engine khong chay, ghi ro verification bi chan boi Docker engine offline.
- Co the doc/grep/compile tinh than bang repo files, nhung khong coi do la test suite pass.

## Ket luan

May hien tai: sua code/docs duoc, test/chay bang Docker neu engine bat.

May nha: co the dung Python local voi virtualenv.

Du an: da co bot source, import tools, tests, Docker setup, va docs handoff. Agent moi nen doc `README.md` va `docs/agent-handoff.md` truoc khi lam viec.

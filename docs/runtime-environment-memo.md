# Memo: Runtime Environment

## Quyet dinh

Khong can cai Python tren may hien tai.

Ly do:

- Repo hien tai moi co tai lieu, chua co source code bot de chay.
- Cai Python tren may nay khong can thiet va co the lam nang moi truong.
- May nha da co Python, phu hop hon de clone repo ve va chay thu khi co code.

## Huong chay sau nay

Co 2 huong chay du an.

### 1. Chay bang Python local tren may nha

Dung khi can dev nhanh va debug truc tiep.

Lenh du kien:

```powershell
git clone git@github-personal:Khiemdept226/LearnJapanese.git
cd LearnJapanese
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Sau do chay bot theo entrypoint cua source code khi duoc them vao repo.

### 2. Chay bang Docker

Dung khi muon moi truong gon, de deploy, khong can cai Python truc tiep tren may host.

Lenh du kien:

```powershell
docker compose up -d
```

Can them cac file sau khi co source code:

- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`
- source code bot
- `.env` tren may chay, khong commit len repo

## Ket luan

Trong giai do hien tai, khong cai them Python tren may nay.

Khi co source code bot, uu tien chay thu tren may nha bang Python local. Neu can deploy on dinh hoac tranh cai runtime tren host, chuyen sang Docker.

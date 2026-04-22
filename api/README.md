# NEO Labs API

Backend สำหรับ NEO Labs autonomous multi-agent web app

## Setup (ครั้งแรก)

```bash
cd api

# สร้าง virtual environment
python3 -m venv venv
source venv/bin/activate

# ติดตั้ง dependencies
pip install -r requirements.txt

# ตั้งค่า environment variables
cp .env.example .env
# แก้ไข .env ใส่ ANTHROPIC_API_KEY จริง
```

## Run

```bash
# activate venv ถ้ายังไม่ได้ทำ
source venv/bin/activate

# start server (auto-reload)
uvicorn main:app --reload --port 8000
```

เปิด browser: http://localhost:8000/health
ดู API docs: http://localhost:8000/docs

## Endpoints (Phase 1)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Root info |
| GET | `/health` | Health check + API key loaded check |

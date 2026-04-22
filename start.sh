#!/bin/bash
# NEO Labs — one-command start
# Usage: ./start.sh

cd "$(dirname "$0")/api" || exit 1

echo "◆ NEO LABS — Starting..."

# เช็คว่า .env มี API key หรือยัง
if [ ! -f .env ] || ! grep -q "sk-ant-" .env 2>/dev/null; then
  echo "⚠️  ไม่พบ ANTHROPIC_API_KEY ใน api/.env"
  echo "    แก้โดยรัน: echo 'ANTHROPIC_API_KEY=sk-ant-xxx' > api/.env"
  exit 1
fi

# เปิด browser ก่อน (เปิด 2 วินาทีหลัง server boot)
(sleep 2 && open ../neo-labs-office.html) &

# activate venv + รัน uvicorn
source venv/bin/activate
echo "◆ Server: http://localhost:8000"
echo "◆ กด Ctrl+C เพื่อปิด"
echo ""
uvicorn main:app --port 8000 --reload

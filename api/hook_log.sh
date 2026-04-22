#!/bin/bash
# Claude Code hook — ทุกครั้งที่ Agent tool ถูกเรียก ส่ง agent + คำตอบจริงไป /log
# ใช้ /dev/stdin เพื่อส่ง JSON input ไปให้ python ปลอดภัย (ไม่มี shell escaping risk)
python3 /Users/akkarawin/Desktop/NewClaude/api/hook_log.py

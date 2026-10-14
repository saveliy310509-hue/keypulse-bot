@echo off
chcp 65001 > nul
title KeyPulse Server
echo ======================================================
echo    Запуск сервера лицензий KeyPulse...
echo    Панель управления будет доступна по адресу:
echo    http://127.0.0.1:8000
echo ======================================================
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
pause

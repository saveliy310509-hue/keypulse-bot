@echo off
chcp 65001 > nul
title KeyPulse Launcher

echo ==============================================================
echo    Запуск Сервера Лицензий и Telegram Бота KeyPulse...
echo ==============================================================

start "KeyPulse Web Server (http://127.0.0.1:8000)" cmd /k "python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000"
start "KeyPulse Telegram Bot" cmd /k "python bot.py"

echo.
echo [+] Сервер запущен: http://127.0.0.1:8000
echo [+] Telegram Бот запущен в фоновом окне.
echo.
pause

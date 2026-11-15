@echo off
chcp 65001 >nul
title Universal Music & Media Bot
echo ====================================================
echo   Universal Music & Media Downloader Bot (Aiogram 3)
echo ====================================================
echo.

cd /d "%~dp0"

if not exist "venv" (
    echo [1/3] Virtual muhit yaratilmoqda...
    python -m venv venv
)

echo [2/3] Kerakli kutubxonalar tekshirilmoqda / o'rnatilmoqda...
call venv\Scripts\activate
pip install -r requirements.txt

echo.
echo [3/3] Bot ishga tushirilmoqda...
python bot.py
pause

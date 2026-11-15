import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

raw_admins = os.getenv("ADMIN_IDS", "")
SUPER_ADMIN_IDS = [
    int(x.strip()) for x in raw_admins.split(",") if x.strip().isdigit()
]

DB_PATH = str(BASE_DIR / os.getenv("DB_PATH", "bot_database.db"))
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Doimiy papka (masalan Railway Volume) bo'lsa, u yerni avtomatik yaratamiz
try:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

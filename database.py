import aiosqlite
from typing import List, Dict, Any, Optional
from config import DB_PATH, SUPER_ADMIN_IDS


DEFAULT_SETTINGS = {
    "welcome_text": (
        "👋 <b>Assalomu alaykum, {name}!</b>\n\n"
        "🎵 <b>Universal Media & Music Bot</b>ga xush kelibsiz!\n\n"
        "🔹 Qo'shiq yoki ijrochi nomini yozing — darhol topib beramiz.\n"
        "🔹 <b>Instagram, TikTok, YouTube</b> linkini yuboring — video va MP3 audiosini yuklab beramiz!\n"
        "🔹 Pastdagi menyular orqali 15+ qo'shimcha xizmatlarimizdan foydalaning."
    ),
    "help_text": (
        "🆘 <b>Yordam va Qo'llanma:</b>\n\n"
        "1️⃣ <b>Musiqa qidirish:</b> Istalgan qo'shiqchi yoki musiqa nomini yozib yuboring (masalan: <i>Konsta - Odamlar nima deydi</i>).\n"
        "2️⃣ <b>Video va Audio yuklash:</b> YouTube, Instagram (Reels/Post), TikTok linkini yuboring. Bot videoni ham, musiqasini ham tortib beradi.\n"
        "3️⃣ <b>Play-list (Sevimlilar):</b> Yoqqan qo'shiqlaringiz ostidagi ❤️ tugmasini bosib shaxsiy pleylistingizga saqlang.\n"
        "4️⃣ <b>Telegram Premium:</b> Arzon va ishonchli narxlarda Premium xarid qiling va chekni adminga yuboring.\n"
        "5️⃣ <b>Adminga bog'lanish:</b> Savol, taklif yoki reklama bo'yicha to'g'ridan-to'g'ri bot ichidan adminga yozing."
    ),
    "location_title": "📍 <b>Bizning manzil:</b>\n🏢 Toshkent sh., Yunusobod tumani, IT Markaz binosi, 3-qavat.\n🕘 Ish vaqti: 09:00 - 20:00",
    "location_lat": "41.311081",
    "location_lon": "69.240562",
    "contacts_text": (
        "📞 <b>Biz bilan bog'lanish va Reklama:</b>\n\n"
        "📢 <b>Reklama va hamkorlik uchun:</b> @jorayevvbb\n"
        "👨‍💻 <b>Admin profili:</b> <a href='https://t.me/jorayevvbb'>@jorayevvbb</a>\n\n"
        "✍️ <i>Shuningdek, pastdagi «✍️ Adminga bog'lanish» tugmasi orqali bot ichidan ham to'g'ridan-to'g'ri yozishingiz mumkin!</i>"
    ),
    "ads_text": (
        "📢 <b>Botda Reklama va Hamkorlik Bo'limi!</b>\n\n"
        "Botimizda o'z kanal, guruh, mahsulot yoki xizmatlaringizni reklama qilmoqchimisiz?\n"
        "Yoki majburiy obunaga kanalingizni ulamoqchimisiz?\n\n"
        "👉 <b>Reklama bo'yicha murojaat qiling:</b> @jorayevvbb\n\n"
        "👇 <i>Pastdagi tugma orqali to'g'ridan-to'g'ri admin profiliga o'tishingiz mumkin:</i>"
    ),
    "premium_text": (
        "💎 <b>Telegram Premium va Stars Xizmati!</b>\n\n"
        "⚡ Rasmiy, kafolatlangan va tezkor ulab berish xizmati!\n\n"
        "💳 <b>To'lov rekvizitlari (Karta):</b>\n"
        "<code>4790 9122 1283 8579</code>\n"
        "👤 Qabul qiluvchi: <b>Munavvar Djurayeva</b>\n\n"
        "📌 <i>Pastdan o'zingizga mos tarifni tanlang, to'lov qiling va to'lov chekini (skrinshot) yuboring. Adminlarimiz 5-15 daqiqada ulab berishadi!</i>"
    ),
    "referral_reward": "500",
    "sub_required": "1",
    "about_text": (
        "ℹ️ <b>Bot haqida ma'lumot:</b>\n\n"
        "Ushbu bot orqali eng so'nggi xit taronalarni topishingiz, Instagram, TikTok va YouTube'dan suv belgisiz (watermark-free) video hamda MP3 yuklab olishingiz, "
        "o'quv kurslarimiz bilan tanishishingiz va Telegram Premium xarid qilishingiz mumkin."
    )
}

DEFAULT_COURSES = [
    (
        "🐍 Python & Telegram Bot (Aiogram 3)",
        "Noldan professional darajagacha Python dasturlash tili va murakkab Telegram botlar yasashni o'rganing. Amaliy loyihalar va sertifikat beriladi!",
        "500,000 so'm / oy",
        "3 oy (haftada 3 kun)"
    ),
    (
        "🌐 Full-Stack Web Dasturlash",
        "HTML, CSS, JavaScript, React hamda Backend (Python/Laravel) texnologiyalarini chuqur o'rganing.",
        "650,000 so'm / oy",
        "6 oy (haftada 3 kun)"
    ),
    (
        "🎬 Mobilografiya va SMM Pro",
        "Instagram, TikTok va YouTube uchun professional videolar olish, montaj qilish va sahifani rivojlantirish sirlari.",
        "450,000 so'm / oy",
        "2 oy"
    )
]

DEFAULT_TARIFFS = [
    ("💎 Telegram Premium — 3 oylik", "185,000 so'm", "Akkauntga kirmasdan (Gift orqali) rasmiy 3 oylik obuna."),
    ("💎 Telegram Premium — 6 oylik", "250,000 so'm", "Akkauntga kirmasdan (Gift orqali) rasmiy 6 oylik obuna."),
    ("💎 Telegram Premium — 12 oylik (1 yil)", "500,000 so'm", "Eng tejamkor yillik rasmiy Telegram Premium obunasi."),
    ("⭐ 100 Telegram Stars", "30,000 so'm", "Kanal va botlar uchun rasmiy Telegram yulduzlari."),
    ("⭐ 500 Telegram Stars", "140,000 so'm", "Kanal va botlar uchun rasmiy Telegram yulduzlari.")
]

DEFAULT_FAQS = [
    ("🎵 Musiqani qanday qidiraman?", "Shunchaki qo'shiqchi yoki qo'shiq nomini botga matn ko'rinishida yozib yuboring."),
    ("📥 Instagram va TikTok videoni qanday yuklayman?", "Video linkini (havolasini) nusxalab botga yuboring. Bot sizga videoni va uning MP3 musiqasini chiqarib beradi."),
    ("💎 Telegram Premium qancha vaqtda tushadi?", "To'lov chekini bot orqali yuborganingizdan so'ng adminlarimiz 5-15 daqiqa ichida tasdiqlab ulab berishadi."),
    ("🎓 Kurslarga qanday yozilsam bo'ladi?", "Menyudan '🎓 Kurslarimiz' bo'limiga kirib, o'zingizga mos kursni tanlang va 'Kursga yozilish' tugmasini bosing.")
]


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA synchronous=NORMAL;")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS media_cache (
                cache_key TEXT PRIMARY KEY,
                file_id TEXT,
                title TEXT,
                performer TEXT,
                duration INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                phone TEXT,
                lang TEXT DEFAULT 'uz',
                is_banned INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                referred_by INTEGER,
                balance INTEGER DEFAULT 0,
                downloads_count INTEGER DEFAULT 0,
                searches_count INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT UNIQUE,
                title TEXT,
                invite_link TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                price TEXT,
                duration TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS course_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                course_id INTEGER,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS premium_tariffs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                price TEXT,
                description TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tariff_name TEXT,
                amount TEXT,
                receipt_file_id TEXT,
                target_username TEXT,
                comment TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                file_id TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS dynamic_buttons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                button_text TEXT UNIQUE,
                response_text TEXT,
                url TEXT
            )
        """)

        # Seed default settings
        for k, v in DEFAULT_SETTINGS.items():
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (k, v)
            )

        # Seed default courses if empty
        async with db.execute("SELECT COUNT(*) FROM courses") as cur:
            row = await cur.fetchone()
            if row and row[0] == 0:
                await db.executemany(
                    "INSERT INTO courses (title, description, price, duration) VALUES (?, ?, ?, ?)",
                    DEFAULT_COURSES
                )

        # Seed default tariffs if empty
        async with db.execute("SELECT COUNT(*) FROM premium_tariffs") as cur:
            row = await cur.fetchone()
            if row and row[0] == 0:
                await db.executemany(
                    "INSERT INTO premium_tariffs (name, price, description) VALUES (?, ?, ?)",
                    DEFAULT_TARIFFS
                )

        # Seed default FAQs if empty
        async with db.execute("SELECT COUNT(*) FROM faqs") as cur:
            row = await cur.fetchone()
            if row and row[0] == 0:
                await db.executemany(
                    "INSERT INTO faqs (question, answer) VALUES (?, ?)",
                    DEFAULT_FAQS
                )

        await db.commit()


# --- USER FUNCTIONS ---
async def register_user(user_id: int, full_name: str, username: Optional[str], referrer_id: Optional[int] = None) -> bool:
    """Returns True if user is newly registered."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cur:
            exists = await cur.fetchone()
        if exists:
            await db.execute(
                "UPDATE users SET full_name = ?, username = ? WHERE user_id = ?",
                (full_name, username or "", user_id)
            )
            await db.commit()
            return False

        is_admin = 1 if user_id in SUPER_ADMIN_IDS else 0
        valid_ref = None
        if referrer_id and referrer_id != user_id:
            async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (referrer_id,)) as cur:
                if await cur.fetchone():
                    valid_ref = referrer_id

        await db.execute(
            """INSERT INTO users (user_id, full_name, username, referred_by, is_admin)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, full_name, username or "", valid_ref, is_admin)
        )

        if valid_ref:
            reward_str = await get_setting("referral_reward", "500")
            reward = int(reward_str) if reward_str.isdigit() else 500
            await db.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (reward, valid_ref)
            )

        await db.commit()
        return True


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def is_user_admin(user_id: int) -> bool:
    if user_id in SUPER_ADMIN_IDS:
        return True
    user = await get_user(user_id)
    return bool(user and user.get("is_admin") == 1)


async def get_all_admin_ids() -> List[int]:
    admins = set(SUPER_ADMIN_IDS)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_admin = 1") as cur:
            rows = await cur.fetchall()
            for r in rows:
                admins.add(r[0])
    return list(admins)


async def set_user_admin(user_id: int, status: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_admin = ? WHERE user_id = ?", (status, user_id))
        await db.commit()


async def set_user_ban(user_id: int, status: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (status, user_id))
        await db.commit()


async def increment_user_stat(user_id: int, field: str):
    if field not in ("downloads_count", "searches_count"):
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {field} = {field} + 1 WHERE user_id = ?", (user_id,))
        await db.commit()


async def get_referrals_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


async def get_all_users() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY joined_at DESC") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_stats() -> Dict[str, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c1:
            total_users = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE date(joined_at) = date('now')") as c2:
            today_users = (await c2.fetchone())[0]
        async with db.execute("SELECT COALESCE(SUM(downloads_count), 0), COALESCE(SUM(searches_count), 0) FROM users") as c3:
            sums = await c3.fetchone()
            total_downloads, total_searches = sums[0], sums[1]
        async with db.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'") as c4:
            pending_payments = (await c4.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM channels") as c5:
            channels_count = (await c5.fetchone())[0]
        return {
            "total_users": total_users,
            "today_users": today_users,
            "total_downloads": total_downloads,
            "total_searches": total_searches,
            "pending_payments": pending_payments,
            "channels_count": channels_count,
        }


# --- SETTINGS FUNCTIONS ---
async def get_setting(key: str, default: str = "") -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else default


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value)
        )
        await db.commit()


# --- FORCE SUB CHANNELS ---
async def get_channels() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM channels ORDER BY id ASC") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def add_channel(chat_id: str, title: str, invite_link: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO channels (chat_id, title, invite_link) VALUES (?, ?, ?)",
            (chat_id.strip(), title.strip(), invite_link.strip())
        )
        await db.commit()


async def delete_channel(channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        await db.commit()


# --- COURSES ---
async def get_courses() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM courses ORDER BY id ASC") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_course(course_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM courses WHERE id = ?", (course_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def add_course(title: str, description: str, price: str, duration: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO courses (title, description, price, duration) VALUES (?, ?, ?, ?)",
            (title, description, price, duration)
        )
        await db.commit()


async def delete_course(course_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        await db.commit()


async def enroll_course(user_id: int, course_id: int, phone: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO course_enrollments (user_id, course_id, phone) VALUES (?, ?, ?)",
            (user_id, course_id, phone)
        )
        await db.commit()


# --- PREMIUM TARIFFS & PAYMENTS ---
async def get_tariffs() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM premium_tariffs ORDER BY id ASC") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_tariff(tariff_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM premium_tariffs WHERE id = ?", (tariff_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def add_tariff(name: str, price: str, description: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO premium_tariffs (name, price, description) VALUES (?, ?, ?)",
            (name, price, description)
        )
        await db.commit()


async def delete_tariff(tariff_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM premium_tariffs WHERE id = ?", (tariff_id,))
        await db.commit()


async def create_payment(user_id: int, tariff_name: str, amount: str, receipt_file_id: str, target_username: str, comment: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO payments (user_id, tariff_name, amount, receipt_file_id, target_username, comment)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, tariff_name, amount, receipt_file_id, target_username, comment)
        )
        await db.commit()
        return cur.lastrowid


async def update_payment_status(payment_id: int, status: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("UPDATE payments SET status = ? WHERE id = ?", (status, payment_id))
        await db.commit()
        async with db.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


# --- FAVORITES (PLAYLIST) ---
async def add_favorite(user_id: int, title: str, file_id: str, url: str = "") -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM favorites WHERE user_id = ? AND (file_id = ? OR title = ?)",
            (user_id, file_id, title)
        ) as cur:
            if await cur.fetchone():
                return False
        await db.execute(
            "INSERT INTO favorites (user_id, title, file_id, url) VALUES (?, ?, ?, ?)",
            (user_id, title, file_id, url)
        )
        await db.commit()
        return True


async def get_favorites(user_id: int) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM favorites WHERE user_id = ? ORDER BY id DESC LIMIT 30", (user_id,)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def delete_favorite(fav_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM favorites WHERE id = ? AND user_id = ?", (fav_id, user_id))
        await db.commit()


# --- SEARCH LOGS & TOP CHARTS ---
async def log_search(user_id: int, query: str):
    clean = query.strip()
    if len(clean) < 2 or clean.startswith("http"):
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO search_logs (query, user_id) VALUES (?, ?)", (clean, user_id))
        await db.commit()


async def get_top_queries(limit: int = 10) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT query, COUNT(*) as cnt
               FROM search_logs
               GROUP BY LOWER(query)
               ORDER BY cnt DESC
               LIMIT ?""",
            (limit,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# --- FAQ ---
async def get_faqs() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM faqs ORDER BY id ASC") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def add_faq(question: str, answer: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO faqs (question, answer) VALUES (?, ?)", (question, answer))
        await db.commit()


async def delete_faq(faq_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
        await db.commit()


# --- DYNAMIC MENU BUTTONS ---
async def get_dynamic_buttons() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM dynamic_buttons ORDER BY id ASC") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_dynamic_button_by_text(text: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM dynamic_buttons WHERE button_text = ?", (text,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def add_dynamic_button(button_text: str, response_text: str, url: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO dynamic_buttons (button_text, response_text, url) VALUES (?, ?, ?)",
            (button_text.strip(), response_text.strip(), url.strip())
        )
        await db.commit()


async def delete_dynamic_button(btn_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM dynamic_buttons WHERE id = ?", (btn_id,))
        await db.commit()


# --- MEDIA FILE_ID CACHE (INSTANT DELIVERY) ---
async def get_cached_media(cache_key: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM media_cache WHERE cache_key = ?", (cache_key,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def save_cached_media(cache_key: str, file_id: str, title: str, performer: str = "", duration: int = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO media_cache (cache_key, file_id, title, performer, duration)
               VALUES (?, ?, ?, ?, ?)""",
            (cache_key, file_id, title, performer, duration)
        )
        await db.commit()


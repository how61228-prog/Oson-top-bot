from typing import List, Dict, Any
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_menu(is_admin: bool = False, dynamic_buttons: List[Dict[str, Any]] = None) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    # Row 1: Music & Video Download & Round Video
    builder.row(
        KeyboardButton(text="🎵 Musiqa qidirish"),
        KeyboardButton(text="📥 Video yuklash (Link)"),
        KeyboardButton(text="⭕ Dumaloq video (Round)"),
    )
    # Row 2: Top Charts & Random Hit & Playlist
    builder.row(
        KeyboardButton(text="🔥 Top Xitlar"),
        KeyboardButton(text="🎲 Tasodifiy qo'shiq"),
        KeyboardButton(text="❤️ Sevimlilar"),
    )
    # Row 3: Telegram Premium & Courses
    builder.row(
        KeyboardButton(text="💎 Telegram Premium"),
        KeyboardButton(text="🎓 Kurslarimiz"),
    )
    # Row 4: Lyrics & Referral & Profile
    builder.row(
        KeyboardButton(text="📝 Qo'shiq matni"),
        KeyboardButton(text="👥 Do'stlarni taklif qilish"),
        KeyboardButton(text="👤 Kabinetim"),
    )
    # Row 5: Ads & Location & Contacts & Support
    builder.row(
        KeyboardButton(text="📢 Reklama berish"),
        KeyboardButton(text="✍️ Adminga bog'lanish"),
    )
    builder.row(
        KeyboardButton(text="📍 Lokatsiyamiz"),
        KeyboardButton(text="📞 Bizning raqamlar"),
    )
    # Row 6: FAQ & Help & Language
    builder.row(
        KeyboardButton(text="❓ Ko'p beriladigan savollar"),
        KeyboardButton(text="🆘 Yordam (Help)"),
        KeyboardButton(text="🌐 Til / Инфо"),
    )

    # Dynamic custom buttons added by Admin
    if dynamic_buttons:
        temp_row = []
        for btn in dynamic_buttons:
            temp_row.append(KeyboardButton(text=btn["button_text"]))
            if len(temp_row) == 2:
                builder.row(*temp_row)
                temp_row = []
        if temp_row:
            builder.row(*temp_row)

    if is_admin:
        builder.row(KeyboardButton(text="🛠 Admin Panel"))

    return builder.as_markup(resize_keyboard=True)


def get_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )


def get_phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )


def get_sub_channels_kb(channels: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for idx, ch in enumerate(channels, start=1):
        builder.row(
            InlineKeyboardButton(
                text=f"📢 {idx}. {ch['title']}",
                url=ch["invite_link"]
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="✅ Obuna bo'ldim (Tekshirish)",
            callback_data="check_subs"
        )
    )
    return builder.as_markup()


def get_search_results_kb(results: List[Dict[str, Any]], session_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    row_btns = []
    for idx, item in enumerate(results):
        row_btns.append(
            InlineKeyboardButton(
                text=f"{idx + 1}",
                callback_data=f"dl_track:{session_key}:{idx}"
            )
        )
        if len(row_btns) == 5:
            builder.row(*row_btns)
            row_btns = []
    if row_btns:
        builder.row(*row_btns)

    builder.row(
        InlineKeyboardButton(text="❌ Yopish", callback_data="close_msg")
    )
    return builder.as_markup()


def get_media_actions_kb(video_id_or_key: str, is_video: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_video:
        builder.row(
            InlineKeyboardButton(
                text="🎵 MP3 (Musiqasini) tortish",
                callback_data=f"extract_mp3:{video_id_or_key}"
            ),
            InlineKeyboardButton(
                text="⭕ Dumaloqcha (Round)",
                callback_data=f"make_round:{video_id_or_key}"
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="❤️ Sevimlilarga saqlash",
            callback_data=f"fav_add:{video_id_or_key}"
        )
    )
    return builder.as_markup()


def get_favorites_kb(favs: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for idx, f in enumerate(favs, start=1):
        title_short = f["title"][:30]
        builder.row(
            InlineKeyboardButton(
                text=f"🎵 {idx}. {title_short}",
                callback_data=f"fav_play:{f['id']}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"fav_del:{f['id']}"
            )
        )
    builder.row(InlineKeyboardButton(text="❌ Yopish", callback_data="close_msg"))
    return builder.as_markup()


def get_courses_kb(courses: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in courses:
        builder.row(
            InlineKeyboardButton(
                text=f"{c['title']} ({c['price']})",
                callback_data=f"course_view:{c['id']}"
            )
        )
    return builder.as_markup()


def get_course_detail_kb(course_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📝 Kursga yozilish",
            callback_data=f"course_enroll:{course_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Kurslar ro'yxatiga qaytish",
            callback_data="courses_back"
        )
    )
    return builder.as_markup()


def get_premium_tariffs_kb(tariffs: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for t in tariffs:
        builder.row(
            InlineKeyboardButton(
                text=f"{t['name']} — {t['price']}",
                callback_data=f"buy_tariff:{t['id']}"
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="✍️ Savol bo'yicha adminga yozish",
            callback_data="contact_admin_inline"
        )
    )
    return builder.as_markup()


def get_admin_payment_verify_kb(payment_id: int, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Tasdiqlash (Ulandi)",
            callback_data=f"pay_ok:{payment_id}:{user_id}"
        ),
        InlineKeyboardButton(
            text="❌ Rad etish",
            callback_data=f"pay_no:{payment_id}:{user_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💬 Foydalanuvchiga javob yozish",
            callback_data=f"admin_reply:{user_id}"
        )
    )
    return builder.as_markup()


def get_admin_support_reply_kb(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💬 Javob yozish",
            callback_data=f"admin_reply:{user_id}"
        )
    )
    return builder.as_markup()


def get_faqs_kb(faqs: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for idx, f in enumerate(faqs, start=1):
        builder.row(
            InlineKeyboardButton(
                text=f"❓ {idx}. {f['question'][:45]}",
                callback_data=f"faq_view:{f['id']}"
            )
        )
    return builder.as_markup()


# --- ADMIN PANEL KEYBOARDS ---
def get_admin_main_kb(sub_required: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    sub_status = "🟢 Yoqilgan" if sub_required else "🔴 O'chirilgan"
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="adm_stats"),
        InlineKeyboardButton(text="📨 Xabar tarqatish (Rassilka)", callback_data="adm_broadcast"),
    )
    builder.row(
        InlineKeyboardButton(text=f"📢 Majburiy obuna ({sub_status})", callback_data="adm_channels"),
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Matnlar va Lokatsiyani sozlash", callback_data="adm_settings"),
    )
    builder.row(
        InlineKeyboardButton(text="💎 Premium & To'lov sozlamalari", callback_data="adm_tariffs"),
        InlineKeyboardButton(text="🎓 Kurslarni boshqarish", callback_data="adm_courses"),
    )
    builder.row(
        InlineKeyboardButton(text="🎛 Dinamik menyu tugmalari", callback_data="adm_dyn_buttons"),
        InlineKeyboardButton(text="❓ FAQ boshqaruvi", callback_data="adm_faqs"),
    )
    builder.row(
        InlineKeyboardButton(text="👤 Foydalanuvchi qidirish / Ban", callback_data="adm_user_manage"),
        InlineKeyboardButton(text="👮‍♂️ Adminlar boshqaruvi", callback_data="adm_admins"),
    )
    builder.row(
        InlineKeyboardButton(text="📥 Baza eksport (CSV)", callback_data="adm_export_csv"),
        InlineKeyboardButton(text="❌ Yopish", callback_data="close_msg"),
    )
    return builder.as_markup()


def get_admin_channels_kb(channels: List[Dict[str, Any]], sub_required: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_text = "🔴 Majburiy obunani O'CHIRISH" if sub_required else "🟢 Majburiy obunani YOQISH"
    builder.row(InlineKeyboardButton(text=toggle_text, callback_data="adm_toggle_sub"))

    for ch in channels:
        builder.row(
            InlineKeyboardButton(text=f"📢 {ch['title']} ({ch['chat_id']})", url=ch["invite_link"]),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_del_ch:{ch['id']}")
        )

    builder.row(InlineKeyboardButton(text="➕ Yangi kanal qo'shish", callback_data="adm_add_ch"))
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_back_main"))
    return builder.as_markup()


def get_admin_settings_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👋 Salomlashish matni", callback_data="adm_set:welcome_text"),
        InlineKeyboardButton(text="🆘 Yordam (Help) matni", callback_data="adm_set:help_text"),
    )
    builder.row(
        InlineKeyboardButton(text="📞 Bizning raqamlar matni", callback_data="adm_set:contacts_text"),
        InlineKeyboardButton(text="ℹ️ Bot haqida matn", callback_data="adm_set:about_text"),
    )
    builder.row(
        InlineKeyboardButton(text="📍 Lokatsiya manzili matni", callback_data="adm_set:location_title"),
        InlineKeyboardButton(text="🗺 Lokatsiya koordinatasi (GPS)", callback_data="adm_set_coords"),
    )
    builder.row(
        InlineKeyboardButton(text="💳 Premium & Karta rekvizit matni", callback_data="adm_set:premium_text"),
        InlineKeyboardButton(text="📢 Reklama paneli matni", callback_data="adm_set:ads_text"),
    )
    builder.row(
        InlineKeyboardButton(text="🎁 Referal bonus miqdori", callback_data="adm_set:referral_reward"),
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_back_main")
    )
    return builder.as_markup()

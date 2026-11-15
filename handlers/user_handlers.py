import random
import uuid
from typing import Dict, Any
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext

from database import (
    register_user,
    get_user,
    is_user_admin,
    get_all_admin_ids,
    get_setting,
    get_dynamic_buttons,
    get_dynamic_button_by_text,
    increment_user_stat,
    log_search,
    get_top_queries,
    get_referrals_count,
    get_courses,
    get_course,
    enroll_course,
    get_tariffs,
    get_tariff,
    create_payment,
    add_favorite,
    get_favorites,
    delete_favorite,
    get_faqs,
    get_cached_media,
    save_cached_media,
)
from keyboards import (
    get_main_menu,
    get_cancel_kb,
    get_phone_kb,
    get_search_results_kb,
    get_media_actions_kb,
    get_favorites_kb,
    get_courses_kb,
    get_course_detail_kb,
    get_premium_tariffs_kb,
    get_admin_payment_verify_kb,
    get_admin_support_reply_kb,
    get_faqs_kb,
    get_sub_channels_kb,
)
from middlewares import check_unsubscribed_channels
from media_service import (
    extract_url,
    search_music_yt,
    download_audio,
    download_video,
    extract_audio_from_local_video,
    convert_video_to_round,
    search_lyrics,
    safe_remove,
    POPULAR_RANDOM_QUERIES,
)
from config import DOWNLOAD_DIR
from states import UserStates

user_router = Router()

# In-memory cache for search sessions and recent tracks
SEARCH_CACHE: Dict[str, Any] = {}
TRACK_META_CACHE: Dict[str, Dict[str, str]] = {}


async def build_user_main_kb(user_id: int):
    is_adm = await is_user_admin(user_id)
    dyn_btns = await get_dynamic_buttons()
    return get_main_menu(is_admin=is_adm, dynamic_buttons=dyn_btns)


# ==================== 1. /START & REFERRAL & SUB CHECK ====================
@user_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext, bot: Bot):
    await state.clear()
    user = message.from_user
    ref_id = None
    if command and command.args and command.args.isdigit():
        ref_id = int(command.args)

    is_new = await register_user(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username,
        referrer_id=ref_id,
    )

    if is_new and ref_id and ref_id != user.id:
        reward = await get_setting("referral_reward", "500")
        try:
            await bot.send_message(
                ref_id,
                f"🎉 <b>Yangi referal!</b>\nDo'stingiz <b>{user.full_name}</b> botga sizning havolangiz orqali qo'shildi!\n💰 Sizga <b>+{reward} so'm</b> bonus yozildi!"
            )
        except Exception:
            pass

    # Check mandatory subscription
    unsubscribed = await check_unsubscribed_channels(bot, user.id)
    if unsubscribed:
        await message.answer(
            "👋 <b>Xush kelibsiz!</b>\n\n"
            "🛑 Botdan to'liq foydalanish, musiqa hamda Instagram/TikTok/YouTube videolarini yuklab olish uchun "
            "quyidagi kanallarga obuna bo'ling:",
            reply_markup=get_sub_channels_kb(unsubscribed)
        )
        return

    welcome_tpl = await get_setting("welcome_text")
    welcome_msg = welcome_tpl.replace("{name}", user.full_name)
    kb = await build_user_main_kb(user.id)
    await message.answer(welcome_msg, reply_markup=kb)


@user_router.message(F.text.lower() == "start")
async def text_start_alias(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    welcome_tpl = await get_setting("welcome_text")
    welcome_msg = welcome_tpl.replace("{name}", message.from_user.full_name)
    kb = await build_user_main_kb(message.from_user.id)
    await message.answer(welcome_msg, reply_markup=kb)


@user_router.callback_query(F.data == "check_subs")
async def cb_check_subs(call: CallbackQuery, bot: Bot):
    unsubscribed = await check_unsubscribed_channels(bot, call.from_user.id, force_check=True)
    if unsubscribed:
        await call.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        try:
            await call.message.edit_reply_markup(reply_markup=get_sub_channels_kb(unsubscribed))
        except Exception:
            pass
        return

    await call.answer("✅ Obuna tasdiqlandi! Marhamat, botdan foydalaning.", show_alert=True)
    try:
        await call.message.delete()
    except Exception:
        pass
    kb = await build_user_main_kb(call.from_user.id)
    welcome_tpl = await get_setting("welcome_text")
    await call.message.answer(welcome_tpl.replace("{name}", call.from_user.first_name), reply_markup=kb)


@user_router.callback_query(F.data == "close_msg")
async def cb_close_msg(call: CallbackQuery):
    try:
        await call.message.delete()
    except Exception:
        await call.answer("Yopildi")


# ==================== CANCEL HANDLER ====================
@user_router.message(F.text == "❌ Bekor qilish")
async def cancel_any_state(message: Message, state: FSMContext):
    await state.clear()
    kb = await build_user_main_kb(message.from_user.id)
    await message.answer("✅ Amal bekor qilindi. Asosiy menyudasiz:", reply_markup=kb)


# ==================== 2. MUSIC SEARCH & VIDEO GUIDE ====================
@user_router.message(F.text == "🎵 Musiqa qidirish")
async def menu_music_search(message: Message):
    await message.answer(
        "🎧 <b>Musiqa qidirish bo'limi!</b>\n\n"
        "Shunchaki qo'shiqchi yoki musiqa nomini yozib yuboring.\n"
        "<i>Misol uchun: Konsta - Odamlar nima deydi</i>"
    )


@user_router.message(F.text == "📥 Video yuklash (Link)")
async def menu_video_download(message: Message):
    await message.answer(
        "📥 <b>Ijtimoiy tarmoqlardan Video va Musiqa yuklash!</b>\n\n"
        "Quyidagi platformalardan video linkini yuboring:\n"
        "🔹 <b>Instagram</b> (Reels, Post, IGTV)\n"
        "🔹 <b>TikTok</b> (Suv belgisiz / Watermark-free)\n"
        "🔹 <b>YouTube</b> (Shorts va Videolar)\n"
        "🔹 <b>Pinterest / Facebook</b>\n\n"
        "💡 <i>Bot videoni yuborgach, ostidagi <b>«🎵 MP3 (Musiqasini) tortish»</b> tugmasi orqali uning musiqasini ham bir zumda olishingiz mumkin!</i>"
    )


# ==================== 3. TOP CHARTS (TOP XITLAR) ====================
@user_router.message(F.text == "🔥 Top Xitlar")
async def menu_top_hits(message: Message):
    top_queries = await get_top_queries(10)
    if not top_queries:
        # Show popular default chart
        queries = POPULAR_RANDOM_QUERIES[:8]
    else:
        queries = [q["query"] for q in top_queries]

    text = "🔥 <b>Eng ko'p qidirilgan Top Xitlar:</b>\n<i>(Yuklab olish uchun quyidagi xitlardan birini bosing)</i>\n\n"
    rows = []
    for idx, q in enumerate(queries, start=1):
        text += f"<b>{idx}.</b> {q}\n"
        rows.append([InlineKeyboardButton(text=f"🎵 {idx}. {q[:30]}", callback_data=f"quick_search:{q[:35]}")])

    rows.append([InlineKeyboardButton(text="❌ Yopish", callback_data="close_msg")])
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@user_router.callback_query(F.data.startswith("quick_search:"))
async def cb_quick_search(call: CallbackQuery):
    query = call.data.split(":", 1)[1]
    await call.answer(f"🔍 Qidirilmoqda: {query}")
    await perform_music_search(call.message, call.from_user.id, query)


# ==================== 4. RANDOM HIT ====================
@user_router.message(F.text == "🎲 Tasodifiy qo'shiq")
async def menu_random_song(message: Message):
    query = random.choice(POPULAR_RANDOM_QUERIES)
    await perform_music_search(message, message.from_user.id, query)


# ==================== 5. FAVORITES / PLAYLIST ====================
@user_router.message(F.text == "❤️ Sevimlilar")
async def menu_favorites(message: Message):
    favs = await get_favorites(message.from_user.id)
    if not favs:
        await message.answer(
            "❤️ <b>Sizning sevimli qo'shiqlar ro'yxatingiz (Play-list) hozircha bo'sh.</b>\n\n"
            "💡 <i>Istalgan yuklab olingan musiqa ostidagi «❤️ Sevimlilarga saqlash» tugmasini bosib saqlab qo'yishingiz mumkin!</i>"
        )
        return

    await message.answer(
        f"❤️ <b>Sizning Sevimli Qo'shiqlaringiz ({len(favs)} ta):</b>\n"
        "<i>Tinglash uchun qo'shiq ustiga bosing:</i>",
        reply_markup=get_favorites_kb(favs)
    )


@user_router.callback_query(F.data.startswith("fav_add:"))
async def cb_fav_add(call: CallbackQuery):
    key = call.data.split(":", 1)[1]
    meta = TRACK_META_CACHE.get(key)
    file_id = ""
    title = "Saqlangan musiqa"
    url = ""

    if call.message.audio:
        file_id = call.message.audio.file_id
        title = call.message.audio.title or call.message.audio.file_name or title
    elif call.message.video:
        file_id = call.message.video.file_id
        title = "Saqlangan Video"

    if meta:
        title = meta.get("title", title)
        url = meta.get("url", "")
        if not file_id:
            file_id = meta.get("file_id", "")

    if not file_id:
        await call.answer("⚠️ Fayl topilmadi!", show_alert=True)
        return

    added = await add_favorite(call.from_user.id, title, file_id, url)
    if added:
        await call.answer("❤️ Sevimlilar ro'yxatiga qo'shildi!", show_alert=True)
    else:
        await call.answer("ℹ️ Bu musiqa allaqachon Sevimlilarda bor!", show_alert=True)


@user_router.callback_query(F.data.startswith("fav_play:"))
async def cb_fav_play(call: CallbackQuery):
    fav_id = int(call.data.split(":")[1])
    favs = await get_favorites(call.from_user.id)
    target = next((f for f in favs if f["id"] == fav_id), None)
    if not target:
        await call.answer("⚠️ Qo'shiq topilmadi!", show_alert=True)
        return
    await call.answer("🎵 Yuborilmoqda...")
    try:
        await call.message.answer_audio(
            audio=target["file_id"],
            caption=f"❤️ <b>{target['title']}</b>\n🤖 @{call.bot._me.username if call.bot._me else 'MusicBot'}"
        )
    except Exception:
        await call.message.answer_document(
            document=target["file_id"],
            caption=f"❤️ <b>{target['title']}</b>"
        )


@user_router.callback_query(F.data.startswith("fav_del:"))
async def cb_fav_del(call: CallbackQuery):
    fav_id = int(call.data.split(":")[1])
    await delete_favorite(fav_id, call.from_user.id)
    favs = await get_favorites(call.from_user.id)
    await call.answer("🗑 Ro'yxatdan o'chirildi!")
    if not favs:
        await call.message.edit_text("❤️ <b>Sevimlilar ro'yxatingiz bo'shatildi.</b>")
    else:
        await call.message.edit_reply_markup(reply_markup=get_favorites_kb(favs))


# ==================== 6. TELEGRAM PREMIUM & PAYMENT ====================
@user_router.message(F.text == "💎 Telegram Premium")
async def menu_telegram_premium(message: Message):
    prem_text = await get_setting("premium_text")
    tariffs = await get_tariffs()
    await message.answer(
        prem_text,
        reply_markup=get_premium_tariffs_kb(tariffs)
    )


@user_router.callback_query(F.data.startswith("buy_tariff:"))
async def cb_buy_tariff(call: CallbackQuery, state: FSMContext):
    tariff_id = int(call.data.split(":")[1])
    tariff = await get_tariff(tariff_id)
    if not tariff:
        await call.answer("⚠️ Tarif topilmadi!", show_alert=True)
        return

    await state.update_data(
        tariff_id=tariff["id"],
        tariff_name=tariff["name"],
        tariff_price=tariff["price"]
    )
    await state.set_state(UserStates.waiting_for_premium_username)
    await call.message.answer(
        f"💎 <b>Tanlangan tarif:</b> {tariff['name']}\n"
        f"💰 <b>Narxi:</b> {tariff['price']}\n"
        f"ℹ️ <b>Tavsif:</b> {tariff['description']}\n\n"
        "👉 <b>1-qadam:</b> Premium yoki Stars qaysi Telegram akkauntga ulanishi kerak? "
        "O'sha profilning <b>@username</b> yoki telefon raqamini yozib yuboring:",
        reply_markup=get_cancel_kb()
    )
    await call.answer()


@user_router.message(UserStates.waiting_for_premium_username, F.text)
async def process_premium_username(message: Message, state: FSMContext):
    target_user = message.text.strip()
    await state.update_data(target_username=target_user)
    await state.set_state(UserStates.waiting_for_premium_receipt)

    prem_text = await get_setting("premium_text")
    await message.answer(
        f"✅ Qabul qiluvchi profil: <b>{target_user}</b>\n\n"
        f"{prem_text}\n\n"
        "📸 <b>2-qadam:</b> Yuqoridagi karta raqamga to'lovni amalga oshirib, "
        "<b>to'lov cheki (skrinshot/rasm yoki fayl)</b>ni shu yerga yuboring!",
        reply_markup=get_cancel_kb()
    )


@user_router.message(UserStates.waiting_for_premium_receipt)
async def process_premium_receipt(message: Message, state: FSMContext, bot: Bot):
    file_id = None
    is_photo = False
    if message.photo:
        file_id = message.photo[-1].file_id
        is_photo = True
    elif message.document:
        file_id = message.document.file_id

    if not file_id:
        await message.answer("⚠️ Iltimos, to'lov chekini <b>rasm (skrinshot)</b> yoki <b>fayl</b> ko'rinishida yuboring!")
        return

    data = await state.get_data()
    tariff_name = data.get("tariff_name", "Telegram Premium")
    tariff_price = data.get("tariff_price", "")
    target_username = data.get("target_username", "")
    comment = message.caption or ""

    payment_id = await create_payment(
        user_id=message.from_user.id,
        tariff_name=tariff_name,
        amount=tariff_price,
        receipt_file_id=file_id,
        target_username=target_username,
        comment=comment
    )

    await state.clear()
    kb = await build_user_main_kb(message.from_user.id)
    await message.answer(
        f"✅ <b>To'lov chekingiz qabul qilindi! (Buyurtma #{payment_id})</b>\n\n"
        f"💎 Xizmat: <b>{tariff_name} ({tariff_price})</b>\n"
        f"👤 Akkaunt: <b>{target_username}</b>\n\n"
        "⏳ Adminlarimiz to'lovni tekshirib, tez orada xizmatni yoqib berishadi va sizga xabar keladi!",
        reply_markup=kb
    )

    # Notify all admins
    admins = await get_all_admin_ids()
    admin_caption = (
        f"💳 <b>YANGI TO'LOV BUYURTMASI #{payment_id}</b>\n\n"
        f"👤 Xaridor: <a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a> "
        f"(@{message.from_user.username or 'yoq'})\n"
        f"🆔 User ID: <code>{message.from_user.id}</code>\n"
        f"💎 Tarif: <b>{tariff_name}</b>\n"
        f"💰 Summa: <b>{tariff_price}</b>\n"
        f"🎯 Ulanadigan profil: <code>{target_username}</code>\n"
        f"💬 Izoh: {comment or 'Yoq'}"
    )
    verify_kb = get_admin_payment_verify_kb(payment_id, message.from_user.id)
    for adm_id in admins:
        try:
            if is_photo:
                await bot.send_photo(adm_id, photo=file_id, caption=admin_caption, reply_markup=verify_kb)
            else:
                await bot.send_document(adm_id, document=file_id, caption=admin_caption, reply_markup=verify_kb)
        except Exception:
            pass


# ==================== 7. COURSES (KURSLARIMIZ) ====================
@user_router.message(F.text == "🎓 Kurslarimiz")
async def menu_courses(message: Message):
    courses = await get_courses()
    if not courses:
        await message.answer("🎓 Hozircha faol kurslar ro'yxati kiritilmagan.")
        return

    await message.answer(
        "🎓 <b>Bizning O'quv Kurslarimiz:</b>\n\n"
        "Batafsil ma'lumot olish va ro'yxatdan o'tish uchun quyidagi kurslardan birini tanlang:",
        reply_markup=get_courses_kb(courses)
    )


@user_router.callback_query(F.data == "courses_back")
async def cb_courses_back(call: CallbackQuery):
    courses = await get_courses()
    await call.message.edit_text(
        "🎓 <b>Bizning O'quv Kurslarimiz:</b>\n\n"
        "Batafsil ma'lumot olish va ro'yxatdan o'tish uchun quyidagi kurslardan birini tanlang:",
        reply_markup=get_courses_kb(courses)
    )


@user_router.callback_query(F.data.startswith("course_view:"))
async def cb_course_view(call: CallbackQuery):
    course_id = int(call.data.split(":")[1])
    c = await get_course(course_id)
    if not c:
        await call.answer("⚠️ Kurs topilmadi!", show_alert=True)
        return

    text = (
        f"🎓 <b>{c['title']}</b>\n\n"
        f"📖 <b>Kurs haqida:</b>\n{c['description']}\n\n"
        f"⏳ <b>Davomiyligi:</b> {c['duration']}\n"
        f"💰 <b>Narxi:</b> {c['price']}\n\n"
        "👇 <i>Kursga yozilish uchun pastdagi tugmani bosing:</i>"
    )
    await call.message.edit_text(text, reply_markup=get_course_detail_kb(course_id))


@user_router.callback_query(F.data.startswith("course_enroll:"))
async def cb_course_enroll(call: CallbackQuery, state: FSMContext):
    course_id = int(call.data.split(":")[1])
    c = await get_course(course_id)
    if not c:
        await call.answer("⚠️ Kurs topilmadi!", show_alert=True)
        return

    await state.update_data(course_id=course_id, course_title=c["title"])
    await state.set_state(UserStates.waiting_for_course_phone)
    await call.message.answer(
        f"📝 <b>«{c['title']}»</b> kursiga ro'yxatdan o'tish uchun telefon raqamingizni yuboring "
        "yoki pastdagi tugmani bosing:",
        reply_markup=get_phone_kb()
    )
    await call.answer()


@user_router.message(UserStates.waiting_for_course_phone)
async def process_course_phone(message: Message, state: FSMContext, bot: Bot):
    phone = ""
    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        phone = message.text.strip()

    if not phone or len(phone) < 7:
        await message.answer("⚠️ Iltimos, to'g'ri telefon raqam kiriting yoki tugmani bosing!")
        return

    data = await state.get_data()
    course_id = data.get("course_id", 0)
    course_title = data.get("course_title", "Kurs")

    await enroll_course(message.from_user.id, course_id, phone)
    await state.clear()
    kb = await build_user_main_kb(message.from_user.id)
    await message.answer(
        f"✅ <b>Arizangiz qabul qilindi!</b>\n\n"
        f"🎓 Kurs: <b>{course_title}</b>\n"
        f"📱 Raqamingiz: <b>{phone}</b>\n\n"
        "Tez orada menejerlarimiz siz bilan bog'lanishadi!",
        reply_markup=kb
    )

    admins = await get_all_admin_ids()
    for adm_id in admins:
        try:
            await bot.send_message(
                adm_id,
                f"🎓 <b>KURSGA YANGI ARIZA!</b>\n\n"
                f"📚 Kurs: <b>{course_title}</b>\n"
                f"👤 Ism: {message.from_user.full_name} (@{message.from_user.username or 'yoq'})\n"
                f"📱 Telefon: <code>{phone}</code>\n"
                f"🆔 ID: <code>{message.from_user.id}</code>",
                reply_markup=get_admin_support_reply_kb(message.from_user.id)
            )
        except Exception:
            pass


# ==================== 8. LYRICS FINDER (QO'SHIQ MATNI) ====================
@user_router.message(F.text == "📝 Qo'shiq matni")
async def menu_lyrics(message: Message, state: FSMContext):
    await state.set_state(UserStates.waiting_for_lyrics_query)
    await message.answer(
        "📝 <b>Qo'shiq matnini (Lyrics) qidirish:</b>\n\n"
        "Qo'shiqchi va qo'shiq nomini yozib yuboring (masalan: <i>Eminem - Lose Yourself</i>):",
        reply_markup=get_cancel_kb()
    )


@user_router.message(UserStates.waiting_for_lyrics_query, F.text)
async def process_lyrics_search(message: Message, state: FSMContext):
    query = message.text.strip()
    wait_msg = await message.answer("🔍 <i>Qo'shiq matni qidirilmoqda...</i>")
    res = await search_lyrics(query)
    await state.clear()
    kb = await build_user_main_kb(message.from_user.id)
    try:
        await wait_msg.delete()
    except Exception:
        pass

    if not res:
        await message.answer(
            f"😔 Kechirasiz, <b>«{query}»</b> bo'yicha qo'shiq matni topilmadi.\n"
            "Boshqa nom bilan urinib ko'ring.",
            reply_markup=kb
        )
        return

    await message.answer(
        f"🎤 <b>{res['artist']} — {res['track']}</b>\n\n"
        f"{res['lyrics']}",
        reply_markup=kb
    )


# ==================== 9. REFERRAL SYSTEM ====================
@user_router.message(F.text == "👥 Do'stlarni taklif qilish")
async def menu_referral(message: Message, bot: Bot):
    me = await bot.get_me()
    ref_link = f"https://t.me/{me.username}?start={message.from_user.id}"
    ref_count = await get_referrals_count(message.from_user.id)
    u = await get_user(message.from_user.id)
    balance = u["balance"] if u else 0
    reward = await get_setting("referral_reward", "500")

    share_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📲 Do'stlarga ulashish",
            url=f"https://t.me/share/url?url={ref_link}&text=Eng%20zo'r%20Musiqa%20va%20Instagram/TikTok/YouTube%20Video%20yuklovchi%20bot!"
        )]
    ])

    await message.answer(
        f"👥 <b>Referal va Bonus tizimi!</b>\n\n"
        f"Do'stlaringizni shaxsiy havolangiz orqali botga taklif qiling va har bir do'stingiz uchun "
        f"<b>{reward} so'm</b> bonusga ega bo'ling!\n\n"
        f"🔗 <b>Sizning referal havolangiz:</b>\n<code>{ref_link}</code>\n\n"
        f"📊 <b>Sizning natijalaringiz:</b>\n"
        f"👤 Taklif qilingan do'stlar: <b>{ref_count} ta</b>\n"
        f"💰 Bonus balansingiz: <b>{balance} so'm</b>",
        reply_markup=share_kb
    )


# ==================== 10. USER CABINET / PROFILE ====================
@user_router.message(F.text == "👤 Kabinetim")
async def menu_profile(message: Message):
    u = await get_user(message.from_user.id)
    ref_count = await get_referrals_count(message.from_user.id)
    favs = await get_favorites(message.from_user.id)
    if not u:
        await message.answer("Ma'lumot topilmadi. /start bosing.")
        return

    await message.answer(
        f"👤 <b>Shaxsiy Kabinetingiz:</b>\n\n"
        f"🆔 <b>ID raqamingiz:</b> <code>{u['user_id']}</code>\n"
        f"🙍‍♂️ <b>Ismingiz:</b> {u['full_name']}\n"
        f"🌐 <b>Username:</b> @{u['username'] or ' kiritilmagan'}\n"
        f"📥 <b>Yuklab olgan media:</b> {u['downloads_count']} ta\n"
        f"🔍 <b>Qidiruvlar soni:</b> {u['searches_count']} ta\n"
        f"❤️ <b>Sevimlilar (Play-list):</b> {len(favs)} ta\n"
        f"👥 <b>Taklif qilinganlar:</b> {ref_count} nafar\n"
        f"💰 <b>Bonus balans:</b> {u['balance']} so'm\n"
        f"📅 <b>Ro'yxatdan o'tilgan:</b> {u['joined_at']}"
    )


# ==================== 11. LOCATION (LOKATSIYAMIZ) ====================
@user_router.message(F.text == "📍 Lokatsiyamiz")
async def menu_location(message: Message):
    loc_title = await get_setting("location_title")
    lat_str = await get_setting("location_lat", "41.311081")
    lon_str = await get_setting("location_lon", "69.240562")
    try:
        lat = float(lat_str)
        lon = float(lon_str)
        await message.answer_location(latitude=lat, longitude=lon)
    except Exception:
        pass
    await message.answer(loc_title)


# ==================== 12. CONTACTS & ADS (REKLAMA PANELI) ====================
@user_router.message(F.text == "📢 Reklama berish")
async def menu_ads_panel(message: Message):
    ads_text = await get_setting(
        "ads_text",
        "📢 <b>Botda Reklama va Hamkorlik!</b>\n\n👉 Reklama uchun @jorayevvbb ga murojaat qiling!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Reklama bo'yicha yozish (@jorayevvbb)", url="https://t.me/jorayevvbb")],
        [InlineKeyboardButton(text="✍️ Bot orqali adminga xabar yozish", callback_data="contact_admin_inline")]
    ])
    await message.answer(ads_text, reply_markup=kb)


@user_router.message(F.text == "📞 Bizning raqamlar")
async def menu_contacts(message: Message):
    contacts = await get_setting("contacts_text")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Reklama uchun: @jorayevvbb", url="https://t.me/jorayevvbb")]
    ])
    await message.answer(contacts, reply_markup=kb, disable_web_page_preview=True)


# ==================== 13. SUPPORT / CONTACT ADMIN ====================
@user_router.message(F.text == "✍️ Adminga bog'lanish")
async def menu_contact_admin(message: Message, state: FSMContext):
    await state.set_state(UserStates.waiting_for_support_msg)
    await message.answer(
        "✍️ <b>Adminga murojaat yuborish:</b>\n\n"
        "Savolingiz, taklifingiz, reklama yoki to'lov bo'yicha murojaatingizni yozib yuboring "
        "(matn, rasm, ovozli xabar yoki video yuborishingiz mumkin):",
        reply_markup=get_cancel_kb()
    )


@user_router.callback_query(F.data == "contact_admin_inline")
async def cb_contact_admin_inline(call: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_support_msg)
    await call.message.answer(
        "✍️ <b>Adminga xabaringizni yozib yuboring:</b>",
        reply_markup=get_cancel_kb()
    )
    await call.answer()


@user_router.message(UserStates.waiting_for_support_msg)
async def process_support_msg(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    kb = await build_user_main_kb(message.from_user.id)
    await message.answer(
        "✅ <b>Xabaringiz adminga muvaffaqiyatli yuborildi!</b>\n"
        "Admin javob yozishi bilan sizga shu yerda xabar keladi.",
        reply_markup=kb
    )

    admins = await get_all_admin_ids()
    header = (
        f"📩 <b>YANGI MUROJAAT (Adminga xabar)!</b>\n\n"
        f"👤 <b>Kimdan:</b> <a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a> "
        f"(@{message.from_user.username or 'yoq'})\n"
        f"🆔 <b>User ID:</b> <code>{message.from_user.id}</code>\n"
    )
    reply_kb = get_admin_support_reply_kb(message.from_user.id)

    for adm_id in admins:
        try:
            if message.text:
                await bot.send_message(
                    adm_id,
                    f"{header}\n💬 <b>Xabar:</b>\n{message.text}",
                    reply_markup=reply_kb
                )
            else:
                await bot.send_message(adm_id, header)
                await bot.copy_message(
                    chat_id=adm_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                    reply_markup=reply_kb
                )
        except Exception:
            pass


# ==================== 14. FAQ ====================
@user_router.message(F.text == "❓ Ko'p beriladigan savollar")
async def menu_faqs(message: Message):
    faqs = await get_faqs()
    if not faqs:
        await message.answer("❓ Hozircha savol-javoblar kiritilmagan.")
        return

    await message.answer(
        "❓ <b>Ko'p beriladigan savollar (FAQ):</b>\n\n"
        "Javobni o'qish uchun savol ustiga bosing:",
        reply_markup=get_faqs_kb(faqs)
    )


@user_router.callback_query(F.data.startswith("faq_view:"))
async def cb_faq_view(call: CallbackQuery):
    faq_id = int(call.data.split(":")[1])
    faqs = await get_faqs()
    item = next((f for f in faqs if f["id"] == faq_id), None)
    if not item:
        await call.answer("Topilmadi", show_alert=True)
        return

    await call.message.answer(
        f"❓ <b>Savol:</b> {item['question']}\n\n"
        f"✅ <b>Javob:</b> {item['answer']}"
    )
    await call.answer()


# ==================== 15. HELP & ABOUT ====================
@user_router.message(Command("help"))
@user_router.message(F.text == "🆘 Yordam (Help)")
async def menu_help(message: Message):
    help_text = await get_setting("help_text")
    await message.answer(help_text)


@user_router.message(F.text == "🌐 Til / Инфо")
async def menu_about_info(message: Message):
    about = await get_setting("about_text")
    await message.answer(about)


# ==================== 16. AUDIO / VOICE RECOGNITION HANDLER ====================
@user_router.message(F.voice | F.audio | F.video_note)
async def handle_voice_or_audio(message: Message):
    if message.audio and message.audio.title:
        query = f"{message.audio.performer or ''} {message.audio.title}".strip()
        await perform_music_search(message, message.from_user.id, query)
    else:
        await message.answer(
            "🎙 <b>Ovozli xabar qabul qilindi!</b>\n\n"
            "💡 Qo'shiqni tezroq topish uchun qo'shiqdan eshitgan <b>2-3 ta so'zni</b> yoki "
            "<b>ijrochi nomini</b> matn ko'rinishida yozib yuboring — darhol topib beramiz!"
        )


# ==================== 16.5 ROUND VIDEO NOTE (DUMALOQCHA / ROUND) ====================
# Keep track of the last video sent/downloaded by each user so typing "round" converts it immediately!
LAST_USER_VIDEO: Dict[int, Dict[str, str]] = {}


async def send_round_from_video_path(message: Message, video_path: str, status_msg: Message, user_id: int):
    round_path = None
    try:
        round_path = await asyncio.to_thread(convert_video_to_round, video_path)
        if not round_path:
            await status_msg.edit_text("⚠️ Videoni dumaloq (Round) formatga o'tkazib bo'lmadi.")
            return
        try:
            await message.answer_video_note(
                video_note=FSInputFile(round_path),
                length=360
            )
        except Exception:
            # If user has Voice/VideoNote privacy restricted, fallback to sending as square video
            await message.answer_video(
                video=FSInputFile(round_path),
                caption="⭕ <b>Dumaloq video tayyor!</b>\n<i>(Profilingizda Video xabarlar yopiq bo'lgani uchun oddiy video ko'rinishida yuborildi)</i>"
            )
        await increment_user_stat(user_id, "downloads_count")
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Dumaloq video yuborishda xatolik: {str(e)[:120]}")
    finally:
        safe_remove(round_path)


async def send_round_from_telegram_video(message: Message, bot: Bot, file_id: str, user_id: int, fallback_url: str = ""):
    status_msg = await message.answer("⭕ <b>Video dumaloqcha (Round) shaklga o'tkazilmoqda, kuting...</b>")
    local_vid = str(DOWNLOAD_DIR / f"tg_vid_{uuid.uuid4().hex[:8]}.mp4")
    try:
        tg_file = await bot.get_file(file_id)
        await bot.download_file(tg_file.file_path, destination=local_vid)
        await send_round_from_video_path(message, local_vid, status_msg, user_id)
    except Exception as e:
        if fallback_url:
            v_path = None
            try:
                dl_info = await download_video(fallback_url)
                v_path = dl_info["file_path"]
                await send_round_from_video_path(message, v_path, status_msg, user_id)
                return
            except Exception as e2:
                await status_msg.edit_text(f"⚠️ Videoni dumaloq qilib bo'lmadi: {str(e2)[:100]}")
                return
            finally:
                safe_remove(v_path)
        await status_msg.edit_text(f"⚠️ Videoni yuklab bo'lmadi: {str(e)[:100]}")
    finally:
        safe_remove(local_vid)


@user_router.message(Command("round"))
@user_router.message(F.text.regexp(r"(?i)^(round|dumaloq|dumaloqcha|⭕ dumaloq video \(round\))$"))
async def cmd_or_text_round(message: Message, state: FSMContext, bot: Bot):
    # 1. If user replied "round" to an existing video message, convert it immediately!
    if message.reply_to_message and message.reply_to_message.video:
        await send_round_from_telegram_video(
            message, bot, message.reply_to_message.video.file_id, message.from_user.id
        )
        return

    # 2. If user recently downloaded/sent a video in this chat and just typed "round", convert that last video!
    last_vid = LAST_USER_VIDEO.get(message.from_user.id)
    if last_vid and message.text.lower().strip() in ("round", "dumaloq", "dumaloqcha"):
        await send_round_from_telegram_video(
            message,
            bot,
            last_vid.get("file_id", ""),
            message.from_user.id,
            fallback_url=last_vid.get("url", "")
        )
        return

    # 3. Otherwise ask user to send a video or link
    await state.set_state(UserStates.waiting_for_round_video)
    await message.answer(
        "⭕ <b>Dumaloq video (Video Note / Round) yasash bo'limi!</b>\n\n"
        "Quyidagilardan birini yuboring:\n"
        "1️⃣ Telefoningizdan <b>oddiy video fayl</b> yuboring — darhol dumaloqcha qilib beraman.\n"
        "2️⃣ Yoki <b>Instagram / TikTok / YouTube</b> video linkini yuboring — videoni tortib dumaloqcha qilib beraman!",
        reply_markup=get_cancel_kb()
    )


@user_router.message(UserStates.waiting_for_round_video)
async def process_round_video_state(message: Message, state: FSMContext, bot: Bot):
    kb = await build_user_main_kb(message.from_user.id)

    vid_file_id = None
    if message.video:
        vid_file_id = message.video.file_id
    elif message.video_note:
        vid_file_id = message.video_note.file_id
    elif message.document and message.document.mime_type and "video" in message.document.mime_type:
        vid_file_id = message.document.file_id
    elif message.animation:
        vid_file_id = message.animation.file_id

    if vid_file_id:
        await state.clear()
        LAST_USER_VIDEO[message.from_user.id] = {"file_id": vid_file_id, "url": ""}
        await send_round_from_telegram_video(message, bot, vid_file_id, message.from_user.id)
        await message.answer("✅ Tayyor! Asosiy menyudasiz:", reply_markup=kb)
        return

    if message.text:
        url = extract_url(message.text)
        if url:
            await state.clear()
            status_msg = await message.answer("⭕ <b>Linkdagi video yuklanib, dumaloqcha (Round) qilinmoqda...</b>")
            video_path = None
            try:
                dl_info = await download_video(url)
                video_path = dl_info["file_path"]
                await send_round_from_video_path(message, video_path, status_msg, message.from_user.id)
                await message.answer("✅ Tayyor!", reply_markup=kb)
            except Exception as e:
                await status_msg.edit_text(f"❌ Linkdan videoni tortib bo'lmadi: {str(e)[:120]}")
                await message.answer("Asosiy menyu:", reply_markup=kb)
            finally:
                safe_remove(video_path)
            return

        # If user clicked another menu button or typed something else, exit round state cleanly!
        await state.clear()
        await handle_text_or_link(message, bot)
        return

    await message.answer(
        "⚠️ Iltimos, <b>video fayl</b> yuboring yoki <b>Instagram/TikTok/YouTube linkini</b> tashlang!\n"
        "Chiqish uchun «❌ Bekor qilish» tugmasini bosing."
    )


@user_router.message(F.video | F.animation)
async def handle_direct_video_for_round(message: Message, bot: Bot):
    """If a user sends any video directly, convert to Round Video Note!"""
    fid = message.video.file_id if message.video else message.animation.file_id
    LAST_USER_VIDEO[message.from_user.id] = {"file_id": fid, "url": ""}
    await send_round_from_telegram_video(message, bot, fid, message.from_user.id)


@user_router.callback_query(F.data.startswith("make_round:"))
async def cb_make_round(call: CallbackQuery, bot: Bot):
    meta_key = call.data.split(":", 1)[1]
    await call.answer("⭕ Dumaloqcha tayyorlanmoqda...")

    meta = TRACK_META_CACHE.get(meta_key, {})
    fallback_url = meta.get("url", "")

    if call.message.video:
        await send_round_from_telegram_video(
            call.message, bot, call.message.video.file_id, call.from_user.id, fallback_url=fallback_url
        )
        return

    if fallback_url:
        status_msg = await call.message.answer("⭕ <b>Video dumaloqcha (Round) shaklga o'tkazilmoqda...</b>")
        video_path = None
        try:
            dl_info = await download_video(fallback_url)
            video_path = dl_info["file_path"]
            await send_round_from_video_path(call.message, video_path, status_msg, call.from_user.id)
        except Exception as e:
            await status_msg.edit_text(f"⚠️ Xatolik: {str(e)[:120]}")
        finally:
            safe_remove(video_path)
        return

    await call.message.answer("⚠️ Video eskirgan, iltimos videoni yoki linkni qaytadan yuboring!")


# ==================== 17. UNIVERSAL LINK DOWNLOADER & MUSIC SEARCH ====================
async def perform_music_search(message: Message, user_id: int, query: str):
    wait_msg = await message.answer(f"🔍 <b>«{query}»</b> qidirilmoqda, kuting...")
    await increment_user_stat(user_id, "searches_count")
    await log_search(user_id, query)

    try:
        results = await search_music_yt(query, limit=10)
    except Exception as e:
        await wait_msg.edit_text(f"⚠️ Qidirishda xatolik yuz berdi: {e}")
        return

    if not results:
        await wait_msg.edit_text(
            f"😔 Kechirasiz, <b>«{query}»</b> bo'yicha hech narsa topilmadi.\n"
            "Iltimos, qo'shiq nomini boshqacharoq yozib ko'ring."
        )
        return

    session_key = uuid.uuid4().hex[:8]
    SEARCH_CACHE[session_key] = results

    lines = [f"🎧 <b>«{query}»</b> bo'yicha topilgan musiqalar:\n"]
    for idx, item in enumerate(results, start=1):
        lines.append(f"<b>{idx}.</b> {item['title']} <i>({item['duration']})</i>")

    lines.append("\n👇 <i>Yuklab olish uchun mos raqamni bosing:</i>")
    await wait_msg.edit_text(
        "\n".join(lines),
        reply_markup=get_search_results_kb(results, session_key)
    )


@user_router.callback_query(F.data.startswith("dl_track:"))
async def cb_download_selected_track(call: CallbackQuery, bot: Bot):
    parts = call.data.split(":")
    session_key = parts[1]
    idx = int(parts[2])

    results = SEARCH_CACHE.get(session_key)
    if not results or idx >= len(results):
        await call.answer("⚠️ Qidiruv natijasi eskirgan. Qaytadan qidiring!", show_alert=True)
        return

    track = results[idx]
    url = track["url"]
    cache_key = f"aud:{url}"

    # 1. Instant delivery from SQLite file_id cache (0.1 seconds!)
    cached = await get_cached_media(cache_key)
    if cached and cached.get("file_id"):
        await call.answer("⚡ Darhol yuborilmoqda!")
        meta_key = uuid.uuid4().hex[:8]
        TRACK_META_CACHE[meta_key] = {
            "title": cached["title"],
            "url": url,
            "file_id": cached["file_id"],
        }
        me = await bot.get_me()
        await call.message.answer_audio(
            audio=cached["file_id"],
            caption=f"🎵 <b>{cached['title']}</b>\n🤖 @{me.username} | 📢 Reklama: @jorayevvbb",
            reply_markup=get_media_actions_kb(meta_key, is_video=False)
        )
        await increment_user_stat(call.from_user.id, "downloads_count")
        return

    await call.answer(f"⏳ Yuklanmoqda: {track['title'][:30]}...")
    status_msg = await call.message.answer(f"📥 <b>«{track['title']}»</b> yuklab olinmoqda...")

    file_path = None
    try:
        dl_info = await download_audio(url)
        file_path = dl_info["file_path"]
        meta_key = uuid.uuid4().hex[:8]
        TRACK_META_CACHE[meta_key] = {
            "title": dl_info["title"],
            "url": url,
        }

        me = await bot.get_me()
        sent = await call.message.answer_audio(
            audio=FSInputFile(file_path),
            title=dl_info["title"][:60],
            performer=dl_info["performer"][:40],
            duration=dl_info["duration"] or None,
            caption=f"🎵 <b>{dl_info['title']}</b>\n🤖 @{me.username} | 📢 Reklama: @jorayevvbb",
            reply_markup=get_media_actions_kb(meta_key, is_video=False)
        )
        if sent.audio:
            TRACK_META_CACHE[meta_key]["file_id"] = sent.audio.file_id
            await save_cached_media(
                cache_key,
                sent.audio.file_id,
                dl_info["title"],
                dl_info["performer"],
                dl_info["duration"] or 0,
            )

        await increment_user_stat(call.from_user.id, "downloads_count")
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Yuklab olishda xatolik: {str(e)[:150]}")
    finally:
        safe_remove(file_path)


@user_router.callback_query(F.data.startswith("extract_mp3:"))
async def cb_extract_mp3_from_video(call: CallbackQuery, bot: Bot):
    meta_key = call.data.split(":", 1)[1]
    meta = TRACK_META_CACHE.get(meta_key)
    if not meta or not meta.get("url"):
        await call.answer("⚠️ Havola eskirgan, linkni qaytadan yuboring!", show_alert=True)
        return

    url = meta["url"]
    await call.answer("🎵 MP3 formatga ajratilmoqda...")
    status_msg = await call.message.answer("🎧 <b>Videoning MP3 musiqasi yuklab olinmoqda...</b>")

    file_path = None
    try:
        dl_info = await download_audio(url)
        file_path = dl_info["file_path"]
        new_key = uuid.uuid4().hex[:8]
        TRACK_META_CACHE[new_key] = {
            "title": dl_info["title"],
            "url": url,
        }
        me = await bot.get_me()
        sent = await call.message.answer_audio(
            audio=FSInputFile(file_path),
            title=dl_info["title"],
            performer=dl_info["performer"],
            duration=dl_info["duration"] or None,
            caption=f"🎵 <b>{dl_info['title']}</b>\n🤖 @{me.username}",
            reply_markup=get_media_actions_kb(new_key, is_video=False)
        )
        if sent.audio:
            TRACK_META_CACHE[new_key]["file_id"] = sent.audio.file_id
        await increment_user_stat(call.from_user.id, "downloads_count")
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"⚠️ MP3 ajratishda xatolik: {str(e)[:150]}")
    finally:
        safe_remove(file_path)


@user_router.message(F.text)
async def handle_text_or_link(message: Message, bot: Bot):
    text = message.text.strip()

    # 1. Check if it matches a dynamic menu button created by Admin
    dyn_btn = await get_dynamic_button_by_text(text)
    if dyn_btn:
        if dyn_btn.get("url"):
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Havolaga o'tish", url=dyn_btn["url"])]
            ])
            await message.answer(dyn_btn["response_text"], reply_markup=kb)
        else:
            await message.answer(dyn_btn["response_text"])
        return

    # 2. Check if text contains Instagram / TikTok / YouTube / Social media URL
    url = extract_url(text)
    if url:
        vid_cache_key = f"vid:{url}"
        aud_cache_key = f"aud:{url}"
        cached_vid = await get_cached_media(vid_cache_key)
        cached_aud = await get_cached_media(aud_cache_key)

        if cached_vid and cached_vid.get("file_id"):
            me = await bot.get_me()
            meta_key = uuid.uuid4().hex[:8]
            TRACK_META_CACHE[meta_key] = {
                "title": cached_vid["title"],
                "url": url,
                "file_id": cached_vid["file_id"],
            }
            LAST_USER_VIDEO[message.from_user.id] = {
                "file_id": cached_vid["file_id"],
                "url": url,
            }
            sent_vid = await message.answer_video(
                video=cached_vid["file_id"],
                caption=f"🎬 <b>{cached_vid['title'][:100]}</b>\n🤖 @{me.username}",
                reply_markup=get_media_actions_kb(meta_key, is_video=True)
            )
            if sent_vid.video:
                LAST_USER_VIDEO[message.from_user.id] = {
                    "file_id": sent_vid.video.file_id,
                    "url": url,
                }
            if cached_aud and cached_aud.get("file_id"):
                aud_key = uuid.uuid4().hex[:8]
                TRACK_META_CACHE[aud_key] = {
                    "title": cached_aud["title"],
                    "url": url,
                    "file_id": cached_aud["file_id"],
                }
                await message.answer_audio(
                    audio=cached_aud["file_id"],
                    caption=f"🎵 <b>{cached_aud['title'][:100]}</b>\n🤖 @{me.username} | 📢 Reklama: @jorayevvbb",
                    reply_markup=get_media_actions_kb(aud_key, is_video=False)
                )
            else:
                audio_path = None
                try:
                    aud_info = await download_audio(url)
                    audio_path = aud_info["file_path"]
                    aud_key = uuid.uuid4().hex[:8]
                    TRACK_META_CACHE[aud_key] = {"title": aud_info["title"], "url": url}
                    sent_aud = await message.answer_audio(
                        audio=FSInputFile(audio_path),
                        title=aud_info["title"][:60],
                        performer=aud_info["performer"][:40],
                        duration=aud_info["duration"] or None,
                        caption=f"🎵 <b>{aud_info['title'][:100]}</b>\n🤖 @{me.username} | 📢 Reklama: @jorayevvbb",
                        reply_markup=get_media_actions_kb(aud_key, is_video=False)
                    )
                    if sent_aud.audio:
                        TRACK_META_CACHE[aud_key]["file_id"] = sent_aud.audio.file_id
                        await save_cached_media(aud_cache_key, sent_aud.audio.file_id, aud_info["title"])
                except Exception:
                    pass
                finally:
                    safe_remove(audio_path)
            await increment_user_stat(message.from_user.id, "downloads_count")
            return

        status_msg = await message.answer(
            "⚡ <b>Yuklab olinmoqda...</b>"
        )
        video_path = None
        audio_path = None
        try:
            me = await bot.get_me()
            dl_info = await download_video(url)
            video_path = dl_info["file_path"]
            meta_key = uuid.uuid4().hex[:8]
            TRACK_META_CACHE[meta_key] = {
                "title": dl_info["title"],
                "url": url,
            }
            sent_vid = await message.answer_video(
                video=FSInputFile(video_path),
                caption=(
                    f"🎬 <b>{dl_info['title'][:100]}</b>\n"
                    f"🤖 @{me.username}"
                ),
                reply_markup=get_media_actions_kb(meta_key, is_video=True)
            )
            if sent_vid.video:
                TRACK_META_CACHE[meta_key]["file_id"] = sent_vid.video.file_id
                LAST_USER_VIDEO[message.from_user.id] = {
                    "file_id": sent_vid.video.file_id,
                    "url": url,
                }
                await save_cached_media(vid_cache_key, sent_vid.video.file_id, dl_info["title"])

            # Extract MP3 directly from the local video file in 0.4s (NO second network download!)
            try:
                audio_path = await asyncio.to_thread(extract_audio_from_local_video, video_path)
                if audio_path:
                    aud_key = uuid.uuid4().hex[:8]
                    TRACK_META_CACHE[aud_key] = {
                        "title": dl_info["title"],
                        "url": url,
                    }
                    sent_aud = await message.answer_audio(
                        audio=FSInputFile(audio_path),
                        title=dl_info["title"][:60],
                        performer=dl_info["uploader"][:40],
                        duration=dl_info["duration"] or None,
                        caption=f"🎵 <b>{dl_info['title'][:100]}</b>\n🤖 @{me.username}",
                        reply_markup=get_media_actions_kb(aud_key, is_video=False)
                    )
                    if sent_aud.audio:
                        TRACK_META_CACHE[aud_key]["file_id"] = sent_aud.audio.file_id
                        await save_cached_media(aud_key, sent_aud.audio.file_id, dl_info["title"])
                        await save_cached_media(aud_cache_key, sent_aud.audio.file_id, dl_info["title"])
            except Exception:
                pass

            await increment_user_stat(message.from_user.id, "downloads_count")
            await status_msg.delete()
        except Exception:
            try:
                me = await bot.get_me()
                aud_info = await download_audio(url)
                audio_path = aud_info["file_path"]
                meta_key = uuid.uuid4().hex[:8]
                TRACK_META_CACHE[meta_key] = {"title": aud_info["title"], "url": url}
                sent_aud = await message.answer_audio(
                    audio=FSInputFile(audio_path),
                    title=aud_info["title"][:60],
                    performer=aud_info["performer"][:40],
                    duration=aud_info["duration"] or None,
                    caption=f"🎵 <b>{aud_info['title'][:100]}</b>\n🤖 @{me.username}",
                    reply_markup=get_media_actions_kb(meta_key, is_video=False)
                )
                if sent_aud.audio:
                    TRACK_META_CACHE[meta_key]["file_id"] = sent_aud.audio.file_id
                    await save_cached_media(aud_cache_key, sent_aud.audio.file_id, aud_info["title"])
                await increment_user_stat(message.from_user.id, "downloads_count")
                await status_msg.delete()
            except Exception as e2:
                await status_msg.edit_text(f"❌ Yuklab bo'lmadi: {str(e2)[:150]}")
        finally:
            safe_remove(video_path)
            safe_remove(audio_path)
        return

    # 3. Otherwise treat text as a Music Search Query
    await perform_music_search(message, message.from_user.id, text)

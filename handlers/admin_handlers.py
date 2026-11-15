import asyncio
import csv
from pathlib import Path
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext

from config import DOWNLOAD_DIR
from database import (
    is_user_admin,
    get_stats,
    get_all_users,
    get_user,
    set_user_ban,
    set_user_admin,
    get_all_admin_ids,
    get_channels,
    add_channel,
    delete_channel,
    get_setting,
    set_setting,
    get_courses,
    add_course,
    delete_course,
    get_tariffs,
    add_tariff,
    delete_tariff,
    update_payment_status,
    get_faqs,
    add_faq,
    delete_faq,
    get_dynamic_buttons,
    add_dynamic_button,
    delete_dynamic_button,
)
from keyboards import (
    get_admin_main_kb,
    get_admin_channels_kb,
    get_admin_settings_kb,
    get_cancel_kb,
    get_main_menu,
)
from states import AdminStates

admin_router = Router()


async def ensure_admin(user_id: int) -> bool:
    return await is_user_admin(user_id)


# ==================== ADMIN ENTRY POINT ====================
@admin_router.message(Command("admin"))
@admin_router.message(F.text == "🛠 Admin Panel")
async def open_admin_panel(message: Message, state: FSMContext):
    if not await ensure_admin(message.from_user.id):
        return
    await state.clear()
    sub_req = (await get_setting("sub_required", "1")) == "1"
    await message.answer(
        "🛠 <b>Boshqaruv Paneli (Admin Panel)</b>\n\n"
        "Botning barcha qismlarini dinamik tarzda shu yerdan sozlashingiz va boshqarishingiz mumkin:",
        reply_markup=get_admin_main_kb(sub_req)
    )


@admin_router.callback_query(F.data == "adm_back_main")
async def cb_adm_back_main(call: CallbackQuery, state: FSMContext):
    if not await ensure_admin(call.from_user.id):
        return
    await state.clear()
    sub_req = (await get_setting("sub_required", "1")) == "1"
    await call.message.edit_text(
        "🛠 <b>Boshqaruv Paneli (Admin Panel)</b>\n\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=get_admin_main_kb(sub_req)
    )


# ==================== 1. STATISTICS ====================
@admin_router.callback_query(F.data == "adm_stats")
async def cb_adm_stats(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    st = await get_stats()
    text = (
        "📊 <b>Botning Real-Vaqt Statistikasi:</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{st['total_users']} ta</b>\n"
        f"🆕 Bugun qo'shilganlar: <b>{st['today_users']} ta</b>\n"
        f"📥 Jami yuklab olingan media: <b>{st['total_downloads']} marta</b>\n"
        f"🔍 Jami musiqa qidiruvlari: <b>{st['total_searches']} marta</b>\n"
        f"📢 Ulangan majburiy kanallar: <b>{st['channels_count']} ta</b>\n"
        f"⏳ Kutilayotgan to'lov cheklari: <b>{st['pending_payments']} ta</b>"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="adm_stats")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_back_main")]
    ])
    try:
        await call.message.edit_text(text, reply_markup=back_kb)
    except Exception:
        await call.answer("Statistika yangilandi!")


# ==================== 2. BROADCAST (XABAR TARQATISH) ====================
@admin_router.callback_query(F.data == "adm_broadcast")
async def cb_adm_broadcast(call: CallbackQuery, state: FSMContext):
    if not await ensure_admin(call.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_broadcast_msg)
    await call.message.answer(
        "📨 <b>Ommaviy xabar tarqatish (Rassilka):</b>\n\n"
        "Barcha foydalanuvchilarga yuboriladigan xabarni jo'nating "
        "(matn, rasm, video, audio yoki tugmali post bo'lishi mumkin):",
        reply_markup=get_cancel_kb()
    )
    await call.answer()


@admin_router.message(AdminStates.waiting_for_broadcast_msg)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    if not await ensure_admin(message.from_user.id):
        return
    await state.clear()
    users = await get_all_users()
    status_msg = await message.answer(f"⏳ Xabar <b>{len(users)}</b> ta foydalanuvchiga yuborilmoqda...")

    sent_count = 0
    failed_count = 0
    for u in users:
        try:
            await bot.copy_message(
                chat_id=u["user_id"],
                from_chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=message.reply_markup
            )
            sent_count += 1
            await asyncio.sleep(0.04)
        except Exception:
            failed_count += 1

    dyn_btns = await get_dynamic_buttons()
    await status_msg.delete()
    await message.answer(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"🟢 Yetkazildi: <b>{sent_count} ta</b>\n"
        f"🔴 Bloklagan / Xatolik: <b>{failed_count} ta</b>",
        reply_markup=get_main_menu(is_admin=True, dynamic_buttons=dyn_btns)
    )


# ==================== 3. FORCE SUB CHANNELS MANAGEMENT ====================
@admin_router.callback_query(F.data == "adm_channels")
async def cb_adm_channels(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    channels = await get_channels()
    sub_req = (await get_setting("sub_required", "1")) == "1"
    await call.message.edit_text(
        "📢 <b>Majburiy Obuna Kanallari Boshqaruvi:</b>\n\n"
        "📌 <i>Eslatma: Bot kanalda obunani tekshira olishi uchun botni o'sha kanalga <b>Admin</b> qilishingiz kerak!</i>",
        reply_markup=get_admin_channels_kb(channels, sub_req)
    )


@admin_router.callback_query(F.data == "adm_toggle_sub")
async def cb_adm_toggle_sub(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    curr = await get_setting("sub_required", "1")
    new_val = "0" if curr == "1" else "1"
    await set_setting("sub_required", new_val)
    channels = await get_channels()
    await call.answer("Majburiy obuna holati o'zgartirildi!")
    await call.message.edit_reply_markup(
        reply_markup=get_admin_channels_kb(channels, new_val == "1")
    )


@admin_router.callback_query(F.data.startswith("adm_del_ch:"))
async def cb_adm_del_ch(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    ch_id = int(call.data.split(":")[1])
    await delete_channel(ch_id)
    channels = await get_channels()
    sub_req = (await get_setting("sub_required", "1")) == "1"
    await call.answer("🗑 Kanal o'chirildi!")
    await call.message.edit_reply_markup(
        reply_markup=get_admin_channels_kb(channels, sub_req)
    )


@admin_router.callback_query(F.data == "adm_add_ch")
async def cb_adm_add_ch(call: CallbackQuery, state: FSMContext):
    if not await ensure_admin(call.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_channel_id)
    await call.message.answer(
        "📢 <b>Yangi kanal qo'shish (1/3):</b>\n\n"
        "Kanalning <b>@username</b> (masalan: <code>@my_channel</code>) yoki "
        "<b>Chat ID</b> raqamini (masalan: <code>-100123456789</code>) yuboring:\n"
        "<i>(Avval botni o'sha kanalga Admin qilib qo'ying!)</i>",
        reply_markup=get_cancel_kb()
    )
    await call.answer()


@admin_router.message(AdminStates.waiting_for_channel_id, F.text)
async def process_ch_id(message: Message, state: FSMContext):
    await state.update_data(chat_id=message.text.strip())
    await state.set_state(AdminStates.waiting_for_channel_title)
    await message.answer(
        "📢 <b>(2/3) Tugmada ko'rinadigan kanal nomini yozing:</b>\n"
        "<i>Masalan: Bizning Rasmiy Kanal</i>"
    )


@admin_router.message(AdminStates.waiting_for_channel_title, F.text)
async def process_ch_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminStates.waiting_for_channel_link)
    await message.answer(
        "📢 <b>(3/3) Kanalga o'tish havolasini (linkini) yuboring:</b>\n"
        "<i>Masalan: https://t.me/my_channel</i>"
    )


@admin_router.message(AdminStates.waiting_for_channel_link, F.text)
async def process_ch_link(message: Message, state: FSMContext):
    data = await state.get_data()
    link = message.text.strip()
    if not link.startswith("http"):
        link = "https://t.me/" + link.lstrip("@")
    await add_channel(data["chat_id"], data["title"], link)
    await state.clear()
    dyn_btns = await get_dynamic_buttons()
    await message.answer(
        f"✅ <b>«{data['title']}»</b> majburiy obuna kanallariga muvaffaqiyatli qo'shildi!",
        reply_markup=get_main_menu(is_admin=True, dynamic_buttons=dyn_btns)
    )


# ==================== 4. DYNAMIC TEXT & LOCATION SETTINGS ====================
@admin_router.callback_query(F.data == "adm_settings")
async def cb_adm_settings(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    await call.message.edit_text(
        "⚙️ <b>Bot Matnlari va Lokatsiyasini Dinamik Sozlash:</b>\n\n"
        "Qaysi ma'lumotni o'zgartirmoqchisiz? Tanlang:",
        reply_markup=get_admin_settings_kb()
    )


@admin_router.callback_query(F.data.startswith("adm_set:"))
async def cb_adm_set_key(call: CallbackQuery, state: FSMContext):
    if not await ensure_admin(call.from_user.id):
        return
    key = call.data.split(":", 1)[1]
    curr_val = await get_setting(key)
    await state.update_data(setting_key=key)
    await state.set_state(AdminStates.waiting_for_setting_value)
    await call.message.answer(
        f"📝 <b>Hozirgi qiymat:</b>\n\n{curr_val}\n\n"
        "👇 <b>Yangi matn yoki qiymatni yozib yuboring</b> (HTML teglaridan foydalanishingiz mumkin):",
        reply_markup=get_cancel_kb()
    )
    await call.answer()


@admin_router.message(AdminStates.waiting_for_setting_value, F.text)
async def process_setting_value(message: Message, state: FSMContext):
    data = await state.get_data()
    key = data["setting_key"]
    await set_setting(key, message.html_text or message.text)
    await state.clear()
    dyn_btns = await get_dynamic_buttons()
    await message.answer(
        f"✅ <b>Sozlama ({key}) muvaffaqiyatli yangilandi!</b>",
        reply_markup=get_main_menu(is_admin=True, dynamic_buttons=dyn_btns)
    )


@admin_router.callback_query(F.data == "adm_set_coords")
async def cb_adm_set_coords(call: CallbackQuery, state: FSMContext):
    if not await ensure_admin(call.from_user.id):
        return
    lat = await get_setting("location_lat")
    lon = await get_setting("location_lon")
    await state.set_state(AdminStates.waiting_for_location_coords)
    await call.message.answer(
        f"🗺 <b>Hozirgi GPS koordinatalar:</b> <code>{lat}, {lon}</code>\n\n"
        "Yangi lokatsiyani Telegram orqali <b>📍 Геопозиция (Location)</b> qilib yuboring "
        "yoki vergul bilan yozib yuboring (masalan: <code>41.311081, 69.240562</code>):",
        reply_markup=get_cancel_kb()
    )
    await call.answer()


@admin_router.message(AdminStates.waiting_for_location_coords)
async def process_location_coords(message: Message, state: FSMContext):
    lat, lon = None, None
    if message.location:
        lat = str(message.location.latitude)
        lon = str(message.location.longitude)
    elif message.text and "," in message.text:
        parts = message.text.split(",")
        try:
            lat = str(float(parts[0].strip()))
            lon = str(float(parts[1].strip()))
        except Exception:
            pass

    if not lat or not lon:
        await message.answer("⚠️ Iltimos, lokatsiya yuboring yoki `41.311081, 69.240562` formatida yozing!")
        return

    await set_setting("location_lat", lat)
    await set_setting("location_lon", lon)
    await state.clear()
    dyn_btns = await get_dynamic_buttons()
    await message.answer(
        f"✅ <b>Yangi GPS koordinatalar saqlandi:</b> {lat}, {lon}",
        reply_markup=get_main_menu(is_admin=True, dynamic_buttons=dyn_btns)
    )


# ==================== 5. PREMIUM TARIFFS & PAYMENT VERIFICATION ====================
@admin_router.callback_query(F.data == "adm_tariffs")
async def cb_adm_tariffs(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    tariffs = await get_tariffs()
    rows = []
    for t in tariffs:
        rows.append([
            InlineKeyboardButton(text=f"{t['name']} ({t['price']})", callback_data="noop"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_del_tariff:{t['id']}")
        ])
    rows.append([InlineKeyboardButton(text="➕ Yangi tarif qo'shish", callback_data="adm_add_tariff")])
    rows.append([InlineKeyboardButton(text="💳 Karta va Premium matnini o'zgartirish", callback_data="adm_set:premium_text")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_back_main")])

    await call.message.edit_text(
        "💎 <b>Telegram Premium va Stars Tariflari Boshqaruvi:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@admin_router.callback_query(F.data.startswith("adm_del_tariff:"))
async def cb_adm_del_tariff(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    t_id = int(call.data.split(":")[1])
    await delete_tariff(t_id)
    await call.answer("🗑 Tarif o'chirildi!")
    await cb_adm_tariffs(call)


@admin_router.callback_query(F.data == "adm_add_tariff")
async def cb_adm_add_tariff(call: CallbackQuery, state: FSMContext):
    if not await ensure_admin(call.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_tariff_name)
    await call.message.answer(
        "💎 <b>Yangi tarif nomini kiriting (1/3):</b>\n"
        "<i>Masalan: 💎 Telegram Premium — 1 oylik</i>",
        reply_markup=get_cancel_kb()
    )
    await call.answer()


@admin_router.message(AdminStates.waiting_for_tariff_name, F.text)
async def process_tariff_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminStates.waiting_for_tariff_price)
    await message.answer("💰 <b>Tarif narxini kiriting (2/3):</b>\n<i>Masalan: 55,000 so'm</i>")


@admin_router.message(AdminStates.waiting_for_tariff_price, F.text)
async def process_tariff_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text.strip())
    await state.set_state(AdminStates.waiting_for_tariff_desc)
    await message.answer("ℹ️ <b>Tarif haqida qisqacha izoh kiriting (3/3):</b>")


@admin_router.message(AdminStates.waiting_for_tariff_desc, F.text)
async def process_tariff_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    await add_tariff(data["name"], data["price"], message.text.strip())
    await state.clear()
    dyn_btns = await get_dynamic_buttons()
    await message.answer(
        f"✅ <b>«{data['name']}»</b> tarifi muvaffaqiyatli qo'shildi!",
        reply_markup=get_main_menu(is_admin=True, dynamic_buttons=dyn_btns)
    )


@admin_router.callback_query(F.data.startswith("pay_ok:"))
async def cb_pay_approve(call: CallbackQuery, bot: Bot):
    if not await ensure_admin(call.from_user.id):
        return
    _, pay_id_str, user_id_str = call.data.split(":")
    pay_id, user_id = int(pay_id_str), int(user_id_str)
    payment = await update_payment_status(pay_id, "approved")

    await call.answer("✅ To'lov tasdiqlandi!")
    try:
        await call.message.edit_caption(
            caption=(call.message.caption or "") + f"\n\n✅ <b>TASDIQLANDI ({call.from_user.first_name})</b>"
        )
    except Exception:
        pass

    try:
        t_name = payment["tariff_name"] if payment else "Telegram Premium"
        await bot.send_message(
            user_id,
            f"🎉 <b>Tabriklaymiz! Buyurtmangiz (#{pay_id}) tasdiqlandi!</b>\n\n"
            f"💎 Xizmat: <b>{t_name}</b> muvaffaqiyatli faollashtirildi!\n"
            "Bizning xizmatimizdan foydalanganingiz uchun rahmat!"
        )
    except Exception:
        pass


@admin_router.callback_query(F.data.startswith("pay_no:"))
async def cb_pay_reject(call: CallbackQuery, bot: Bot):
    if not await ensure_admin(call.from_user.id):
        return
    _, pay_id_str, user_id_str = call.data.split(":")
    pay_id, user_id = int(pay_id_str), int(user_id_str)
    await update_payment_status(pay_id, "rejected")

    await call.answer("❌ Buyurtma rad etildi!")
    try:
        await call.message.edit_caption(
            caption=(call.message.caption or "") + f"\n\n❌ <b>RAD ETILDI ({call.from_user.first_name})</b>"
        )
    except Exception:
        pass

    try:
        await bot.send_message(
            user_id,
            f"⚠️ <b>Sizning #{pay_id}-sonli to'lov chekingiz admin tomonidan rad etildi.</b>\n"
            "Agar xatolik bo'lsa, «✍️ Adminga bog'lanish» bo'limi orqali murojaat qiling."
        )
    except Exception:
        pass


# ==================== 6. REPLY TO USER SUPPORT / PAYMENT ====================
@admin_router.callback_query(F.data.startswith("admin_reply:"))
async def cb_admin_reply_user(call: CallbackQuery, state: FSMContext):
    if not await ensure_admin(call.from_user.id):
        return
    target_user_id = int(call.data.split(":")[1])
    await state.update_data(reply_target_id=target_user_id)
    await state.set_state(AdminStates.waiting_for_reply_message)
    await call.message.answer(
        f"💬 <b>ID <code>{target_user_id}</code> foydalanuvchiga yuboriladigan javob xabarini yozing</b> "
        "(matn, rasm yoki ovozli xabar bo'lishi mumkin):",
        reply_markup=get_cancel_kb()
    )
    await call.answer()


@admin_router.message(AdminStates.waiting_for_reply_message)
async def process_admin_reply_message(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_id = data.get("reply_target_id")
    await state.clear()
    dyn_btns = await get_dynamic_buttons()

    try:
        if message.text:
            await bot.send_message(
                target_id,
                f"👨‍💻 <b>Admindan javob xabari:</b>\n\n{message.text}"
            )
        else:
            await bot.send_message(target_id, "👨‍💻 <b>Admindan javob xabari:</b>")
            await bot.copy_message(
                chat_id=target_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
        await message.answer(
            f"✅ <b>Javobingiz foydalanuvchiga (ID: {target_id}) yetkazildi!</b>",
            reply_markup=get_main_menu(is_admin=True, dynamic_buttons=dyn_btns)
        )
    except Exception as e:
        await message.answer(
            f"❌ Xabar yetkazilmadi (foydalanuvchi botni bloklagan bo'lishi mumkin): {e}",
            reply_markup=get_main_menu(is_admin=True, dynamic_buttons=dyn_btns)
        )


# ==================== 7. COURSES MANAGEMENT ====================
@admin_router.callback_query(F.data == "adm_courses")
async def cb_adm_courses(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    courses = await get_courses()
    rows = []
    for c in courses:
        rows.append([
            InlineKeyboardButton(text=f"🎓 {c['title']}", callback_data="noop"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_del_course:{c['id']}")
        ])
    rows.append([InlineKeyboardButton(text="➕ Yangi kurs qo'shish", callback_data="adm_add_course")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_back_main")])

    await call.message.edit_text(
        "🎓 <b>O'quv Kurslarini Boshqarish:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@admin_router.callback_query(F.data.startswith("adm_del_course:"))
async def cb_adm_del_course(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    c_id = int(call.data.split(":")[1])
    await delete_course(c_id)
    await call.answer("🗑 Kurs o'chirildi!")
    await cb_adm_courses(call)


@admin_router.callback_query(F.data == "adm_add_course")
async def cb_adm_add_course(call: CallbackQuery, state: FSMContext):
    if not await ensure_admin(call.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_course_title)
    await call.message.answer("🎓 <b>Yangi kurs nomini kiriting (1/4):</b>", reply_markup=get_cancel_kb())
    await call.answer()


@admin_router.message(AdminStates.waiting_for_course_title, F.text)
async def process_course_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminStates.waiting_for_course_desc)
    await message.answer("📖 <b>Kurs haqida batafsil ma'lumot kiriting (2/4):</b>")


@admin_router.message(AdminStates.waiting_for_course_desc, F.text)
async def process_course_desc(message: Message, state: FSMContext):
    await state.update_data(desc=message.text.strip())
    await state.set_state(AdminStates.waiting_for_course_price)
    await message.answer("💰 <b>Kurs narxini kiriting (3/4):</b>\n<i>Masalan: 600,000 so'm / oy</i>")


@admin_router.message(AdminStates.waiting_for_course_price, F.text)
async def process_course_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text.strip())
    await state.set_state(AdminStates.waiting_for_course_duration)
    await message.answer("⏳ <b>Kurs davomiyligini kiriting (4/4):</b>\n<i>Masalan: 4 oy (haftada 3 kun)</i>")


@admin_router.message(AdminStates.waiting_for_course_duration, F.text)
async def process_course_duration(message: Message, state: FSMContext):
    data = await state.get_data()
    await add_course(data["title"], data["desc"], data["price"], message.text.strip())
    await state.clear()
    dyn_btns = await get_dynamic_buttons()
    await message.answer(
        f"✅ <b>«{data['title']}»</b> kursi muvaffaqiyatli qo'shildi!",
        reply_markup=get_main_menu(is_admin=True, dynamic_buttons=dyn_btns)
    )


# ==================== 8. DYNAMIC MENU BUTTONS BUILDER ====================
@admin_router.callback_query(F.data == "adm_dyn_buttons")
async def cb_adm_dyn_buttons(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    btns = await get_dynamic_buttons()
    rows = []
    for b in btns:
        rows.append([
            InlineKeyboardButton(text=f"🔘 {b['button_text']}", callback_data="noop"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_del_dynbtn:{b['id']}")
        ])
    rows.append([InlineKeyboardButton(text="➕ Yangi menyu tugmasi qo'shish", callback_data="adm_add_dynbtn")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_back_main")])

    await call.message.edit_text(
        "🎛 <b>Dinamik Menyu Konstruktori:</b>\n\n"
        "Bu bo'lim orqali dasturchisiz asosiy menyuga yangi tugmalar (masalan: <i>🎁 Aksiyalar, 📢 Yangiliklar, 💼 Vakansiyalar</i>) "
        "qo'shishingiz va javob matnini belgilashingiz mumkin!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@admin_router.callback_query(F.data.startswith("adm_del_dynbtn:"))
async def cb_adm_del_dynbtn(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    b_id = int(call.data.split(":")[1])
    await delete_dynamic_button(b_id)
    await call.answer("🗑 Tugma o'chirildi!")
    await cb_adm_dyn_buttons(call)


@admin_router.callback_query(F.data == "adm_add_dynbtn")
async def cb_adm_add_dynbtn(call: CallbackQuery, state: FSMContext):
    if not await ensure_admin(call.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_dyn_btn_text)
    await call.message.answer(
        "🎛 <b>Yangi tugma nomini yozing (1/3):</b>\n<i>Masalan: 🎁 Haftalik Konkurs</i>",
        reply_markup=get_cancel_kb()
    )
    await call.answer()


@admin_router.message(AdminStates.waiting_for_dyn_btn_text, F.text)
async def process_dynbtn_text(message: Message, state: FSMContext):
    await state.update_data(btn_text=message.text.strip())
    await state.set_state(AdminStates.waiting_for_dyn_btn_resp)
    await message.answer(
        "💬 <b>Foydalanuvchi bu tugmani bosganda chiqadigan matnni yuboring (2/3):</b>"
    )


@admin_router.message(AdminStates.waiting_for_dyn_btn_resp, F.text)
async def process_dynbtn_resp(message: Message, state: FSMContext):
    await state.update_data(resp_text=message.html_text or message.text)
    await state.set_state(AdminStates.waiting_for_dyn_btn_url)
    await message.answer(
        "🔗 <b>Xabar tagida havola (URL) tugmasi bo'lsinmi? (3/3):</b>\n"
        "Agar bo'lsa link yuboring (masalan: <code>https://t.me/kanal</code>), kerak bo'lmasa <code>0</code> deb yozing:"
    )


@admin_router.message(AdminStates.waiting_for_dyn_btn_url, F.text)
async def process_dynbtn_url(message: Message, state: FSMContext):
    data = await state.get_data()
    url = message.text.strip()
    if url == "0" or not url.startswith("http"):
        url = ""
    await add_dynamic_button(data["btn_text"], data["resp_text"], url)
    await state.clear()
    dyn_btns = await get_dynamic_buttons()
    await message.answer(
        f"✅ <b>«{data['btn_text']}»</b> tugmasi asosiy menyuga qo'shildi!",
        reply_markup=get_main_menu(is_admin=True, dynamic_buttons=dyn_btns)
    )


# ==================== 9. FAQ MANAGEMENT ====================
@admin_router.callback_query(F.data == "adm_faqs")
async def cb_adm_faqs(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    faqs = await get_faqs()
    rows = []
    for f in faqs:
        rows.append([
            InlineKeyboardButton(text=f"❓ {f['question'][:32]}", callback_data="noop"),
            InlineKeyboardButton(text="🗑", callback_data=f"adm_del_faq:{f['id']}")
        ])
    rows.append([InlineKeyboardButton(text="➕ Yangi savol-javob qo'shish", callback_data="adm_add_faq")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_back_main")])

    await call.message.edit_text(
        "❓ <b>Ko'p beriladigan savollar (FAQ) boshqaruvi:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@admin_router.callback_query(F.data.startswith("adm_del_faq:"))
async def cb_adm_del_faq(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    f_id = int(call.data.split(":")[1])
    await delete_faq(f_id)
    await call.answer("🗑 O'chirildi!")
    await cb_adm_faqs(call)


@admin_router.callback_query(F.data == "adm_add_faq")
async def cb_adm_add_faq(call: CallbackQuery, state: FSMContext):
    if not await ensure_admin(call.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_faq_q)
    await call.message.answer("❓ <b>Savol matnini yozing (1/2):</b>", reply_markup=get_cancel_kb())
    await call.answer()


@admin_router.message(AdminStates.waiting_for_faq_q, F.text)
async def process_faq_q(message: Message, state: FSMContext):
    await state.update_data(q=message.text.strip())
    await state.set_state(AdminStates.waiting_for_faq_a)
    await message.answer("✅ <b>Savolga javob matnini yozing (2/2):</b>")


@admin_router.message(AdminStates.waiting_for_faq_a, F.text)
async def process_faq_a(message: Message, state: FSMContext):
    data = await state.get_data()
    await add_faq(data["q"], message.text.strip())
    await state.clear()
    dyn_btns = await get_dynamic_buttons()
    await message.answer(
        "✅ <b>Yangi FAQ muvaffaqiyatli qo'shildi!</b>",
        reply_markup=get_main_menu(is_admin=True, dynamic_buttons=dyn_btns)
    )


# ==================== 10. USER SEARCH / BAN / UNBAN & ADMIN MANAGE ====================
@admin_router.callback_query(F.data == "adm_user_manage")
async def cb_adm_user_manage(call: CallbackQuery, state: FSMContext):
    if not await ensure_admin(call.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_user_search)
    await call.message.answer(
        "👤 <b>Foydalanuvchini topish va boshqarish:</b>\n\n"
        "Foydalanuvchining <b>Telegram ID</b> raqamini yuboring:",
        reply_markup=get_cancel_kb()
    )
    await call.answer()


@admin_router.message(AdminStates.waiting_for_user_search, F.text)
async def process_user_search(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamdan iborat User ID kiriting!")
        return
    uid = int(message.text.strip())
    u = await get_user(uid)
    await state.clear()
    dyn_btns = await get_dynamic_buttons()

    if not u:
        await message.answer(
            "❌ Bunday ID ga ega foydalanuvchi bazada topilmadi.",
            reply_markup=get_main_menu(is_admin=True, dynamic_buttons=dyn_btns)
        )
        return

    ban_btn_text = "🟢 Bandan chiqarish (Unban)" if u["is_banned"] else "🚫 Bloklash (Ban)"
    ban_action = f"adm_unban:{uid}" if u["is_banned"] else f"adm_ban:{uid}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ban_btn_text, callback_data=ban_action)],
        [InlineKeyboardButton(text="💬 Xabar yozish", callback_data=f"admin_reply:{uid}")]
    ])

    await message.answer(
        f"👤 <b>Foydalanuvchi ma'lumotlari:</b>\n\n"
        f"🆔 ID: <code>{u['user_id']}</code>\n"
        f"🙍‍♂️ Ism: {u['full_name']}\n"
        f"🌐 Username: @{u['username'] or 'yoq'}\n"
        f"📥 Yuklashlar: {u['downloads_count']} ta\n"
        f"💰 Balans: {u['balance']} so'm\n"
        f"🔒 Holati: {'🚫 Bloklangan' if u['is_banned'] else '🟢 Faol'}",
        reply_markup=kb
    )


@admin_router.callback_query(F.data.startswith("adm_ban:"))
async def cb_adm_ban(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    uid = int(call.data.split(":")[1])
    await set_user_ban(uid, 1)
    await call.answer("🚫 Foydalanuvchi bloklandi!", show_alert=True)
    await call.message.edit_text(f"🚫 Foydalanuvchi (ID: <code>{uid}</code>) bloklandi.")


@admin_router.callback_query(F.data.startswith("adm_unban:"))
async def cb_adm_unban(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    uid = int(call.data.split(":")[1])
    await set_user_ban(uid, 0)
    await call.answer("🟢 Foydalanuvchi bandan chiqarildi!", show_alert=True)
    await call.message.edit_text(f"🟢 Foydalanuvchi (ID: <code>{uid}</code>) bandan chiqarildi.")


@admin_router.callback_query(F.data == "adm_admins")
async def cb_adm_admins(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    admin_ids = await get_all_admin_ids()
    rows = []
    for aid in admin_ids:
        rows.append([
            InlineKeyboardButton(text=f"👮‍♂️ ID: {aid}", callback_data="noop"),
            InlineKeyboardButton(text="❌ Huquqni olish", callback_data=f"adm_rm_admin:{aid}")
        ])
    rows.append([InlineKeyboardButton(text="➕ Yangi Admin tayinlash", callback_data="adm_add_admin")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_back_main")])

    await call.message.edit_text(
        "👮‍♂️ <b>Bot Adminlari Boshqaruvi:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@admin_router.callback_query(F.data.startswith("adm_rm_admin:"))
async def cb_adm_rm_admin(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    aid = int(call.data.split(":")[1])
    if aid == call.from_user.id:
        await call.answer("⚠️ O'zingizni adminlikdan o'chira olmaysiz!", show_alert=True)
        return
    await set_user_admin(aid, 0)
    await call.answer("Adminlik huquqi olindi!")
    await cb_adm_admins(call)


@admin_router.callback_query(F.data == "adm_add_admin")
async def cb_adm_add_admin(call: CallbackQuery, state: FSMContext):
    if not await ensure_admin(call.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_new_admin_id)
    await call.message.answer(
        "👮‍♂️ <b>Yangi admin qilinadigan foydalanuvchining Telegram ID raqamini yuboring:</b>\n"
        "<i>(U avval botga /start bosgan bo'lishi kerak)</i>",
        reply_markup=get_cancel_kb()
    )
    await call.answer()


@admin_router.message(AdminStates.waiting_for_new_admin_id, F.text)
async def process_new_admin_id(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Faqat raqam kiriting!")
        return
    aid = int(message.text.strip())
    await set_user_admin(aid, 1)
    await state.clear()
    dyn_btns = await get_dynamic_buttons()
    await message.answer(
        f"✅ <b>ID <code>{aid}</code> foydalanuvchiga Admin huquqi berildi!</b>",
        reply_markup=get_main_menu(is_admin=True, dynamic_buttons=dyn_btns)
    )


# ==================== 11. EXPORT DATABASE TO CSV ====================
@admin_router.callback_query(F.data == "adm_export_csv")
async def cb_adm_export_csv(call: CallbackQuery):
    if not await ensure_admin(call.from_user.id):
        return
    await call.answer("📥 CSV fayl tayyorlanmoqda...")
    users = await get_all_users()
    csv_path = DOWNLOAD_DIR / "users_export.csv"

    with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["User ID", "Full Name", "Username", "Downloads", "Searches", "Balance", "Joined At"])
        for u in users:
            writer.writerow([
                u["user_id"],
                u["full_name"],
                u["username"],
                u["downloads_count"],
                u["searches_count"],
                u["balance"],
                u["joined_at"],
            ])

    await call.message.answer_document(
        document=FSInputFile(str(csv_path)),
        caption=f"📊 <b>Barcha foydalanuvchilar bazasi (CSV)</b>\nJami: <b>{len(users)} ta</b> foydalanuvchi."
    )


@admin_router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()

import time
from typing import Callable, Dict, Any, Awaitable, List, Tuple
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery
from database import get_user, get_channels, get_setting, is_user_admin
from keyboards import get_sub_channels_kb

# 30-second cache for verified channel subscriptions so every click is instant
_SUB_PASS_CACHE: Dict[int, float] = {}


async def check_unsubscribed_channels(bot: Bot, user_id: int, force_check: bool = False) -> List[Dict[str, Any]]:
    if not force_check and _SUB_PASS_CACHE.get(user_id, 0) > time.time():
        return []

    sub_req = await get_setting("sub_required", "1")
    if sub_req != "1":
        return []

    if await is_user_admin(user_id):
        _SUB_PASS_CACHE[user_id] = time.time() + 120
        return []

    channels = await get_channels()
    if not channels:
        _SUB_PASS_CACHE[user_id] = time.time() + 60
        return []

    unsubscribed = []
    for ch in channels:
        chat_id = ch["chat_id"]
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in ("left", "kicked"):
                unsubscribed.append(ch)
        except Exception:
            continue

    if not unsubscribed:
        _SUB_PASS_CACHE[user_id] = time.time() + 45

    return unsubscribed


class AuthAndSubMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        bot: Bot = data["bot"]
        user = getattr(event, "from_user", None)
        if not user or user.is_bot:
            return await handler(event, data)

        # 1. Check ban status
        db_user = await get_user(user.id)
        if db_user and db_user.get("is_banned") == 1 and not await is_user_admin(user.id):
            if isinstance(event, Message):
                await event.answer("🚫 <b>Siz botdan foydalanishdan chetlatilgansiz (Ban).</b>")
            elif isinstance(event, CallbackQuery):
                await event.answer("🚫 Siz bloklangansiz!", show_alert=True)
            return

        # Allow /start and check_subs callback to pass through or handle cleanly
        if isinstance(event, CallbackQuery) and event.data == "check_subs":
            return await handler(event, data)

        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)

        # 2. Check mandatory channel subscription
        unsubscribed = await check_unsubscribed_channels(bot, user.id)
        if unsubscribed:
            text = (
                "🛑 <b>Botdan to'liq foydalanish va musiqa/video yuklab olish uchun "
                "quyidagi homiy kanallarimizga obuna bo'ling:</b>\n\n"
                "Obuna bo'lgach, <b>«✅ Obuna bo'ldim (Tekshirish)»</b> tugmasini bosing."
            )
            kb = get_sub_channels_kb(unsubscribed)
            if isinstance(event, Message):
                await event.answer(text, reply_markup=kb)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(text, reply_markup=kb)
                await event.answer("⚠️ Avval kanallarga obuna bo'ling!", show_alert=True)
            return

        return await handler(event, data)

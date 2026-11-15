from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    # Support / Contact Admin
    waiting_for_support_msg = State()
    # Telegram Premium Purchase
    waiting_for_premium_username = State()
    waiting_for_premium_receipt = State()
    # Course Enrollment
    waiting_for_course_phone = State()
    # Lyrics search
    waiting_for_lyrics_query = State()
    # Round Video Note (Dumaloqcha)
    waiting_for_round_video = State()


class AdminStates(StatesGroup):
    # Reply to User Support / Payment
    waiting_for_reply_message = State()

    # Broadcast
    waiting_for_broadcast_msg = State()

    # Force Sub Channel Add
    waiting_for_channel_id = State()
    waiting_for_channel_title = State()
    waiting_for_channel_link = State()

    # Dynamic Text Settings Edit
    waiting_for_setting_value = State()
    waiting_for_location_coords = State()

    # Course Add
    waiting_for_course_title = State()
    waiting_for_course_desc = State()
    waiting_for_course_price = State()
    waiting_for_course_duration = State()

    # Premium Tariff Add
    waiting_for_tariff_name = State()
    waiting_for_tariff_price = State()
    waiting_for_tariff_desc = State()

    # FAQ Add
    waiting_for_faq_q = State()
    waiting_for_faq_a = State()

    # Dynamic Menu Button Add
    waiting_for_dyn_btn_text = State()
    waiting_for_dyn_btn_resp = State()
    waiting_for_dyn_btn_url = State()

    # User Management
    waiting_for_user_search = State()
    waiting_for_new_admin_id = State()

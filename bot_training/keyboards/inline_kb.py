from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import LEVELS

def get_levels_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for key, value in LEVELS.items():
        button = InlineKeyboardButton(
            text=value,
            callback_data=f"level_{key}"
        )
        keyboard.inline_keyboard.append([button])  # Добавляем кнопку в новую строку
    
    return keyboard

def get_dates_keyboard(dates: list):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for date in dates:
        button = InlineKeyboardButton(
            text=date,
            callback_data=f"date_{date}"
        )
        keyboard.inline_keyboard.append([button])  # Добавляем кнопку в новую строку
    
    back_button = InlineKeyboardButton(
        text="◀️ Назад к уровням",
        callback_data="back_to_levels"
    )
    keyboard.inline_keyboard.append([back_button])  # Добавляем кнопку "Назад"
    
    return keyboard

def get_payment_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    pay_button = InlineKeyboardButton(
        text="💳 Оплатить",
        callback_data="make_payment"
    )
    back_button = InlineKeyboardButton(
        text="◀️ Назад к датам",
        callback_data="back_to_dates"
    )
    
    keyboard.inline_keyboard.append([pay_button])  # Добавляем кнопку "Оплатить"
    keyboard.inline_keyboard.append([back_button])  # Добавляем кнопку "Назад"
    
    return keyboard

# keyboards/inline_kb.py - добавляем новую клавиатуру
def get_payment_confirmation_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    pay_button = InlineKeyboardButton(
        text="💳 Перейти к оплате",
        callback_data="start_payment"
    )
    back_button = InlineKeyboardButton(
        text="◀️ Назад к датам",
        callback_data="back_to_dates"
    )
    
    keyboard.inline_keyboard.append([pay_button])
    keyboard.inline_keyboard.append([back_button])
    
    return keyboard

# Добавляем в конец inline_kb.py

def get_receipt_confirmation_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я отправил чек", callback_data="receipt_sent")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
    ])
    return keyboard

def get_admin_payment_keyboard(user_id: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"confirm_payment_{user_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_payment_{user_id}")]
    ])
    return keyboard
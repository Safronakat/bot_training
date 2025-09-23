from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import logging

from config import LEVELS
from services.google_sheets import GoogleSheetsManager
from keyboards.inline_kb import get_dates_keyboard, get_levels_keyboard
from data.temporary_storage import TemporaryStorage

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(lambda c: c.data.startswith('level_'))
async def process_level_selection(callback: CallbackQuery, state: FSMContext):
    try:
        level_key = callback.data.split('_')[1]
        
        if level_key not in LEVELS:
            await callback.answer("Неверный уровень")
            return
        
        # Сохраняем уровень во временные данные
        user_data = TemporaryStorage.get_user_data(callback.from_user.id)
        user_data['level'] = LEVELS[level_key]
        user_data['level_key'] = level_key
        TemporaryStorage.save_user_data(callback.from_user.id, user_data)
        
        # Получаем даты из Google Sheets
        from config import GOOGLE_SHEETS_CREDENTIALS, SHEET_URL  # Импортируем напрямую
        sheets_manager = GoogleSheetsManager(GOOGLE_SHEETS_CREDENTIALS, SHEET_URL)
        
        dates = sheets_manager.get_dates_for_level(LEVELS[level_key])
        
        # ДЕБАГ: Логируем что ищем и что нашли
        logger.info(f"Searching dates for level: '{LEVELS[level_key]}'")
        logger.info(f"Found dates: {dates}")
        
        if not dates:
            message_text = (
                "❌ На данный момент нет доступных дат для этого уровня.\n"
                "Пожалуйста, выберите другой уровень или попробуйте позже."
            )
            keyboard = get_levels_keyboard()
        else:
            message_text = f"📅 Выберите дату для уровня {LEVELS[level_key]}:"
            keyboard = get_dates_keyboard(dates)
        
        # Пытаемся обновить сообщение с обработкой ошибки
        try:
            await callback.message.edit_text(
                message_text,
                reply_markup=keyboard
            )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                # Игнорируем ошибку, если сообщение не изменилось
                logger.info("Message not modified - ignoring error")
                pass
            else:
                # Пробрасываем другие ошибки
                raise
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in level selection: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз.", show_alert=True)

@router.callback_query(lambda c: c.data == 'back_to_levels')
async def back_to_levels(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "Выберите уровень обучения:",
            reply_markup=get_levels_keyboard()
        )
        await callback.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise
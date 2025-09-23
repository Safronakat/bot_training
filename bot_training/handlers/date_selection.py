from aiogram import Router
from aiogram.types import CallbackQuery

from data.temporary_storage import TemporaryStorage
from keyboards.inline_kb import get_payment_confirmation_keyboard

router = Router()

@router.callback_query(lambda c: c.data.startswith('date_'))
async def process_date_selection(callback: CallbackQuery):
    selected_date = callback.data.split('_', 1)[1]
    
    # Сохраняем дату во временные данные
    user_data = TemporaryStorage.get_user_data(callback.from_user.id)
    user_data['date'] = selected_date
    TemporaryStorage.save_user_data(callback.from_user.id, user_data)
    
    await callback.message.edit_text(
        f"📋 Ваши данные:\n"
        f"👤 ФИО: {user_data['full_name']}\n"
        f"🏙 Город: {user_data['city']}\n"
        f"📚 Уровень: {user_data['level']}\n"
        f"📅 Дата: {selected_date}\n\n"
        f"Для завершения записи необходимо внести предоплату.",
        reply_markup=get_payment_confirmation_keyboard()
    )
    await callback.answer()
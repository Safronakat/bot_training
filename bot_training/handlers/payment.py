from aiogram import Router
from aiogram.types import CallbackQuery
import logging

from data.temporary_storage import TemporaryStorage
from services.google_sheets import GoogleSheetsManager
from services.group_manager import GroupManager
from config import ADMIN_IDS, GOOGLE_SHEETS_CREDENTIALS, SHEET_URL

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(lambda c: c.data == 'make_payment')
async def process_payment(callback: CallbackQuery):
    try:
        user_data = TemporaryStorage.get_user_data(callback.from_user.id)
        
        if not user_data:
            await callback.answer("❌ Данные не найдены. Начните регистрацию заново.", show_alert=True)
            return
        
        # Заглушка для оплаты
        user_data['payment_status'] = 'paid'
        
        # Сохраняем в Google Sheets
        sheets_manager = GoogleSheetsManager(GOOGLE_SHEETS_CREDENTIALS, SHEET_URL)
        
        if sheets_manager.save_user_data(user_data):
            # Получаем информацию о группе
            group_info = sheets_manager.get_group_info_for_date(
                user_data['level'], 
                user_data['date']
            )
            
            # Добавляем в группу
            group_manager = GroupManager(callback.bot, ADMIN_IDS)
            
            group_result = await group_manager.add_user_to_group(
                level=user_data['level'],
                date=user_data['date'],
                user_id=callback.from_user.id,
                user_data=user_data,
                group_link=group_info.get('group_link') if group_info.get('group_exists') else None
            )
            
            # Отправляем информацию о группе пользователю
            await group_manager.send_group_info_to_user(callback.from_user.id, group_result)
            
            if group_result["success"]:
                if group_result.get("status") == "link_provided":
                    success_message = (
                        "✅ Оплата прошла успешно!\n\n"
                        "Ссылка на группу отправлена вам в личные сообщения. "
                        "Присоединяйтесь к учебной группе!\n\n"
                        "Спасибо за регистрацию! 🎉"
                    )
                else:
                    success_message = (
                        "✅ Оплата прошла успешно!\n\n"
                        "Администратор создаст группу и добавит вас в ближайшее время. "
                        "С вами свяжутся для уточнения деталей.\n\n"
                        "Спасибо за регистрацию! 🎉"
                    )
            else:
                success_message = (
                    "✅ Оплата прошла успешно!\n\n"
                    "⚠️ Возникли небольшие технические сложности. "
                    "Администратор свяжется с вами в ближайшее время.\n\n"
                    "Спасибо за регистрацию! 🎉"
                )
            
            await callback.message.edit_text(success_message)
            
            # Очищаем временные данные
            TemporaryStorage.delete_user_data(callback.from_user.id)
            
        else:
            await callback.message.edit_text(
                "❌ Произошла ошибка при сохранении данных. "
                "Пожалуйста, свяжитесь с администратором."
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in payment process: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка. Пожалуйста, свяжитесь с администратором."
        )
        await callback.answer()
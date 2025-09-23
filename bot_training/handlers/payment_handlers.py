from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from datetime import datetime

from data.temporary_storage import TemporaryStorage
from services.google_sheets import GoogleSheetsManager
from services.group_manager import GroupManager
from config import ADMIN_IDS, GOOGLE_SHEETS_CREDENTIALS, SHEET_URL, PAYMENT_DETAILS, PRICES, calculate_prepayment
from keyboards.inline_kb import get_payment_confirmation_keyboard, get_receipt_confirmation_keyboard

router = Router()
logger = logging.getLogger(__name__)

class PaymentStates(StatesGroup):
    waiting_for_receipt = State()

@router.callback_query(lambda c: c.data == 'start_payment')
async def start_payment_process(callback: CallbackQuery, state: FSMContext):
    try:
        user_data = TemporaryStorage.get_user_data(callback.from_user.id)
        
        if not user_data:
            await callback.answer("❌ Данные не найдены. Начните регистрацию заново.", show_alert=True)
            return
        
        # Рассчитываем предоплату
        level_key = user_data.get('level_key')
        full_price = PRICES.get(level_key, 0)
        prepayment = calculate_prepayment(level_key)
        
        # Сохраняем цены в данные пользователя
        user_data['full_price'] = full_price
        user_data['prepayment'] = prepayment
        TemporaryStorage.save_user_data(callback.from_user.id, user_data)
        
        # Отправляем реквизиты для оплаты
        payment_text = (
            "💳 **Реквизиты для оплаты:**\n\n"
            f"📱 Номер телефона: `{PAYMENT_DETAILS['phone_number']}`\n"
            f"💳 Банковская карта: `{PAYMENT_DETAILS['bank_card']}`\n\n"
            f"💰 **Сумма к оплате (предоплата 50%): {prepayment} руб.**\n"
            f"💰 Полная стоимость курса: {full_price} руб.\n\n"
            f"💡 **Инструкция:**\n{PAYMENT_DETAILS['instructions']}\n\n"
            "После оплаты, пожалуйста, отправьте чек в этот чат."
        )
        
        await callback.message.edit_text(
            payment_text,
            reply_markup=get_receipt_confirmation_keyboard()
        )
        
        # Устанавливаем состояние ожидания чека
        await state.set_state(PaymentStates.waiting_for_receipt)
        await state.update_data(user_id=callback.from_user.id)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in payment start: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз.", show_alert=True)


@router.message(PaymentStates.waiting_for_receipt, F.content_type.in_([ContentType.PHOTO, ContentType.DOCUMENT]))
async def handle_receipt(message: Message, state: FSMContext):
    try:
        state_data = await state.get_data()
        user_id = state_data.get('user_id')
        
        if user_id != message.from_user.id:
            return
        
        user_data = TemporaryStorage.get_user_data(user_id)
        
        if not user_data:
            await message.answer("❌ Данные не найдены. Начните регистрацию заново.")
            await state.clear()
            return
        
        # Сохраняем информацию о чеке
        user_data['receipt_sent'] = True
        user_data['payment_status'] = 'pending_verification'
        TemporaryStorage.save_user_data(user_id, user_data)
        
        # Отправляем чек администраторам для проверки
        await send_receipt_to_admins(message, user_data)
        
        await message.answer(
            "✅ Чек получен! Администратор проверит оплату в ближайшее время.\n\n"
            "После проверки вы будете добавлены в учебную группу."
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error handling receipt: {e}")
        await message.answer("❌ Произошла ошибка при обработке чека.")

@router.message(PaymentStates.waiting_for_receipt)
async def handle_wrong_receipt_format(message: Message):
    await message.answer(
        "❌ Пожалуйста, отправьте скриншот чека в виде фото или документа.\n\n"
        "Если у вас возникли проблемы с оплатой, свяжитесь с администратором."
    )

def get_file_id(message: Message) -> str:
    """Извлекает file_id из сообщения"""
    if message.content_type == ContentType.PHOTO:
        return message.photo[-1].file_id
    elif message.content_type == ContentType.DOCUMENT:
        return message.document.file_id
    return ""

async def send_receipt_to_admins(message: Message, user_data: dict):
    """Отправляет чек администраторам для проверки"""
    
    # Сохраняем чек в ожидающие
    receipt_data = {
        'user_data': user_data,
        'message_id': message.message_id,
        'file_id': get_file_id(message),
        'content_type': message.content_type,
        'timestamp': datetime.now().isoformat()
    }
    TemporaryStorage.add_pending_receipt(user_data['user_id'], receipt_data)
    
    receipt_info = (
        "🧾 **НОВЫЙ ЧЕК ДЛЯ ПРОВЕРКИ**\n\n"
        f"👤 **ФИО:** {user_data['full_name']}\n"
        f"🏙 **Город:** {user_data['city']}\n"
        f"📚 **Уровень:** {user_data['level']}\n"
        f"📅 **Дата:** {user_data['date']}\n"
        f"🆔 **User ID:** {user_data['user_id']}\n"
        f"👤 **Username:** @{user_data.get('username', 'не указан')}\n"
        f"⏰ **Время отправки:** {datetime.now().strftime('%H:%M %d.%m.%Y')}\n\n"
        "👇 **Чек ниже** 👇"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            # Отправляем информацию о пользователе
            admin_message = await message.bot.send_message(admin_id, receipt_info)
            
            # Пересылаем сам чек (фото/документ)
            if message.content_type == ContentType.PHOTO:
                photo = message.photo[-1]
                await message.bot.send_photo(admin_id, photo.file_id)
            elif message.content_type == ContentType.DOCUMENT:
                await message.bot.send_document(admin_id, message.document.file_id)
                
            # Кнопки для администратора с явным указанием user_id
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="✅ Подтвердить оплату", 
                    callback_data=f"confirm_payment_{user_data['user_id']}"
                )],
                [InlineKeyboardButton(
                    text="❌ Отклонить", 
                    callback_data=f"reject_payment_{user_data['user_id']}"
                )],
                [InlineKeyboardButton(
                    text="📋 Все ожидающие чеки", 
                    callback_data="show_pending_receipts"
                )]
            ])
            
            await message.bot.send_message(
                admin_id, 
                f"💬 Действие для чека пользователя {user_data['full_name']}:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error sending receipt to admin {admin_id}: {e}")

# Добавляем хендлер для просмотра всех ожидающих чеков
@router.callback_query(lambda c: c.data == 'show_pending_receipts')
async def show_pending_receipts(callback: CallbackQuery):
    """Показывает все чеки, ожидающие проверки"""
    try:
        pending_receipts = TemporaryStorage.get_all_pending_receipts()
        
        if not pending_receipts:
            await callback.message.answer("📭 Нет чеков, ожидающих проверки.")
            await callback.answer()
            return
        
        response = "📋 **Чеки, ожидающие проверки:**\n\n"
        
        for user_id, receipt_data in pending_receipts.items():
            user_data = receipt_data.get('user_data', {})
            response += (
                f"👤 {user_data.get('full_name', 'Неизвестно')} "
                f"(ID: {user_id})\n"
                f"📚 {user_data.get('level', 'Неизвестно')} • "
                f"📅 {user_data.get('date', 'Неизвестно')}\n"
                f"⏰ {receipt_data.get('timestamp', 'Неизвестно')}\n"
            )
            
            # Кнопки для быстрого действия
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"🔍 Проверить {user_data.get('full_name', 'Unknown')}",
                    callback_data=f"review_receipt_{user_id}"
                )]
            ])
            
            await callback.message.answer(response, reply_markup=keyboard)
            response = ""  # Сбрасываем для следующего сообщения
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing pending receipts: {e}")
        await callback.answer("❌ Ошибка при загрузке списка чеков")

# Хендлер для быстрого перехода к проверке чека
@router.callback_query(lambda c: c.data.startswith('review_receipt_'))
async def review_receipt(callback: CallbackQuery):
    """Быстрый переход к проверке конкретного чека"""
    try:
        user_id = int(callback.data.split('_')[-1])
        receipt_data = TemporaryStorage.get_pending_receipt(user_id)
        
        if not receipt_data:
            await callback.answer("❌ Чек не найден или уже обработан")
            return
        
        user_data = receipt_data.get('user_data', {})
        
        # Повторно отправляем информацию о чеке
        receipt_info = (
            "🔍 **ПРОВЕРКА ЧЕКА**\n\n"
            f"👤 **ФИО:** {user_data['full_name']}\n"
            f"🏙 **Город:** {user_data['city']}\n"
            f"📚 **Уровень:** {user_data['level']}\n"
            f"📅 **Дата:** {user_data['date']}\n"
            f"⏰ **Время отправки:** {receipt_data.get('timestamp', 'Неизвестно')}\n\n"
            "Выберите действие:"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Подтвердить оплату", 
                callback_data=f"confirm_payment_{user_id}"
            )],
            [InlineKeyboardButton(
                text="❌ Отклонить", 
                callback_data=f"reject_payment_{user_id}"
            )],
            [InlineKeyboardButton(
                text="📋 Все чеки", 
                callback_data="show_pending_receipts"
            )]
        ])
        
        await callback.message.answer(receipt_info, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error reviewing receipt: {e}")
        await callback.answer("❌ Ошибка при загрузке чека")

@router.callback_query(lambda c: c.data.startswith('confirm_payment_'))
async def confirm_payment(callback: CallbackQuery):
    """Администратор подтверждает оплату"""
    try:
        user_id = int(callback.data.split('_')[-1])
        receipt_data = TemporaryStorage.get_pending_receipt(user_id)
        
        if not receipt_data:
            await callback.answer("❌ Чек не найден или уже обработан")
            return
        
        user_data = receipt_data.get('user_data', {})
        
        if not user_data:
            await callback.answer("❌ Данные пользователя не найдены")
            return
        
        # Обновляем статус оплаты
        user_data['payment_status'] = 'confirmed'
        user_data['verified_by'] = callback.from_user.id
        user_data['verified_at'] = datetime.now().isoformat()
        
        TemporaryStorage.save_user_data(user_id, user_data)
        TemporaryStorage.remove_pending_receipt(user_id)  # Удаляем из ожидающих
        
        # Сохраняем в Google Sheets
        sheets_manager = GoogleSheetsManager(GOOGLE_SHEETS_CREDENTIALS, SHEET_URL)
        sheets_manager.save_user_data(user_data)
        
        # Добавляем в группу
        group_manager = GroupManager(callback.bot, ADMIN_IDS)
        group_info = sheets_manager.get_group_info_for_date(user_data['level'], user_data['date'])
        
        group_result = await group_manager.add_user_to_group(
            level=user_data['level'],
            date=user_data['date'],
            user_id=user_id,
            user_data=user_data,
            group_link=group_info.get('group_link') if group_info.get('group_exists') else None
        )
        
        # Уведомляем пользователя
        await callback.bot.send_message(
            user_id,
            "✅ Ваша оплата подтверждена администратором! Вы были добавлены в учебную группу.\n\n"
            "Спасибо за регистрацию! 🎉"
        )
        
        # Уведомляем администратора об успешном завершении
        await callback.message.edit_text(
            f"✅ Оплата подтверждена для пользователя {user_data['full_name']}\n"
            f"👤 Пользователь уведомлен, данные сохранены."
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error confirming payment: {e}")
        await callback.answer("❌ Ошибка при подтверждении оплаты")

@router.callback_query(lambda c: c.data.startswith('reject_payment_'))
async def reject_payment(callback: CallbackQuery):
    """Администратор отклоняет оплату"""
    try:
        user_id = int(callback.data.split('_')[-1])
        receipt_data = TemporaryStorage.get_pending_receipt(user_id)
        
        if not receipt_data:
            await callback.answer("❌ Чек не найден или уже обработан")
            return
        
        user_data = receipt_data.get('user_data', {})
        TemporaryStorage.remove_pending_receipt(user_id)  # Удаляем из ожидающих
        
        # Уведомляем пользователя
        await callback.bot.send_message(
            user_id,
            "❌ Ваш чек не прошел проверку администратором. "
            "Пожалуйста, свяжитесь с администратором для уточнения деталей или отправьте корректный чек."
        )
        
        await callback.message.edit_text(
            f"❌ Оплата отклонена для пользователя {user_data['full_name']}\n"
            f"👤 Пользователь уведомлен об отклонении."
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error rejecting payment: {e}")
        await callback.answer("❌ Ошибка при отклонении оплаты")
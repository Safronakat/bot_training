from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from data.temporary_storage import TemporaryStorage
from keyboards.inline_kb import get_levels_keyboard

router = Router()

class Registration(StatesGroup):
    waiting_for_info = State()


@router.message(Registration.waiting_for_info)
async def process_user_info(message: Message, state: FSMContext):
    user_input = message.text.strip()
    print(f"Received input: {user_input}") 
    
   
    try:
        # Разделяем по первой запятой
        if ',' in user_input:
            full_name, city = user_input.split(',', 1)
        else:
            await message.answer("❌ Пожалуйста, используйте запятую между ФИО и городом. Например: Ivan Ivanov, Moscow")
            return
        
        full_name = full_name.strip()
        city = city.strip()
        
        if not full_name or not city:
            await message.answer("❌ И ФИО и город должны быть заполнены. Например: Ivan Ivanov, Moscow")
            return
        
        # Сохраняем во временное хранилище
        user_data = {
            'user_id': message.from_user.id,
            'full_name': full_name,
            'city': city,
            'username': message.from_user.username
        }
        
        print(f"Saving user data: {user_data}")  # Логирование данных перед сохранением
        TemporaryStorage.save_user_data(message.from_user.id, user_data)
        
        # Проверка сохраненных данных
        saved_data = TemporaryStorage.get_user_data(message.from_user.id)
        print(f"Retrieved data: {saved_data}")  # Логирование данных после сохранения
        
        if saved_data != user_data:
            print("Data mismatch: saved data does not match input data.")
            await message.answer("❌ Произошла ошибка при сохранении данных.")
            return
        
        await state.clear()
        
        await message.answer(
            f"✅ Данные сохранены!\n"
            f"👤 ФИО: {full_name}\n"
            f"🏙 Город: {city}\n\n"
            "Теперь выберите уровень обучения:",
            reply_markup=get_levels_keyboard()
        )
        
    except Exception as e:
        print(f"Error: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте еще раз. Формат: ФИО, Город")
        return  # Возврат, чтобы пользователь мог попробовать снова

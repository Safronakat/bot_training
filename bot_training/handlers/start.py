from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from handlers.registration import Registration
from aiogram.fsm.context import FSMContext
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):  # Добавлен параметр state
    await state.set_state(Registration.waiting_for_info)  # Устанавливаем состояние
    await message.answer(
        "👋 Добро пожаловать в систему записи на обучение!\n\n"
        "Пожалуйста, напишите ваше ФИО на английском языке и город, откуда вы."
    )


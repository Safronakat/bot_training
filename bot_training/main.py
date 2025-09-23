import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_IDS, GOOGLE_SHEETS_CREDENTIALS, SHEET_URL
from handlers.start import router as start_router
from handlers.registration import router as registration_router
from handlers.level_selection import router as level_selection_router
from handlers.date_selection import router as date_selection_router
from handlers.payment import router as payment_router
from handlers.payment_handlers import router as payment_handlers_router

class BotConfig:
    def __init__(self):
        self.ADMIN_IDS = ADMIN_IDS
        self.GOOGLE_SHEETS_CREDENTIALS = GOOGLE_SHEETS_CREDENTIALS
        self.SHEET_URL = SHEET_URL

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Создаем объект конфига и привязываем к боту
    config = BotConfig()
    bot.config = config  # Правильное присваивание
    
    # Регистрируем ВСЕ роутеры
    dp.include_router(start_router)
    dp.include_router(registration_router)
    dp.include_router(level_selection_router)
    dp.include_router(date_selection_router)
    #dp.include_router(payment_router)
    dp.include_router(payment_handlers_router)
    
    print("Бот запущен...")
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
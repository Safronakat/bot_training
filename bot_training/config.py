import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(',')))
GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
SHEET_URL = os.getenv('SHEET_URL')

# Уровни обучения
LEVELS = {
    'basic': 'Basic',
    'progressive': 'Progressive', 
    'functional': 'Functional',
    'drum': 'Drum',
    '3d': '3D',
    'kids': 'Kids',
    'power_seminar': 'Strong',
    'stretch_seminar': 'Stretch'
}

# Цены для каждого уровня (полная стоимость)
PRICES = {
    'basic': 10000,  # Пример: 10,000 руб
    'progressive': 12000,
    'functional': 15000,
    'drum': 18000,
    '3d': 20000,
    'kids': 8000,
    'power_seminar': 5000,
    'stretch_seminar': 5000
}

# Предоплата (50% от полной стоимости)
def calculate_prepayment(level_key: str) -> int:
    full_price = PRICES.get(level_key, 0)
    return full_price // 2  # 50%

# config.py - добавляем в конец
PAYMENT_DETAILS = {
    'phone_number': '+79991234567',
    'bank_card': '0000 0000 0000 0000',
    'instructions': 'Оплата на номер телефона или банковскую карту'
}
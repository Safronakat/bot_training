import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Настройка логирования
logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    def __init__(self, credentials_json: str, sheet_url: str):
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            json.loads(credentials_json), scope
        )
        self.client = gspread.authorize(credentials)
        self.sheet = self.client.open_by_url(sheet_url)
    
    def get_dates_for_level(self, level: str) -> list:
        try:
            worksheet = self.sheet.worksheet('Даты')
            
            # Получаем все данные без автоматического парсинга заголовков
            all_data = worksheet.get_all_values()
            
            # Если нет данных или только заголовки
            if len(all_data) <= 1:
                logger.info("No data found in worksheet")
                return []
            
            # Извлекаем заголовки из первой строки
            headers = [header.strip().lower() for header in all_data[0]]
            logger.info(f"Headers found: {headers}")
            
            dates = []
            
            # Обрабатываем данные начиная со второй строки
            for row in all_data[1:]:
                if len(row) < 3:  # Проверяем, что в строке достаточно данных
                    continue
                
                # Создаем словарь из заголовков и значений
                record = dict(zip(headers, row))
                logger.info(f"Processing record: {record}")
                
                # Проверяем условия с нормализацией данных
                record_level = record.get('уровень', '').strip()
                actual_status = record.get('актуальная', '').strip().lower()
                date_value = record.get('дата', '').strip()
                
                logger.info(f"Level: '{record_level}', Actual: '{actual_status}', Date: '{date_value}'")
                
                # Сравниваем с учетом возможных вариантов написания
                if (record_level.lower() == level.lower() and 
                    actual_status in ['да', 'yes', 'true', '1', '+'] and
                    date_value):
                    dates.append(date_value)
                    logger.info(f"✓ Added date: {date_value}")
            
            logger.info(f"Found dates for level '{level}': {dates}")
            return dates
            
        except Exception as e:
            logger.error(f"Error getting dates for level '{level}': {e}")
            return []
    
    def get_group_info_for_date(self, level: str, date: str) -> dict:
        """Получает информацию о группе для конкретного уровня и даты"""
        try:
            worksheet = self.sheet.worksheet('Даты')
            all_data = worksheet.get_all_values()
            
            if len(all_data) <= 1:
                return {"group_exists": False, "group_link": None}
            
            # Нормализуем заголовки
            headers = [header.strip().lower() for header in all_data[0]]
            
            # Ищем индексы колонок
            level_col = None
            date_col = None
            actual_col = None
            link_col = None
            
            for i, header in enumerate(headers):
                if 'уровень' in header:
                    level_col = i
                elif 'дата' in header:
                    date_col = i
                elif 'актуальная' in header:
                    actual_col = i
                elif 'ссылка' in header:
                    link_col = i
            
            if level_col is None or date_col is None or actual_col is None:
                return {"group_exists": False, "group_link": None}
            
            # Ищем подходящую запись
            for row in all_data[1:]:
                if len(row) <= max(level_col, date_col, actual_col):
                    continue
                
                record_level = row[level_col].strip()
                record_date = row[date_col].strip()
                actual_status = row[actual_col].strip().lower()
                
                if (record_level.lower() == level.lower() and 
                    record_date == date and
                    actual_status in ['да', 'yes', 'true', '1', '+']):
                    
                    group_link = row[link_col].strip() if link_col is not None and len(row) > link_col else None
                    
                    return {
                        "group_exists": True,
                        "group_link": group_link if group_link else None,
                        "has_link": bool(group_link)
                    }
            
            return {"group_exists": False, "group_link": None}
            
        except Exception as e:
            logger.error(f"Error getting group info: {e}")
            return {"group_exists": False, "group_link": None}
    
    def debug_worksheet_structure(self):
        """Функция для отладки структуры worksheet"""
        try:
            worksheet = self.sheet.worksheet('Даты')
            all_data = worksheet.get_all_values()
            
            logger.info("=== WORKSHEET STRUCTURE DEBUG ===")
            logger.info(f"Total rows: {len(all_data)}")
            
            for i, row in enumerate(all_data):
                logger.info(f"Row {i+1}: {row}")
            
            return all_data
        except Exception as e:
            logger.error(f"Debug error: {e}")
            return []
    
    def get_dates_alternative_method(self, level: str) -> list:
        """Альтернативный метод получения дат"""
        try:
            worksheet = self.sheet.worksheet('Даты')
            
            # Находим колонки по заголовкам
            all_data = worksheet.get_all_values()
            if not all_data:
                return []
            
            headers = [header.strip().lower() for header in all_data[0]]
            
            # Ищем индексы колонок
            level_col = None
            date_col = None
            actual_col = None
            
            for i, header in enumerate(headers):
                if 'уровень' in header:
                    level_col = i
                elif 'дата' in header:
                    date_col = i
                elif 'актуальная' in header:
                    actual_col = i
            
            logger.info(f"Column indexes - Level: {level_col}, Date: {date_col}, Actual: {actual_col}")
            
            if level_col is None or date_col is None or actual_col is None:
                logger.error("Required columns not found")
                return []
            
            dates = []
            
            # Обрабатываем данные
            for i, row in enumerate(all_data[1:], start=2):
                if len(row) <= max(level_col, date_col, actual_col):
                    continue
                
                record_level = row[level_col].strip()
                actual_status = row[actual_col].strip().lower()
                date_value = row[date_col].strip()
                
                if (record_level.lower() == level.lower() and 
                    actual_status in ['да', 'yes', 'true', '1', '+'] and
                    date_value):
                    dates.append(date_value)
            
            return dates
            
        except Exception as e:
            logger.error(f"Alternative method error: {e}")
            return []
    
    def save_user_data(self, user_data: dict) -> bool:
        """Сохранение данных пользователя в Google Sheets."""
        required_keys = ['user_id', 'full_name', 'city', 'level', 'date', 'payment_status']
        
        # Проверка наличия всех необходимых данных
        if not all(key in user_data for key in required_keys):
            logging.error("Недостающие данные в user_data")
            return False
        
        try:
            worksheet = self.sheet.worksheet('Ученики')
            worksheet.append_row([
                user_data['user_id'],
                user_data['full_name'],
                user_data['city'],
                user_data['level'],
                user_data['date'],
                user_data['payment_status'],
                user_data.get('full_price', ''),
                user_data.get('prepayment', ''),
                user_data.get('verified_by', ''),
                user_data.get('verified_at', '')
            ])
            logging.info("Данные пользователя успешно сохранены.")
            return True
        except Exception as e:
            logging.error(f"Ошибка при сохранении данных: {e}")
            return False

# Функция для тестирования
def test_sheet_connection():
    """Тестирование подключения и структуры таблицы"""
    try:
        from config import GOOGLE_SHEETS_CREDENTIALS, SHEET_URL
        sheets_manager = GoogleSheetsManager(GOOGLE_SHEETS_CREDENTIALS, SHEET_URL)
        
        # Тестируем структуру
        structure = sheets_manager.debug_worksheet_structure()
        
        # Тестируем оба метода
        dates1 = sheets_manager.get_dates_for_level('Functional')
        dates2 = sheets_manager.get_dates_alternative_method('Functional')
        
        logger.info(f"Method 1 results: {dates1}")
        logger.info(f"Method 2 results: {dates2}")
        
        return dates1 or dates2
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        return []

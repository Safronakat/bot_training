from datetime import datetime
from typing import Dict, Any, List

# Временное хранилище данных пользователей
user_data = {}
# Хранилище ожидающих проверки чеков
pending_receipts = {}

class TemporaryStorage:
    @staticmethod
    def save_user_data(user_id: int, data: Dict[str, Any]):
        user_data[user_id] = data
    
    @staticmethod
    def get_user_data(user_id: int) -> Dict[str, Any]:
        return user_data.get(user_id, {})
    
    @staticmethod
    def delete_user_data(user_id: int):
        if user_id in user_data:
            del user_data[user_id]
    
    # Методы для управления чеками
    @staticmethod
    def add_pending_receipt(user_id: int, receipt_data: Dict[str, Any]):
        pending_receipts[user_id] = {
            **receipt_data,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def get_pending_receipt(user_id: int) -> Dict[str, Any]:
        return pending_receipts.get(user_id, {})
    
    @staticmethod
    def remove_pending_receipt(user_id: int):
        if user_id in pending_receipts:
            del pending_receipts[user_id]
    
    @staticmethod
    def get_all_pending_receipts() -> Dict[int, Dict[str, Any]]:
        return pending_receipts.copy()
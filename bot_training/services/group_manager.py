from aiogram import Bot
import logging

logger = logging.getLogger(__name__)

class GroupManager:
    def __init__(self, bot: Bot, admin_ids: list):
        self.bot = bot
        self.admin_ids = admin_ids
        self.existing_groups = {}  # Кэш созданных групп: {("level", "date"): chat_id}
    
    async def get_or_create_group(self, level: str, date: str) -> dict:
        """Находит существующую группу или возвращает информацию для администратора"""
        group_key = (level, date)
        
        # Проверяем кэш
        if group_key in self.existing_groups:
            return {"chat_id": self.existing_groups[group_key], "is_new": False}
        
        # Боты не могут создавать группы, поэтому возвращаем инструкцию для администратора
        return await self.get_group_creation_instructions(level, date)
    
    async def get_group_creation_instructions(self, level: str, date: str) -> dict:
        """Возвращает инструкции для создания группы администратором"""
        group_title = f"{level} - {date}"
        
        instructions = (
            f"Администратору необходимо:\n"
            f"1. Создать группу с названием: '{group_title}'\n"
            f"2. Добавить бота в группу как администратора\n"
            f"3. Отправить команду /set_group_id в группе\n"
            f"4. Или предоставить ID группы для добавления учеников"
        )
        
        # Отправляем инструкции всем администраторам
        for admin_id in self.admin_ids:
            try:
                await self.bot.send_message(admin_id, instructions)
            except Exception as e:
                logger.error(f"Error sending instructions to admin {admin_id}: {e}")
        
        return {
            "needs_admin_action": True,
            "group_title": group_title,
            "instructions": "Ожидание создания группы администратором"
        }
    
    async def add_user_to_group(self, level: str, date: str, user_id: int, user_data: dict, group_link: str = None) -> dict:
        """Добавляет пользователя в группу через ссылку или ставит в очередь"""
        try:
            if group_link:
                # Если есть ссылка на группу, отправляем ее пользователю
                message_text = (
                    f"✅ Регистрация завершена!\n\n"
                    f"🎉 Вы успешно записаны на курс:\n"
                    f"📚 Уровень: {level}\n"
                    f"📅 Дата: {date}\n\n"
                    f"Присоединяйтесь к учебной группе по ссылке:\n{group_link}\n\n"
                    f"С вами свяжутся администраторы для уточнения деталей."
                )
                
                try:
                    await self.bot.send_message(user_id, message_text)
                    
                    # Уведомляем администраторов
                    await self.notify_admins_about_new_user(level, date, user_data, has_link=True)
                    
                    return {
                        "success": True, 
                        "status": "link_provided",
                        "message": "Пользователю отправлена ссылка на группу"
                    }
                except Exception as e:
                    logger.error(f"Error sending group link to user: {e}")
                    return {"success": False, "error": f"Не удалось отправить ссылку: {e}"}
            
            else:
                # Если ссылки нет, уведомляем администраторов
                message_text = (
                    f"✅ Ваша регистрация принята!\n\n"
                    f"📚 Уровень: {level}\n"
                    f"📅 Дата: {date}\n\n"
                    f"Группа будет создана в ближайшее время. "
                    f"Администратор свяжется с вами для добавления в учебную группу."
                )
                
                await self.bot.send_message(user_id, message_text)
                
                # Уведомляем администраторов о необходимости создать группу
                await self.notify_admins_about_new_user(level, date, user_data, has_link=False)
                
                return {
                    "success": True, 
                    "status": "pending_admin_action",
                    "message": "Ожидание создания группы администратором"
                }
                
        except Exception as e:
            logger.error(f"Error in add_user_to_group: {e}")
            return {"success": False, "error": str(e)}
    
    async def notify_admins_about_new_user(self, level: str, date: str, user_data: dict, has_link: bool = False):
        """Уведомляет администраторов о новом участнике"""
        if has_link:
            message_text = (
                f"✅ Новый участник присоединился по ссылке:\n"
                f"👤 ФИО: {user_data['full_name']}\n"
                f"🏙 Город: {user_data['city']}\n"
                f"📚 Уровень: {level}\n"
                f"📅 Дата: {date}\n"
                f"🔗 Группа: по ссылке"
            )
        else:
            message_text = (
                f"📋 Новый участник ожидает создания группы:\n"
                f"👤 ФИО: {user_data['full_name']}\n"
                f"🏙 Город: {user_data['city']}\n"
                f"📚 Уровень: {level}\n"
                f"📅 Дата: {date}\n\n"
                f"❌ Ссылка на группу отсутствует!\n"
                f"Необходимо создать группу и добавить участника."
            )
        
        for admin_id in self.admin_ids:
            try:
                await self.bot.send_message(admin_id, message_text)
            except Exception as e:
                logger.error(f"Error notifying admin {admin_id}: {e}")
    
    async def set_group_id(self, level: str, date: str, chat_id: int):
        """Устанавливает ID существующей группы (вызывается администратором)"""
        group_key = (level, date)
        self.existing_groups[group_key] = chat_id
        logger.info(f"Group ID set for {level} - {date}: {chat_id}")
    
    async def send_group_info_to_user(self, user_id: int, group_info: dict):
        """Отправляет пользователю информацию о группе"""
        try:
            if group_info["success"]:
                if group_info.get("status") == "link_provided":
                    # Пользователь получил ссылку
                    message_text = (
                        f"✅ Регистрация завершена!\n\n"
                        f"Ссылка на группу отправлена вам в личные сообщения.\n"
                        f"Присоединяйтесь к учебной группе!"
                    )
                elif group_info.get("status") == "pending_admin_action":
                    # Группа еще не создана
                    message_text = (
                        f"✅ Регистрация завершена!\n\n"
                        f"Администратор создаст группу и добавит вас в ближайшее время.\n"
                        f"С вами свяжутся для уточнения деталей."
                    )
                else:
                    # Пользователь добавлен в группу (старая логика)
                    message_text = (
                        f"✅ Вы успешно добавлены в группу обучения!\n\n"
                        f"С вами свяжутся администраторы для уточнения деталей.\n"
                        f"Спасибо за регистрацию! 🎉"
                    )
                
                await self.bot.send_message(user_id, message_text)
            else:
                await self.bot.send_message(
                    user_id, 
                    "❌ Произошла ошибка при добавлении в группу. Администратор свяжется с вами."
                )
                
        except Exception as e:
            logger.error(f"Error sending group info to user: {e}")
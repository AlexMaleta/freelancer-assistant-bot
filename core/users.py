from typing import Optional
from models.users import UserCreate, UserInDB
from database import users as user_db


class UserService:
    def create_user(self, user_data: UserCreate) -> int:
        return user_db.create_user(user_data)

    def get_user_by_id(self, user_id: int) -> Optional[UserInDB]:
        return user_db.get_user_by_id(user_id)

    def update_language(self, user_id: int, new_language: str) -> bool:
        return user_db.update_user_language(user_id, new_language)

    def update_user_name(self, user_id: int, neme: str) -> bool:
        return user_db.update_user_name(user_id, neme)

    def update_email(self, user_id: int, email: str) -> bool:
        return user_db.update_user_email(user_id, email)

    def delete_user(self, user_id: int) -> bool:
        return user_db.delete_user(user_id)

    def update_notifications(self, user_id: int, notify_email: Optional[bool] = None, notify_telegram: Optional[bool] = None) -> bool:
        """
            Update user's notification preferences (email and/or Telegram).
            Parameters:
                user_id (int): Target user ID.
                notify_email (bool, optional): Whether email notifications are enabled.
                notify_telegram (bool, optional): Whether Telegram notifications are enabled.

            Returns:
                bool: True if update was successful, False otherwise.
        """
        return user_db.update_notification_settings(
            user_id,
            notify_email=notify_email,
            notify_telegram=notify_telegram
        )

from typing import Optional

from database.database import get_connection
from models.users import UserCreate, UserInDB


def create_user(user: UserCreate) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, language, telegram_id, email)
            VALUES (?, ?, ?, ?)
        """, (user.name, user.language, user.telegram_id, user.email))
        return cursor.lastrowid


def get_user_by_id(user_id: int) -> Optional[UserInDB]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, language, telegram_id, email, notify_email, notify_telegram
            FROM users
            WHERE id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            return UserInDB(
                id=row[0],
                name=row[1],
                language=row[2],
                telegram_id=row[3],
                email=row[4],
                notify_email=bool(row[5]),
                notify_telegram=bool(row[6])
            )
        return None


def get_user_by_telegram_id(telegram_id: int) -> Optional[UserInDB]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, language, telegram_id, email, notify_email, notify_telegram
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,))
        row = cursor.fetchone()
        if row:
            return UserInDB(
                id=row[0],
                name=row[1],
                language=row[2],
                telegram_id=row[3],
                email=row[4],
                notify_email=bool(row[5]),
                notify_telegram=bool(row[6])
            )
        return None


def update_user_language(user_id: int, new_language: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET language = ?
            WHERE id = ?
        """, (new_language, user_id))
        return cursor.rowcount > 0


def delete_user(user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM users
            WHERE id = ?
        """, (user_id,))
        return cursor.rowcount > 0


def update_user_email(user_id: int, email: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
    conn.commit()
    conn.close()


def update_notification_settings(user_id: int, notify_email: Optional[bool] = None, notify_telegram: Optional[bool] = None) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()

        fields = []
        values = []

        if notify_email is not None:
            fields.append("notify_email = ?")
            values.append(int(notify_email))

        if notify_telegram is not None:
            fields.append("notify_telegram = ?")
            values.append(int(notify_telegram))

        if not fields:
            return False

        query = f"""
        UPDATE users SET {", ".join(fields)}
        WHERE id = ?
        """
        values.append(user_id)

        cursor.execute(query, values)
        conn.commit()

        return cursor.rowcount > 0


def update_user_name(user_id: int, name: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
        conn.commit()
        return cursor.rowcount > 0

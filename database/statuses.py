from database.database import get_connection
from typing import Optional


def get_status_name(status_id: int, language: str = "ru") -> Optional[str]:
    with get_connection() as conn:
        cursor = conn.cursor()

        # First, search for translation
        cursor.execute("""
            SELECT translation
            FROM status_translations
            WHERE status_id = ? AND language = ?
        """, (status_id, language))
        row = cursor.fetchone()

        if row:
            return row[0]

        # If there is no translation, return the default_name.
        cursor.execute("""
            SELECT default_name
            FROM statuses
            WHERE id = ?
        """, (status_id,))
        row = cursor.fetchone()

        return row[0] if row else None


def get_all_statuses(lang: str) -> list[tuple[int, str]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, t.translation
        FROM statuses s
        JOIN status_translations t ON s.id = t.status_id
        WHERE t.language = ? and s.id > 1
        ORDER BY s.id
    """, (lang,))

    result = cursor.fetchall()
    conn.close()
    return result

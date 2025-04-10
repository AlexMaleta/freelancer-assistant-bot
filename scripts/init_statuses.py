import sqlite3

from database.database import get_connection

STATUSES = [
    {"code": "new", "default_name": "New", "translations": {"ru": "Новый", "en": "New"}},
    {"code": "in_progress", "default_name": "In progress", "translations": {"ru": "В работе", "en": "In progress"}},
    {"code": "done", "default_name": "Done", "translations": {"ru": "Завершён", "en": "Done"}},
    {"code": "rejected", "default_name": "Rejected", "translations": {"ru": "Отклонён", "en": "Rejected"}},
    {"code": "frozen", "default_name": "Frozen", "translations": {"ru": "Заморожен", "en": "Frozen"}},
]


def init_statuses():
    with get_connection() as conn:
        cursor = conn.cursor()

    for status in STATUSES:
        # Check: does such status already exist?
        cursor.execute("SELECT id FROM statuses WHERE code = ?", (status["code"],))
        result = cursor.fetchone()
        if result:
            print(f"Status {status['code']} already exists, skipping.")
            continue

        # Insert into statuses
        cursor.execute(
            "INSERT INTO statuses (code, default_name) VALUES (?, ?)",
            (status["code"], status["default_name"])
        )
        status_id = cursor.lastrowid

        # Insert translations
        for lang, translation in status["translations"].items():
            cursor.execute(
                "INSERT INTO status_translations (status_id, language, translation) VALUES (?, ?, ?)",
                (status_id, lang, translation)
            )

        print(f"✅ Added status: {status['code']}")

    conn.commit()
    conn.close()
    print("Initialization complete.")


if __name__ == "__main__":
    init_statuses()

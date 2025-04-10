from database.database import get_connection


def init_db():
    with get_connection() as conn:
        c = conn.cursor()

    # users
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        language TEXT DEFAULT 'ru',
        telegram_id TEXT,
        email TEXT,
        notify_email INTEGER DEFAULT 0,
        notify_telegram INTEGER DEFAULT 1
    )
    """)

    # customers
    c.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME,
        phone TEXT,
        email TEXT,
        notes TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # statuses
    c.execute("""
    CREATE TABLE IF NOT EXISTS statuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        default_name TEXT NOT NULL
    )
    """)

    # status_translations
    c.execute("""
    CREATE TABLE IF NOT EXISTS status_translations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status_id INTEGER NOT NULL,
        language TEXT NOT NULL,
        translation TEXT NOT NULL,
        FOREIGN KEY(status_id) REFERENCES statuses(id)
    )
    """)

    # orders
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        status_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME,
        deadline DATETIME,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(customer_id) REFERENCES customers(id),
        FOREIGN KEY(status_id) REFERENCES statuses(id)
    )
    """)

    # order_stages
    c.execute("""
    CREATE TABLE IF NOT EXISTS order_stages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        status_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME,
        deadline DATETIME,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(status_id) REFERENCES statuses(id)
    )
    """)

    # checklist_items
    c.execute("""
    CREATE TABLE IF NOT EXISTS checklist_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stage_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        status_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME,
        FOREIGN KEY(stage_id) REFERENCES order_stages(id),
        FOREIGN KEY(status_id) REFERENCES statuses(id)
    )
    """)

    # notifications_sent
    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications_sent (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        notification_type TEXT NOT NULL,
        sent_at TEXT NOT NULL,
        channel TEXT DEFAULT 'telegram',
        message TEXT)
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database and tables created.")

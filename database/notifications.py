from datetime import datetime
from typing import Optional

from database.database import get_connection
from models.notifications import NotificationBase, NotificationCreate


def mark_notified(notification: NotificationCreate) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notifications_sent
            (user_id, entity_type, entity_id, notification_type, sent_at, channel, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (notification.user_id,
              notification.entity_type,
              notification.entity_id,
              notification.notification_type,
              datetime.now().isoformat(),
              notification.channel,
              notification.message
              ))
        conn.commit()



def was_notified(notification: NotificationBase
                 ) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM notifications_sent
            WHERE user_id = ? AND entity_type = ? AND entity_id = ? AND notification_type = ? AND channel = ?
            LIMIT 1
        """, (notification.user_id,
              notification.entity_type,
              notification.entity_id,
              notification.notification_type,
              notification.channel)
             )
        return cursor.fetchone() is not None
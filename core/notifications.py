from database import notifications as notif_db
from models.notifications import NotificationBase, NotificationCreate


class NotificationService:
    def was_notified(self, data: NotificationBase) -> bool:
        """
        Check if a notification of the same type for the same entity
        has already been sent to the user.
        Prevents duplicate notifications.
        """
        return notif_db.was_notified(data)

    def mark_notified(self, data: NotificationCreate) -> None:
        """
        Store the fact that a notification has been sent to the user.
        Helps avoid sending the same notification again.
        """
        notif_db.mark_notified(data)



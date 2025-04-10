from datetime import datetime, timedelta

from core.notifications import NotificationService
from core.order_stages import OrderStageService
from core.orders import OrderService
from core.users import UserService
from models.notifications import NotificationCreate
from utils.notification_utils import send_deadline_notification
from utils.translations import I18n

user_service = UserService()
order_service = OrderService()
order_stages_service = OrderStageService()
notification_service = NotificationService()

async def check_upcoming_deadlines():
    """
    Scheduled task to notify users about upcoming order and stage deadlines (1 day in advance).

    - Checks orders and stages with a deadline set to tomorrow.
    - Sends notifications via Telegram and/or Email depending on user preferences.
    - Prevents duplicate notifications using NotificationService.

    This function is designed to be run by a background scheduler (e.g. apscheduler).
    """
    print(f"[{datetime.now().isoformat()}]🔔 Start checking deadlines")

    tomorrow = (datetime.now() + timedelta(days=1))

    # Checking orders
    orders = order_service.get_orders_with_deadline(tomorrow)
    for order in orders:
        user = user_service.get_user_by_id(order.user_id)
        message = I18n.t(user.language, "mess_deadline_order").format(order_name=order.name)
        # TELEGRAM
        if user.notify_telegram:
            notif = NotificationCreate(
                user_id=user.id,
                entity_type="order",
                entity_id=order.id,
                notification_type="deadline",
                sent_at=datetime.now(),
                channel="telegram",
                message=message
            )
            if not notification_service.was_notified(notif):
                await send_deadline_notification(user=user,
                                                 message=message,
                                                 type="telegram",
                                                 subject=I18n.t(user.language, "deadline_reminder"))
                notification_service.mark_notified(notif)

        # EMAIL
        if user.notify_email:
            notif = NotificationCreate(
                user_id=user.id,
                entity_type="order",
                entity_id=order.id,
                notification_type="deadline",
                sent_at=datetime.now(),
                channel="email",
                message=message
            )
            if not notification_service.was_notified(notif):
                await send_deadline_notification(user=user,
                                                 message=message,
                                                 type="email",
                                                 subject=I18n.t(user.language, "deadline_reminder"))
                notification_service.mark_notified(notif)

    # Checking stages
    stages = order_stages_service.get_stages_with_deadline(tomorrow)
    for stage in stages:
        order = order_service.get_by_id(stage.order_id)
        user = user_service.get_user_by_id(order.user_id)
        message = I18n.t(user.language, "mess_deadline_stage").format(stage_name=stage.name, order_name=order.name)
        # TELEGRAM
        if user.notify_telegram:
            notif = NotificationCreate(
                user_id=user.id,
                entity_type="stage",
                entity_id=stage.id,
                notification_type="deadline",
                sent_at=datetime.now(),
                channel="telegram",
                message=message
            )
            if not notification_service.was_notified(notif):
                await send_deadline_notification(user=user,
                                                 message=message,
                                                 type="telegram",
                                                 subject=I18n.t(user.language, "deadline_reminder"))
                notification_service.mark_notified(notif)

        # EMAIL
        if user.notify_email:
            notif = NotificationCreate(
                user_id=user.id,
                entity_type="stage",
                entity_id=stage.id,
                notification_type="deadline",
                sent_at=datetime.now(),
                channel="email",
                message=message
            )
            if not notification_service.was_notified(notif):
                await send_deadline_notification(user=user,
                                                 message=message,
                                                 type="email",
                                                 subject=I18n.t(user.language, "deadline_reminder"))
                notification_service.mark_notified(notif)


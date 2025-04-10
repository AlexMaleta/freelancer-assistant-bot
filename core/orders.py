from typing import Optional, List

from config.constants import Statuses
from core.order_stages import OrderStageService
from models.orders import OrderCreate, OrderInDB
from database import orders as order_db
from datetime import datetime

order_stages_service = OrderStageService()


class OrderService:
    def create_order(self, order_data: OrderCreate) -> int:
        return order_db.create_order(order_data)

    def get_orders_by_user(self, user_id: int, status_id: Optional[int] = None) -> List[OrderInDB]:
        """
        Returns a list of user orders.
        Can be filtered by status.
        """
        return order_db.get_all_orders_by_user(user_id, status_id)

    def get_by_id(self, order_id: int) -> Optional[OrderInDB]:
        return order_db.get_order_by_id(order_id)

    def update_order_status(self, order_id: int, status_id: int) -> bool:
        return order_db.update_order(order_id, status_id=status_id)

    def update_order_fields(
            self,
            order_id: int,
            name: Optional[str] = None,
            description: Optional[str] = None,
            status_id: Optional[int] = 1,
            deadline: Optional[datetime] = None
    ) -> bool:
        """
        Updates order fields. Only transferred fields.
        If the status changes to COMPLETED — automatically completes the stages.
        """
        if order_db.update_order(
                order_id,
                name=name,
                description=description,
                status_id=status_id,
                deadline=deadline
        ):
            if status_id == Statuses.COMPLETED:
                self.check_setage_if_order_completed(order_id)

            return True
        else:
            return False

    def delete_order(self, order_id: int) -> bool:
        """
        Deletes an order and all stages associated with it (cascade).
        """
        stages = order_stages_service.get_stages_by_order(order_id)
        if stages:
            for stage in stages:
                order_stages_service.delete_stage(stage.id)
        return order_db.delete_order(order_id)

    def check_order_if_stage_completed(self, order_id: int) -> bool:
        """
        Checks: if all stages are completed - mark the order as completed.
        """
        stages = order_stages_service.get_stages_by_order(order_id)
        if all(stage.status_id == Statuses.COMPLETED for stage in stages):
            self.update_order_fields(order_id, status_id=Statuses.COMPLETED)
            return True
        return False


    def check_setage_if_order_completed(self, order_id: int) -> bool:
        """
        Checks: if the order is completed - completes all active stages.
        """
        stages = order_stages_service.get_stages_by_order(order_id)
        if stages:
            for stage in stages:
                if stage.status_id in Statuses.ACTIVE:
                    order_stages_service.update_stage(stage_id=stage.id, status_id=Statuses.COMPLETED)
                    return True
        else:
            return False
        return False

    def get_orders_with_deadline(self, date: datetime) -> list:
        """
        Returns orders with a deadline on the specified date.
        Used in the reminder scheduler.
        """
        return order_db.get_orders_with_deadline(date.date().isoformat())


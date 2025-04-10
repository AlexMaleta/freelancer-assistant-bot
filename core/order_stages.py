from typing import Optional, List
from datetime import datetime

from config.constants import Statuses
from core.checklist_items import ChecklistService
from models.order_stages import StageCreate, StageInDB
from database import order_stages as stage_db

checklist_service = ChecklistService()


class OrderStageService:
    def create_stage(self, data: StageCreate) -> int:
        return stage_db.create_stage(data)

    def get_stage_by_id(self, stage_id: int) -> Optional[StageInDB]:
        return stage_db.get_stage_by_id(stage_id)

    def get_stages_by_order(self, order_id: int, status_id: Optional[int] = None) -> List[StageInDB]:
        return stage_db.get_all_stages_by_order(order_id, status_id)

    def update_stage(
            self,
            stage_id: int,
            name: Optional[str] = None,
            description: Optional[str] = None,
            status_id: Optional[int] = 1,
            deadline: Optional[datetime] = None
    ) -> bool:
        """
        Update one or more fields of a stage.
        If stage is marked as COMPLETED, automatically check and update checklist items and parent order.
        """
        from core.orders import OrderService
        if stage_db.update_stage(
                stage_id,
                name=name,
                description=description,
                status_id=status_id,
                deadline=deadline
        ):
            if status_id == Statuses.COMPLETED:
                self.check_items_if_stage_completed(stage_id)
                order_service = OrderService()
                order_service.check_order_if_stage_completed(stage_id)

            return True
        else:
            return False

    def delete_stage(self, stage_id: int) -> bool:
        """
        Delete a stage and all of its associated checklist items.
        """
        checklist_items = checklist_service.get_items_by_stage(stage_id)
        if checklist_items:
            for checklist_item in checklist_items:
                checklist_service.delete_item(checklist_item.id)
        return stage_db.delete_stage(stage_id)

    def check_stage_if_item_completed(self, item_id: int) -> bool:
        """
         If the stage is completed, we complete everything in its checklist
        """
        from core.orders import OrderService
        item = checklist_service.get_item_by_id(item_id)
        items = checklist_service.get_items_by_stage(item.stage_id)
        if all(item.status_id == Statuses.COMPLETED for item in items):
            self.update_stage(stage_id=item.stage_id, status_id=Statuses.COMPLETED)
            stage = self.get_stage_by_id(item.stage_id)
            order_service = OrderService()
            order_service.check_order_if_stage_completed(stage.order_id)
            return True
        return False

    def check_items_if_stage_completed(self, stage_id: int) -> bool:
        """
        If all checklist items are completed, automatically mark the stage as completed.
        """
        items = checklist_service.get_items_by_stage(stage_id)
        if items:
            for item in items:
                if item.status_id in Statuses.ACTIVE:
                    checklist_service.update_item(item_id=item.id, status_id=Statuses.COMPLETED)
                    return True
        else:
            return False
        return False

    def get_stages_with_deadline(self, date: datetime) -> list:
        """
        Used by scheduler: return stages that are due on a specific date.
        """
        return stage_db.get_stages_with_deadline(date.date().isoformat())

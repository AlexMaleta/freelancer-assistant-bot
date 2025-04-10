from typing import Optional, List
from models.checklist_items import ChecklistItemCreate, ChecklistItemInDB
from database import checklist_items as checklist_db


class ChecklistService:
    def create_item(self, item_data: ChecklistItemCreate) -> int:
        return checklist_db.create_checklist_item(item_data)

    def get_item_by_id(self, item_id: int) -> Optional[ChecklistItemInDB]:
        return checklist_db.get_checklist_item_by_id(item_id)

    def get_items_by_stage(self, stage_id: int, status_id: Optional[int] = None) -> List[ChecklistItemInDB]:
        return checklist_db.get_all_items_by_stage(stage_id, status_id)

    def update_item(
        self,
        item_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status_id: Optional[int] = 1
    ) -> bool:
        """
        Update fields of a checklist item.
        If item is marked as completed, trigger re-evaluation of its parent stage.
        """
        from core.order_stages import OrderStageService
        stage_service = OrderStageService()
        if checklist_db.update_checklist_item(
            item_id,
            name=name,
            description=description,
            status_id=status_id
        ):
            stage_service.check_stage_if_item_completed(item_id)
            return True
        else:
            return False

    def delete_item(self, item_id: int) -> bool:
        return checklist_db.delete_checklist_item(item_id)

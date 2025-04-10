from database.database import get_connection
from models.checklist_items import ChecklistItemCreate, ChecklistItemInDB
from typing import Optional, List
from datetime import datetime


def create_checklist_item(item: ChecklistItemCreate) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO checklist_items (stage_id, name, description, status_id, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            item.stage_id,
            item.name,
            item.description,
            item.status_id,
            datetime.utcnow()
        ))
        return cursor.lastrowid


def get_checklist_item_by_id(item_id: int) -> Optional[ChecklistItemInDB]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, stage_id, name, description, status_id, created_at, updated_at
            FROM checklist_items
            WHERE id = ?
        """, (item_id,))
        row = cursor.fetchone()
        if row:
            return ChecklistItemInDB(
                id=row[0],
                stage_id=row[1],
                name=row[2],
                description=row[3],
                status_id=row[4],
                created_at=row[5],
                updated_at=row[6]
            )
        return None


def get_all_items_by_stage(stage_id: int, status_id: Optional[int] = None) -> List[ChecklistItemInDB]:
    with get_connection() as conn:
        cursor = conn.cursor()

        if status_id is not None:
            cursor.execute("""
                SELECT id, stage_id, name, description, status_id, created_at, updated_at
                FROM checklist_items
                WHERE stage_id = ? AND status_id = ?
                ORDER BY created_at
            """, (stage_id, status_id))
        else:
            cursor.execute("""
                SELECT id, stage_id, name, description, status_id, created_at, updated_at
                FROM checklist_items
                WHERE stage_id = ?
                ORDER BY created_at
            """, (stage_id,))

        rows = cursor.fetchall()
        return [
            ChecklistItemInDB(
                id=row[0],
                stage_id=row[1],
                name=row[2],
                description=row[3],
                status_id=row[4],
                created_at=row[5],
                updated_at=row[6]
            )
            for row in rows
        ]


def update_checklist_item(item_id: int,
                          name: Optional[str] = None,
                          description: Optional[str] = None,
                          status_id: Optional[int] = None) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()

        fields = []
        values = []

        if name is not None:
            fields.append("name = ?")
            values.append(name)
        if description is not None:
            fields.append("description = ?")
            values.append(description)
        if status_id is not None:
            fields.append("status_id = ?")
            values.append(status_id)

        if not fields:
            return False

        fields.append("updated_at = ?")
        values.append(datetime.utcnow())
        values.append(item_id)

        sql = f"""
            UPDATE checklist_items
            SET {', '.join(fields)}
            WHERE id = ?
        """

        cursor.execute(sql, values)
        return cursor.rowcount > 0


def delete_checklist_item(item_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM checklist_items
            WHERE id = ?
        """, (item_id,))
        return cursor.rowcount > 0

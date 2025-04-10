from database.database import get_connection
from models.order_stages import StageCreate, StageInDB
from typing import Optional, List
from datetime import datetime


def create_stage(stage: StageCreate) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO order_stages (order_id, name, description, status_id, deadline, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            stage.order_id,
            stage.name,
            stage.description,
            stage.status_id,
            stage.deadline,
            datetime.utcnow()
        ))
        return cursor.lastrowid


def get_stage_by_id(stage_id: int) -> Optional[StageInDB]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, order_id, name, description, status_id, deadline, created_at, updated_at
            FROM order_stages
            WHERE id = ?
        """, (stage_id,))
        row = cursor.fetchone()
        if row:
            return StageInDB(
                id=row[0],
                order_id=row[1],
                name=row[2],
                description=row[3],
                status_id=row[4],
                deadline=row[5],
                created_at=row[6],
                updated_at=row[7]
            )
        return None


def get_all_stages_by_order(order_id: int, status_id: Optional[int] = None) -> List[StageInDB]:
    with get_connection() as conn:
        cursor = conn.cursor()

        if status_id is not None:
            cursor.execute("""
                SELECT id, order_id, name, description, status_id, deadline, created_at, updated_at
                FROM order_stages
                WHERE order_id = ? AND status_id = ?
                ORDER BY created_at
            """, (order_id, status_id))
        else:
            cursor.execute("""
                SELECT id, order_id, name, description, status_id, deadline, created_at, updated_at
                FROM order_stages
                WHERE order_id = ?
                ORDER BY created_at
            """, (order_id,))

        rows = cursor.fetchall()
        return [
            StageInDB(
                id=row[0],
                order_id=row[1],
                name=row[2],
                description=row[3],
                status_id=row[4],
                deadline=row[5],
                created_at=row[6],
                updated_at=row[7]
            )
            for row in rows
        ]


def update_stage(stage_id: int,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 status_id: Optional[int] = None,
                 deadline: Optional[datetime] = None) -> bool:
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
        if deadline is not None:
            fields.append("deadline = ?")
            values.append(deadline)

        if not fields:
            return False

        fields.append("updated_at = ?")
        values.append(datetime.utcnow())
        values.append(stage_id)

        sql = f"""
            UPDATE order_stages
            SET {', '.join(fields)}
            WHERE id = ?
        """

        cursor.execute(sql, values)
        return cursor.rowcount > 0


def delete_stage(stage_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM order_stages
            WHERE id = ?
        """, (stage_id,))
        return cursor.rowcount > 0


def get_stages_with_deadline(date_str: str) -> list:
    """
    Return all active or in-progress stages with a deadline on the given date.
    Parameters:
        date_str (str): Target deadline date in YYYY-MM-DD format.
    Returns:
        list[StageInDB]: List of matching order stages.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, order_id, name, description, status_id, created_at, deadline, updated_at
            FROM order_stages
            WHERE (status_id = 1 or status_id =2) and DATE(deadline) = ?
        """, (date_str,))
        rows = cursor.fetchall()

        return [StageInDB(
            id=row[0],
            order_id=row[1],
            name=row[2],
            description=row[3],
            status_id=row[4],
            created_at=row[5],
            deadline=row[6],
            updated_at=row[7],
        ) for row in rows]

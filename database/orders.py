from database.database import get_connection
from models.orders import OrderCreate, OrderInDB
from typing import Optional, List
from datetime import datetime


def create_order(order: OrderCreate) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (user_id, customer_id, name, description, status_id, deadline, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            order.user_id,
            order.customer_id,
            order.name,
            order.description,
            order.status_id,
            order.deadline,
            datetime.utcnow()
        ))
        return cursor.lastrowid


def get_order_by_id(order_id: int) -> Optional[OrderInDB]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, customer_id, name, description, status_id, deadline, created_at, updated_at
            FROM orders
            WHERE id = ?
        """, (order_id,))
        row = cursor.fetchone()
        if row:
            return OrderInDB(
                id=row[0],
                user_id=row[1],
                customer_id=row[2],
                name=row[3],
                description=row[4],
                status_id=row[5],
                deadline=row[6],
                created_at=row[7],
                updated_at=row[8]
            )
        return None


def get_all_orders_by_user(
        user_id: int,
        status_id: Optional[int] = None,
        customer_id: Optional[int] = None) -> List[OrderInDB]:
    with get_connection() as conn:
        cursor = conn.cursor()

        query = """
        SELECT id, user_id, customer_id, name, description, status_id, deadline, created_at, updated_at
        FROM orders
        WHERE user_id = ?
        """
        params = [user_id]

        if status_id is not None:
            query += " AND status_id = ?"
            params.append(status_id)

        if customer_id is not None:
            query += " AND customer_id = ?"
            params.append(customer_id)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [
            OrderInDB(
                id=row[0],
                user_id=row[1],
                customer_id=row[2],
                name=row[3],
                description=row[4],
                status_id=row[5],
                deadline=row[6],
                created_at=row[7],
                updated_at=row[8],
            )
            for row in rows
        ]


def update_order(order_id: int,
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
        values.append(order_id)

        sql = f"""
            UPDATE orders
            SET {', '.join(fields)}
            WHERE id = ?
        """

        cursor.execute(sql, values)
        return cursor.rowcount > 0


def delete_order(order_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM orders
            WHERE id = ?
        """, (order_id,))
        return cursor.rowcount > 0


def get_orders_with_deadline(date_str: str) -> list:
    """
    Return all active or in-progress orders with a deadline on the given date.
    Parameters:
        date_str (str): Target deadline date in YYYY-MM-DD format.
    Returns:
        list[OrderInDB]: List of matching orders.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, customer_id, name, description, status_id, created_at, deadline, updated_at
            FROM orders
            WHERE (status_id = 1 or status_id = 2) and DATE(deadline) = ?
        """, (date_str,))
        rows = cursor.fetchall()

        from models.orders import OrderInDB
        return [OrderInDB(
            id=row[0],
            user_id=row[1],
            customer_id=row[2],
            name=row[3],
            description=row[4],
            status_id=row[5],
            created_at=row[6],
            deadline=row[7],
            updated_at=row[8],
        ) for row in rows]


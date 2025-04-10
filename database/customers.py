from database.database import get_connection
from models.customers import CustomerCreate, CustomerInDB
from typing import Optional, List
from datetime import datetime


def create_customer(customer: CustomerCreate) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customers (user_id, name, phone, email, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            customer.user_id,
            customer.name,
            customer.phone,
            customer.email,
            customer.notes,
            datetime.utcnow()
        ))
        return cursor.lastrowid


def get_customer_by_id(customer_id: int) -> Optional[CustomerInDB]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, name, phone, email, notes, created_at, updated_at
            FROM customers
            WHERE id = ?
        """, (customer_id,))
        row = cursor.fetchone()
        if row:
            return CustomerInDB(
                id=row[0],
                user_id=row[1],
                name=row[2],
                phone=row[3],
                email=row[4],
                notes=row[5],
                created_at=row[6],
                updated_at=row[7]
            )
        return None


def update_customer(customer_id: int,
                    name: Optional[str] = None,
                    phone: Optional[str] = None,
                    email: Optional[str] = None,
                    notes: Optional[str] = None) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        fields = []
        values = []

        if name is not None:
            fields.append("name = ?")
            values.append(name)
        if phone is not None:
            fields.append("phone = ?")
            values.append(phone)
        if email is not None:
            fields.append("email = ?")
            values.append(email)
        if notes is not None:
            fields.append("notes = ?")
            values.append(notes)

        if not fields:
            return False

        fields.append("updated_at = ?")
        values.append(datetime.utcnow())
        values.append(customer_id)

        sql = f"""
            UPDATE customers
            SET {', '.join(fields)}
            WHERE id = ?
        """

        cursor.execute(sql, values)
        return cursor.rowcount > 0


def delete_customer(customer_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM customers
            WHERE id = ?
        """, (customer_id,))
        return cursor.rowcount > 0


def get_all_customers_by_user(user_id: int) -> List[CustomerInDB]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, name, phone, email, notes, created_at, updated_at
            FROM customers
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        return [
            CustomerInDB(
                id=row[0],
                user_id=row[1],
                name=row[2],
                phone=row[3],
                email=row[4],
                notes=row[5],
                created_at=row[6],
                updated_at=row[7]
            )
            for row in rows
        ]


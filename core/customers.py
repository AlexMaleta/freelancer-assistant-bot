from typing import Optional, List

from core.orders import OrderService
from database.orders import get_all_orders_by_user
from models.customers import CustomerCreate, CustomerInDB
from database import customers as customer_db


order_service = OrderService()

class CustomerService:
    def create_customer(self, data: CustomerCreate) -> int:
        return customer_db.create_customer(data)

    def get_customer_by_id(self, customer_id: int) -> Optional[CustomerInDB]:
        return customer_db.get_customer_by_id(customer_id)

    def get_customers_by_user(self, user_id: int) -> List[CustomerInDB]:
        return customer_db.get_all_customers_by_user(user_id)

    def update_customer(
        self,
        customer_id: int,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        return customer_db.update_customer(
            customer_id,
            name=name,
            phone=phone,
            email=email,
            notes=notes
        )

    def delete_customer(self, customer_id: int) -> bool:
        """
        Delete customer and all related orders (with cascade).
        """
        customer = customer_db.get_customer_by_id(customer_id)
        orders = get_all_orders_by_user(user_id=customer.user_id, customer_id=customer_id)
        if orders:
            for order in orders:
                order_service.delete_order(order.id)
        return customer_db.delete_customer(customer_id)

from .fallback import router as fallback_router
from .start import router as start_router
from .customers import router as customers_router
from .orders import router as orders_router
from .order_stages import router as stages_router
from .checklist_items import router as checklist_router
from .settings import router as settings_router

all_routers = [
    start_router,
    customers_router,
    orders_router,
    stages_router,
    checklist_router,
    settings_router,
    fallback_router
]

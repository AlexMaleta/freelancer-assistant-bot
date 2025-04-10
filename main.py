import asyncio
from datetime import datetime

from bot.bot import main
from database.models import init_db
from scheduler.scheduler import setup_scheduler
from scripts.init_statuses import init_statuses


async def startup():
    now = datetime.now()
    print(f"⏰ Launch in {now.strftime('%Y-%m-%d %H:%M:%S')}")

    init_db()
    init_statuses()

    setup_scheduler()

    await main()

if __name__ == '__main__':
    asyncio.run(startup())
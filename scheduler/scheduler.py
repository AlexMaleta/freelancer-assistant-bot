from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from scheduler.tasks import check_upcoming_deadlines

scheduler = AsyncIOScheduler()


def setup_scheduler():
    # Every day at 8:00 am server time
    scheduler.add_job(check_upcoming_deadlines, CronTrigger(hour=8, minute=0))
    scheduler.start()
    print("✅ Scheduler launched")

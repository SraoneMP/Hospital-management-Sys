import os
from celery import Celery
from celery.schedules import crontab

# ============================================================================
# CONFIGURE REMINDER AND REPORT TIMES HERE
# ============================================================================
# Change these values to adjust when tasks run, then restart Celery Beat
DAILY_REMINDER_HOUR = 13        # Hour in 24-hour format (0-23)
DAILY_REMINDER_MINUTE = 53      # Minute (0-59)

MONTHLY_REPORT_DAY = '29'        # Day of month (1-31) - use string format
MONTHLY_REPORT_HOUR = 13         # Hour in 24-hour format (0-23)
MONTHLY_REPORT_MINUTE = 53       # Minute (0-59)
# ============================================================================

def make_celery():
    broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    backend_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    celery = Celery(
        "hms",
        broker=broker_url,
        backend=backend_url,
        include=["tasks"],  # auto-discover our task module
    )
    celery.conf.timezone = os.getenv("TZ", "Asia/Kolkata")
    
    celery.conf.beat_schedule = {
        "daily-reminders": {
            "task": "tasks.daily_reminders",
            "schedule": crontab(
                hour=DAILY_REMINDER_HOUR,
                minute=DAILY_REMINDER_MINUTE
            ),
        },
        "monthly-activity-report": {
            "task": "tasks.monthly_activity_report",
            "schedule": crontab(
                hour=MONTHLY_REPORT_HOUR,
                minute=MONTHLY_REPORT_MINUTE,
                day_of_month=MONTHLY_REPORT_DAY
            ),
        },
    }
    
    print(f"📅 Celery Beat Schedule Configured:")
    print(f"   - Daily Reminders: Every day at {DAILY_REMINDER_HOUR:02d}:{DAILY_REMINDER_MINUTE:02d} IST")
    print(f"   - Monthly Reports: Day {MONTHLY_REPORT_DAY} at {MONTHLY_REPORT_HOUR:02d}:{MONTHLY_REPORT_MINUTE:02d} IST")
    
    return celery

celery = make_celery()

if __name__ == "__main__":
    celery.start()

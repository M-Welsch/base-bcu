from datetime import datetime, timedelta

from base.asyncio_demo.wakeup_reason import WakeupReason


def calculate_backup_time(wakeup_reason):
    backup_time = datetime.now()
    if wakeup_reason != WakeupReason.BACKUP_NOW:
        backup_time += timedelta(seconds=3)  # Get from config file instead
    return backup_time

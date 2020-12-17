import sys
import os
from datetime import datetime, timedelta
path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)
from base.common.config import Config


class TimeCalculator:
    def __init__(self):
        self._bu_config = Config(path_to_module+"/base/config/schedule_backup.json")

    def next_bu(self):
        if self._bu_config.backup_frequency == "days":
            next = self._next_daily_bu()

        elif self._bu_config.backup_frequency == "weeks":
            next = self._next_weekly_bu()

        elif self._bu_config.backup_frequency == "months":
            next = self._next_monthly_bu()

        else:
            print("invalid backup frequency!")

        return next

    def _next_daily_bu(self):
        now = datetime.now()
        next_bu = datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=self._bu_config.hour,
            minute=self._bu_config.minute
        )
        while next_bu < now:
            next_bu = next_bu + timedelta(days=1)
        return next_bu

    def _next_weekly_bu(self):
        now = datetime.now()
        next_bu = datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=self._bu_config.hour,
            minute=self._bu_config.minute
        )
        target_day_of_week = self._bu_config.day_of_week
        while next_bu.weekday() < target_day_of_week:
            next_bu = next_bu + timedelta(days=1)
        while next_bu < now:
            next_bu = next_bu + timedelta(days=7)
        return next_bu

    def _next_monthly_bu(self):
        now = datetime.now()
        next_bu = datetime(
            year=now.year,
            month=now.month,
            day=self._bu_config.day_of_month,
            hour=self._bu_config.hour,
            minute=self._bu_config.minute
        )
        while next_bu < now:
            next_bu = self._increment_one_month(next_bu)
        return next_bu

    @staticmethod
    def _increment_one_month(orig_date):
        target_day_of_month = orig_date.day
        incremented = orig_date + timedelta(days=1)
        while not incremented.day == target_day_of_month:
            incremented = incremented + timedelta(days=1)
        return incremented


if __name__ == '__main__':
    TC = TimeCalculator()
    print(TC.next_bu())
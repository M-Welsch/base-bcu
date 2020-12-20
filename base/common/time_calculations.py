from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from base.common.config import Config


class TimeCalculator:
    increments = {
        "days": timedelta(days=1),
        "weeks": timedelta(weeks=1),
        "months": relativedelta(months=1)
    }

    def next_backup(self, plan: Config) -> datetime:
        self._validate_plan(plan)
        now = datetime.now()
        next_backup = datetime(
            year=now.year,
            month=now.month,
            day=plan.day_of_month if plan.backup_frequency == "months" else now.day,
            hour=plan.hour,
            minute=plan.minute
        )

        if plan.backup_frequency == "weekly":
            while next_backup.weekday() < plan.day_of_week:
                next_backup = next_backup + timedelta(days=1)

        if next_backup < now:
            next_backup += TimeCalculator.increments[plan.backup_frequency]

        return next_backup

    @staticmethod
    def _validate_plan(plan):  # TODO: Test this function
        assert plan.backup_frequency in TimeCalculator.increments.keys()
        assert 0 <= plan.day_of_month <= 31
        assert 0 <= plan.day_of_week <= 6
        assert 0 <= plan.hour <= 23
        assert 0 <= plan.minute <= 59


if __name__ == '__main__':
    from pathlib import Path

    Config.set_config_base_dir(Path(__file__).parent.parent/"config")
    config = Config("schedule_backup.json")

    print(TimeCalculator().next_backup(config))

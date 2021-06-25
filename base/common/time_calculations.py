from collections import namedtuple
from datetime import datetime

from dateutil.rrule import DAILY, MONTHLY, WEEKLY, rrule

from base.common.config import Config

_Plan = namedtuple("Plan", "frequency monthday weekday hour minute second")


class TimeCalculator:
    _frequencies = {"days": DAILY, "weeks": WEEKLY, "months": MONTHLY}

    def next_backup(self, config: Config) -> datetime:
        plan = self._plan_from_config(config)
        return next(
            iter(
                rrule(
                    freq=plan.frequency,
                    bymonthday=plan.monthday,
                    byweekday=plan.weekday,
                    byhour=plan.hour,
                    byminute=plan.minute,
                    bysecond=plan.second,
                )
            )
        )

    def next_backup_timestring(self, config: Config) -> str:
        dt = self.next_backup(config)
        return dt.strftime("%d.%m.%Y %H:%M")

    def next_backup_seconds(self, config: Config) -> int:
        dt = self.next_backup(config)
        return int((dt - datetime.now()).total_seconds())

    def _plan_from_config(self, config: Config) -> _Plan:
        self._validate_config(config)
        frequency = TimeCalculator._frequencies[config.backup_frequency]
        return _Plan(
            frequency=frequency,
            monthday=config.day_of_month if frequency == MONTHLY else None,
            weekday=config.day_of_week if frequency == WEEKLY else None,
            hour=config.hour,
            minute=config.minute,
            second=config.second,
        )

    @staticmethod
    def _validate_config(config: Config) -> None:
        assert config.backup_frequency in TimeCalculator._frequencies.keys()
        assert 1 <= config.day_of_month <= 31
        assert 0 <= config.day_of_week <= 6
        assert 0 <= config.hour <= 23
        assert 0 <= config.minute <= 59
        assert 0 <= config.second <= 59


if __name__ == "__main__":
    from pathlib import Path

    Config.set_config_base_path(Path(__file__).parent.parent / "config")
    conf = Config("schedule_backup.json")

    print(TimeCalculator().next_backup(conf))

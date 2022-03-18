from collections import namedtuple
from datetime import datetime

from dateutil.rrule import DAILY, MONTHLY, WEEKLY, rrule

from base.common.config import Config
from base.common.constants import next_backup_timestring_format_for_sbu

_Plan = namedtuple("_Plan", "freq bymonthday byweekday byhour byminute")


BACKUP_INTERVALS = {"days": DAILY, "weeks": WEEKLY, "months": MONTHLY}


def next_backup(config: Config) -> datetime:
    plan = _plan_from_config(config)
    next_backup_time: datetime = next(iter(rrule(**plan._asdict())))
    return next_backup_time


def next_backup_timestring(config: Config) -> str:
    dt = next_backup(config)
    return dt.strftime(next_backup_timestring_format_for_sbu)


def next_backup_seconds(config: Config) -> int:
    dt = next_backup(config)
    return int((dt - datetime.now()).total_seconds())


def _plan_from_config(config: Config) -> _Plan:
    interval = BACKUP_INTERVALS[config.backup_interval]
    return _Plan(
        freq=interval,
        bymonthday=config.day_of_month if interval == MONTHLY else None,
        byweekday=config.day_of_week if interval == WEEKLY else None,
        byhour=config.hour,
        byminute=config.minute,
    )

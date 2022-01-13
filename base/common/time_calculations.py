from collections import namedtuple
from datetime import datetime

from dateutil.rrule import DAILY, MONTHLY, WEEKLY, rrule

from base.common.config import Config
from base.common.exceptions import ConfigValidationError

_Plan = namedtuple("_Plan", "freq bymonthday byweekday byhour byminute bysecond")


BACKUP_INTERVALS = {"days": DAILY, "weeks": WEEKLY, "months": MONTHLY}


def next_backup(config: Config) -> datetime:
    plan = _plan_from_config(config)
    next_backup_time: datetime = next(iter(rrule(**plan._asdict())))
    return next_backup_time


def next_backup_timestring(config: Config) -> str:
    dt = next_backup(config)
    return dt.strftime("%d.%m.%Y %H:%M")


def next_backup_seconds(config: Config) -> int:
    dt = next_backup(config)
    return int((dt - datetime.now()).total_seconds())


def _plan_from_config(config: Config) -> _Plan:
    _validate_config(config)
    interval = BACKUP_INTERVALS[config.backup_interval]
    return _Plan(
        freq=interval,
        bymonthday=config.day_of_month if interval == MONTHLY else None,
        byweekday=config.day_of_week if interval == WEEKLY else None,
        byhour=config.hour,
        byminute=config.minute,
        bysecond=config.second,
    )


def _validate_config(config: Config) -> None:
    if config.backup_interval not in BACKUP_INTERVALS.keys():
        raise ConfigValidationError(f"Invalid interval: '{config.backup_interval}'")
    if not 1 <= config.day_of_month <= 31:
        raise ConfigValidationError(f"Invalid day of month: '{config.day_of_month}'")
    if not 0 <= config.day_of_week <= 6:
        raise ConfigValidationError(f"Invalid day_of_week: '{config.day_of_week}'")
    if not 0 <= config.hour <= 23:
        raise ConfigValidationError(f"Invalid hour: '{config.hour}'")
    if not 0 <= config.minute <= 59:
        raise ConfigValidationError(f"Invalid minute: '{config.minute}'")
    if not 0 <= config.second <= 59:
        raise ConfigValidationError(f"Invalid second: '{config.second}'")

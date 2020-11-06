from schedule import Scheduler as Scheduler
import pudb
from base.common.exceptions import *
import logging


class BaseScheduler(Scheduler):
    def __init__(self, config_schedule):
        super(BaseScheduler, self).__init__()
        self._config_schedule = config_schedule
        self.backup_suggested = False
        self.setup_schedule()

    def setup_schedule(self):
        # pudb.set_trace()
        backup_frequency = self._config_schedule["backup_frequency"]
        minutes_and_hours = f'{int(self._config_schedule["hour"]):02d}:{int(self._config_schedule["minute"]):02d}'
        if backup_frequency == 'Minutely':
            self.every(self._config_schedule["minute"]).minutes.do(self._suggest_backup)
            logging_message = f'Schedule: Frequency = Minutely, every {self._config_schedule["minute"]} minutes'
        elif backup_frequency == 'Hourly':
            self.every(self._config_schedule["minute"]).hour.do(self._suggest_backup)
            logging_message = f'Schedule: Frequency = Hourly at hh:{self._config_schedule["minute"]}'
        elif backup_frequency == 'Daily':
            self.every().day.at(minutes_and_hours).do(self._suggest_backup)
            logging_message = f'Schedule: Frequency = Daily at {minutes_and_hours}'
        elif backup_frequency == 'Weekly':
            self._setup_schedule_for_weekly(minutes_and_hours)
            logging_message = f'Schedule: Frequency = Weekly, every ' \
                              f'{self._config_schedule["day_of_week"]}th day of week at {minutes_and_hours}'
        else:
            raise ScheduleError("No valid backup interval specified!")
        logging.info(logging_message)
        print(logging_message)
    # Todo: Monthly

    def _setup_schedule_for_weekly(self, minutes_and_hours):
        day_of_week = int(self._config_schedule["day_of_week"])
        if day_of_week == 1:
            self.every().monday.at(minutes_and_hours).do(self._suggest_backup)
        elif day_of_week == 2:
            self.every().tuesday.at(minutes_and_hours).do(self._suggest_backup)
        elif day_of_week == 3:
            self.every().wednesday.at(minutes_and_hours).do(self._suggest_backup)
        elif day_of_week == 4:
            self.every().thursday.at(minutes_and_hours).do(self._suggest_backup)
        elif day_of_week == 5:
            self.every().friday.at(minutes_and_hours).do(self._suggest_backup)
        elif day_of_week == 6:
            self.every().saturday.at(minutes_and_hours).do(self._suggest_backup)
        elif day_of_week == 7:
            self.every().sunday.at(minutes_and_hours).do(self._suggest_backup)
        else:
            logging.warning(
                f"Day of week was entered as {day_of_week}, which is invalid (1-7 is ok). Setting to Sunday"
            )
            self._config_schedule["day_of_week"] = 7
            self._setup_schedule_for_weekly(minutes_and_hours)

    def _suggest_backup(self):
        print("Suggesting backup...")
        self.backup_suggested = True

    def is_backup_scheduled(self):
        self.run_pending()
        result = self.backup_suggested
        return result

    def next_backup_scheduled(self):
        return self.next_backup_scheduled_raw().strftime('%d.%m.%Y %H:%M')

    def next_backup_scheduled_raw(self):
        # returns datetime-object
        return self.next_run

    def seconds_to_next_bu(self):
        seconds_to_next_bu = self.idle_seconds
        return seconds_to_next_bu

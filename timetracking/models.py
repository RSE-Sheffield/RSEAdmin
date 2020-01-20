from django.db import models
from rse.models import *
from datetime import datetime, date
from django.conf import settings


class TimeSheetEntry(models.Model):
    """
    Represents a single time sheet entry (either full day or hourly)
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    rse = models.ForeignKey(RSE, on_delete=models.CASCADE)
    date = models.DateField()
    all_day = models.BooleanField(default=False) 
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    def duration(self):
        """ duration is is based off the global WORKING_HOURS_PER_DAY value (if all day event) or the actual hours if hourly entry """
        if self.all_day:
            return settings.WORKING_HOURS_PER_DAY
        else: # Need to construct a valid datetime object to subtract
            return datetime.combine(date.min, self.end_time) - datetime.combine(date.min, self.start_time)

    @staticmethod
    def working_days(tses) -> float:
        """ 
        Get the working days recorded on timesheet for project for the specified time sheet entries.
        These must have been pre filtered to include only the records of interest.
        """

        timesheet_days_sum = 0

        # Loop through time sheet entries and accumulate
        for tse in tses:
            date = tse.date
            # accumulate time
            if tse.all_day:
                timesheet_days_sum += 1
            else:
                timesheet_days_sum += (datetime.combine(date.today(), tse.end_time) - datetime.combine(date.today(), tse.start_time)).seconds / (60*60*settings.WORKING_HOURS_PER_DAY) # convert hours to fractional days

        return timesheet_days_sum
 
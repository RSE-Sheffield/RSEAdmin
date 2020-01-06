from django.db import models
from rse.models import *
from datetime import datetime, date


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
        if self.all_day:
            return 7.5
        else: # Need to construct a valid datetime object to subtract
            return datetime.combine(date.min, self.end_time) - datetime.combine(date.min, self.start_time)
 
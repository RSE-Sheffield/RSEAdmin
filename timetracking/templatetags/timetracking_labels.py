from django import template
from django.db.models import QuerySet
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

register = template.Library()

@register.filter
def days_to_days_and_hours(value):
    """ converts day to string representation of days and hours (based of working day length)"""
    days = int(value)
    hours = value % 1*settings.WORKING_HOURS_PER_DAY
    return f"{days} days and {hours:.2f} hours"


@register.filter
def days_to_d_and_h(value):
    """ converts day to string representation of days and hours (based of working day length). Short version."""
    days = int(value)
    hours = value % 1*settings.WORKING_HOURS_PER_DAY
    return f"{days} d + {hours:.2f} h"


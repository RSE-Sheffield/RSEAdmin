from django import template
from django.db.models import QuerySet
from rse.models import *
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()

@register.filter
def projectstatuslabel(value):
    """Converts a project status to a bootstrap label"""
    if value == Project.PREPARATION:
        return "label-warning"
    elif value == Project.REVIEW:
        return "label-info"
    elif value == Project.FUNDED:
        return "label-success"
    else:
        return "label-danger"        


@register.filter
def schedulestatuslabel(value):
    """Converts a project status to a bootstrap label"""
    if value == Project.SCHEDULE_SCHEDULED:
        return "label-warning"
    elif value == Project.SCHEDULE_COMPLETED:
        return "label-info"
    elif value == Project.SCHEDULE_ACTIVE:
        return "label-success"
    else:
        return "label-danger"    

@register.filter
def progressbar_colour(value: float):
    """Converts a percentage to a bootstrap label"""
    if value > 99.5:
        return "progress-bar-green"
    elif value < 50.0:
        return "progress-bar-red"
    else:
        return "progress-bar-yellow"    
              


@register.filter      
def isrseuser(value):
    """ Return true for users who are RSEs. Value must eb a user. """
    try:
        rse = RSE.objects.get(user=value)
        return True
    except ObjectDoesNotExist:
        return False

@register.filter
def percent(value):
    return f"{value:.0f}"

@register.filter
def dp2(value):
    return f"{value:.2f}"

@register.simple_tag
def sum_project_allocation_percentage(project: Project, allocations: QuerySet):
    """
    Cost distributions include any active allocation. It is possible that there may be multiple allocations active within a cost
    distribution period related to the same project (i.e. someone is allocated 5% and 10% on the same project but for different 
    overlapping durations). This filter will provide a sum (or empty string if 0) of allocation percentages for the given proejct.
    """
    sum = 0
    for a in allocations:
        if a.project == project:
            sum += a.percentage
    if sum > 0:
        return f"{sum}%"
    else:
        return ""

@register.simple_tag
def sum_allocation_percentage(allocations: QuerySet):
    """
    Sums the allocation percentages for a cost distribution.
    """
    sum = 0
    for a in allocations:
        sum += a.percentage

    return f"{sum}%"


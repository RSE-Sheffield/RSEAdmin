from django import template
from rse.models import *
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()

@register.filter
def projectstatuslabel(value):
    """Concerts a project status to a bootstrap label"""
    if value == Project.PREPARATION:
        return "label-warning"
    elif value == Project.REVIEW:
        return "label-info"
    elif value == Project.FUNDED:
        return "label-success"
    else:
        return "label-danger"        
        

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

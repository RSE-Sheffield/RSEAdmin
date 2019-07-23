from django import template
from rse.models import *

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
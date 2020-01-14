from django import template
from django.db.models import QuerySet
from rse.models import *
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()


@register.simple_tag
def timetracking_installed():
  from django.apps import apps
  return apps.is_installed("timetracking")

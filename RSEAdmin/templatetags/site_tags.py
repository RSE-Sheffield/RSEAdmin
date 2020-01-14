from django import template
from django.db.models import QuerySet
from rse.models import *
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()


@register.simple_tag
def test_tag():
  return True

@register.simple_tag
def timetracking_installed():
  from django.apps import apps
  logger.error(apps.is_installed("timetracking.apps.TimetrackingConfig"))
  return apps.is_installed("timetracking.apps.TimetrackingConfig")

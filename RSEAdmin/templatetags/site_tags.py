from django import template
from django.db.models import QuerySet
from rse.models import *
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()


@register.simple_tag
def timetracking_installed():
  """
  This tag is designed to test if the timetracking app is installed in the current project.
  Tags at the project level are loaded in settings under TEMPLATES libraries dict (See base.py)
  The tag can not be used in a conditional statement (not sure why this is) and as such myst be imported as follows in a template
  {% load site_tags %}
  {% timetracking as timetracking_installed%} {% if timetracking %} ... {% endif %}
  """
  from django.apps import apps
  return apps.is_installed("timetracking")

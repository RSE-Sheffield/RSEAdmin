from datetime import datetime, timedelta
from typing import Dict
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.core.serializers import serialize
from django.http import JsonResponse
import json
from django.forms.models import model_to_dict

from timetracking.forms import *


def json_error_response(message:str) -> JsonResponse:
    response = JsonResponse({"Error": message})
    response.status_code = 500
    return response

@login_required
def timesheet(request: HttpRequest) -> HttpResponse:
    """
    Renders the timesheet page for a given RSE user
    """
    
    return render(request, 'timesheet.html')


@login_required
def timesheet_events(request: HttpRequest) -> HttpResponse:
    """
    Gets a JSON set of events
    """
    start_str = request.GET.get('start', None)
    end_str = request.GET.get('end', None)

    # check for start and end paramaters
    if not start_str or not end_str:
        return json_error_response("Query requires 'start' and 'end' GET parameters")

    # format date
    try:
        start = datetime.strptime(start_str, r"%Y-%m-%dT%H:%M:%SZ")
        end = datetime.strptime(end_str, r"%Y-%m-%dT%H:%M:%SZ")
    except (ValueError ):
        return json_error_response("GET parameters 'start' and 'end' must be in format '%Y-%m-%dT%H:%M:%SZ'")

    # query database
    tses = TimeSheetEntry.objects.filter(person__id=1, date__gte=start, date__lte=end)
    events = []
    for tse in tses:
        event = {}
        event['title'] = tse.project.name
        p_rgb = tse.project.colour_rbg
        event['backgroundColor'] = f"rgb({p_rgb['r']}, {p_rgb['g']}, {p_rgb['b']})"
        if tse.all_day:
            event['start'] = tse.date.strftime(r'%Y-%m-%d')
            event['allDay '] = True
        else:
            event_start = datetime.combine(tse.date, tse.start_time)
            event_end = datetime.combine(tse.date, tse.end_time)
            event['start'] = event_start.strftime(r'%Y-%m-%dT%H:%M:%S')
            event['end'] = event_end.strftime(r'%Y-%m-%dT%H:%M:%S')
        events.append(event)

    return JsonResponse(events, safe=False)

@login_required
def timesheet_projects(request: HttpRequest) -> HttpResponse:
    """
    Gets a JSON set of events
    """
    start_str = request.GET.get('start', None)
    end_str = request.GET.get('end', None)

    # check for start and end paramaters
    if not start_str or not end_str:
        return json_error_response("Query requires 'start' and 'end' GET parameters")

    # format date
    logger.error(start_str)
    try:
        start = datetime.strptime(start_str, r"%Y-%m-%d")
        end = datetime.strptime(end_str, r"%Y-%m-%d")
    except (ValueError ):
        return json_error_response("GET parameters 'start' and 'end' must be in format '%Y-%m-%dT%H:%M:%SZ'")


    # get any allocation tht fall within query period
    project_ids = RSEAllocation.objects.filter(rse__id=1, start__lt=end, end__gt=start).values_list('project_id').distinct()
    projects = Project.objects.filter(id__in=project_ids)
    # merge rgb property with selected project fields
    output = [dict(model_to_dict(p, fields=['id', 'name', 'start', 'end']), **p.colour_rbg) for p in projects]

    return JsonResponse(list(output), safe=False)

@login_required
def timesheet_add(request: HttpRequest) -> HttpResponse:
    """
    Adds a timesheet entry (e.g. as a result of drag drop)
    """

    if request.method == 'POST':
        form = TimesheetForm(request.POST)
        if form.is_valid():
            entry = form.save()
            data = serialize('json', [entry])
            return JsonResponse(data, safe=False)
        else:
            return json_error_response("Timesheet Entry has Invalid Data")
    
    return json_error_response("Unable to create new Timesheet Entry")
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

from timetracking.forms import *

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
    start = request.GET.get('start', None)
    end = request.GET.get('end', None)

    if not start or not end:
        response = JsonResponse({"Error": "Query requires 'start' and 'end' GET parameters"})
        response.status_code = 500
        return response

    # query database
    tses = TimeSheetEntry.objects.filter(person__id=1)
    events = []
    for tse in tses:
        event = {}
        event['title'] = tse.project.name
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
            response = JsonResponse({"Error": "Timesheet Entry has Invalid Data"})
            response.status_code = 403
            return response
    
    response = JsonResponse({"Error": "Unable to create new Timesheet Entry"})
    response.status_code = 500
    return response
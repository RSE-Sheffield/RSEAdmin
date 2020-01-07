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


def timesheetentry_json(timesheetentry) -> dict:
    data = {}
    data['id'] = timesheetentry.id
    data['project'] = timesheetentry.project.id
    data['rse'] = timesheetentry.rse.id
    data['date'] = timesheetentry.date.strftime(r'%Y-%m-%d')
    data['all_day'] = timesheetentry.all_day
    data['start_time'] = timesheetentry.start_time.strftime(r'%H:%M:%S')
    data['end_time'] = timesheetentry.start_time.strftime(r'%H:%M:%S')

    return data

def json_error_response(message:str) -> JsonResponse:
    response = JsonResponse({"Error": message})
    response.status_code = 400
    return response

@login_required
def timesheet(request: HttpRequest) -> HttpResponse:
    """
    Renders the timesheet page for a given RSE user
    """
    view_dict = {}

    # if admin then include rses in view dict
    if request.user.is_superuser:
        view_dict['rses'] = RSE.objects.all()
    #else get the rse id of user
    else:
        rse = get_object_or_404(RSE, user=request.user)
        view_dict['rse'] = rse
    
    return render(request, 'timesheet.html', view_dict)


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
        start = datetime.strptime(start_str, r"%Y-%m-%dT%H:%M:%S%z")
        end = datetime.strptime(end_str, r"%Y-%m-%dT%H:%M:%S%z")
    except (ValueError ):
        return json_error_response("GET parameters 'start' and 'end' must be in format '%Y-%m-%dT%H:%M:%S%z'")

    #select an RSE
    if request.user.is_superuser:
        rse_id = request.GET.get('rse_id', -1)
    #else get the rse id of user
    else:
        rse = get_object_or_404(RSE, user=request.user)
        rse_id = rse.id

    # query database
    tses = TimeSheetEntry.objects.filter(rse__id=rse_id, date__gte=start, date__lte=end)
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
        # extended properties
        extendedProps = {}
        extendedProps['db_id'] = tse.id
        extendedProps['project_id'] = tse.project.id
        extendedProps['rse_id'] = tse.rse.id
        event['extendedProps'] = extendedProps

        # append event to list
        events.append(event)


    return JsonResponse(events, safe=False)

@login_required
def timesheet_projects(request: HttpRequest) -> HttpResponse:
    """
    Gets a JSON set of projects for a given time period and RSE
    """

    start_str = request.GET.get('start', None)
    end_str = request.GET.get('end', None)

    # check for start and end paramaters
    if not start_str or not end_str:
        return json_error_response("Query requires 'start' and 'end' GET parameters")

    # format date
    try:
        start = datetime.strptime(start_str, r"%Y-%m-%d")
        end = datetime.strptime(end_str, r"%Y-%m-%d")
    except (ValueError ):
        return json_error_response("GET parameters 'start' and 'end' must be in format '%Y-%m-%dT%H:%M:%SZ'")

    # get the RSE
    if request.user.is_superuser:
        rse_id = request.GET.get('rse_id', -1)
    #else get the rse id of user
    else:
        rse = get_object_or_404(RSE, user=request.user)
        rse_id = rse.id

    # get any allocation tht fall within query period
    project_ids = RSEAllocation.objects.filter(rse__id=rse_id, start__lt=end, end__gt=start).values_list('project_id').distinct()
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
            return JsonResponse(json.dumps(timesheetentry_json(entry)), safe=False)
        else:
            # construct an error string based off validation field values
            # requires double join as each field may have multiple error strings
            error_str = ". ".join(". ".join(error) for error in form.errors.values())
            return json_error_response(error_str)
    
    return json_error_response("Unable to create new Timesheet Entry")


@login_required
def timesheet_edit(request: HttpRequest) -> HttpResponse:
    """
    Edit a timesheet entry (e.g. as a result of drag drop or resize)
    """

    if request.method == 'POST':

        # get instance
        if 'id' not in request.POST:
            return json_error_response("Timesheet Entry id not provided in POST")
        id = request.POST.get('id')
        try:
            event = TimeSheetEntry.objects.get(id=id)
        except DoesNotExist:
            return json_error_response(f"Timesheet Entry id={id} does not exist")

        form = TimesheetForm(request.POST, instance=event)
        if form.is_valid():
            entry = form.save()
            return JsonResponse(json.dumps(timesheetentry_json(entry)), safe=False)
        else:
            return json_error_response("Timesheet Entry could not be edited")
    
    return json_error_response("Unable to edit Timesheet Entry")


########################
### Reporting Views ####
########################

@login_required
def time_project(request: HttpRequest, project_id: int) -> HttpResponse:

    view_dict = {}

    # get time breakdown
    commitment_data = []
    
    #TODO: RSE selection
    rse = RSE.objects.all()[0]
    project = get_object_or_404(Project, id=project_id)

    # Time sheet entries
    tses = TimeSheetEntry.objects.filter(rse=rse, project=project).order_by('date')
    commitments = []
    total = 0
    for tse in tses:
        date = tse.date
        # accumulate time
        if tse.all_day:
            total += 1
        else:
            # convert seconds to days
            total += (datetime.combine(date.today(), tse.end_time) - datetime.combine(date.today(), tse.start_time)).seconds / (60*60*7.4)
        commitments.append([date, total])
    
    commitment_data.append((rse, commitments))
    view_dict['commitment_data'] = commitment_data



    return render(request, 'time_project.html', view_dict)
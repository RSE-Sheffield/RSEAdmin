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
from django.conf import settings
from django.views.generic.edit import DeleteView

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

def daterange(start_date, end_date, delta: str ='days'):
    """
    Generator function for iterating between two dates
    Delta can break the time period down by days weeks or months
    """

    if delta == 'day':
        days = int ((end_date - start_date).days)
        logger.error(f"days = {days}")
        for n in range(days):
            yield (start_date + timedelta(n), start_date + timedelta(n+1), 1)
    if delta == 'week':
        weeks = int ((end_date - start_date).days/7)
        logger.error(f"weeks = {weeks}")
        for n in range(weeks):
            yield (start_date + timedelta(n*7), start_date + timedelta((n+1)*7), 7)
    if delta == 'month':
        # convert to months
        ym_start= 12*start_date.year + start_date.month - 1 
        ym_end= 12*end_date.year + end_date.month - 1
        for ym in range( ym_start, ym_end ):
            # start
            y, m = divmod( ym, 12 )
            s = date(y, m+1, 1)
            if s < start_date:
                s = start_date
            # end
            y, m = divmod( ym +1, 12 )
            e = date(y, m+1, 1)
            if e > end_date:
                e = end_date
            yield (s, e, (e-s).days)




############################
### Time Tracking Pages ####
############################

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


#############################
### AJAX Responsive URLS ####
#############################

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
    filter_str = request.GET.get('filter', 'A')

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
        rse_id = request.GET.get('rse_id', '-1')
    #else get the rse id of user
    else:
        rse = get_object_or_404(RSE, user=request.user)
        rse_id = rse.id

    # Filter all active projects
    if filter_str == 'A' and rse_id != '-1':
        projects =  Project.objects.filter(start__lt=end, end__gt=start)
    # Filter projects allocated to the RSE
    else:
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


class timesheet_delete(UserPassesTestMixin, DeleteView):
    model = TimeSheetEntry
    success_message = "Timesheet entry was successfully deleted."
    
    def get(self, request, *args, **kwargs):
        """ disable this view when arriving by get (i.e. only allow post) """
        raise Http404("Page does not exist")

    def test_func(self):
        """ Only for super users or for RSEs to delete their own time sheet entries"""
        if self.request.user.is_superuser:
            return True
        else:
            # can only delete own time sheet entries
            tse = self.get_object()
            if tse.rse.user.id == self.request.user.id:
                return True
            else:
                return False

    def get_object(self, queryset=None):
        id = self.request.POST['id']
        return self.get_queryset().filter(id=id).get()
      
    def delete(self, request, *args, **kwargs):
        # No success message as this wont be displayed until the next request (and page is AJAX based)
        # messages.success(self.request, self.success_message)
        # call super which will the the actual delete
        self.get_object().delete()
        return JsonResponse(json.dumps({'delete': 'ok'}), safe=False)
        

########################
### Reporting Views ####
########################

@login_required
def time_project(request: HttpRequest, project_id: int) -> HttpResponse:

    view_dict = {}

    # get time breakdown
    commitment_data = []

    #gte the project
    project = get_object_or_404(Project, id=project_id)

    # form (is always valid as no fields are required)
    form = ProjectTimeViewOptionsForm(request.GET, project=project)
    if form.is_valid():
        granularity = form.cleaned_data['granularity']
        if form.cleaned_data['rse'] == "":
            allocations = RSEAllocation.objects.filter(project=project)
            tses = TimeSheetEntry.objects.filter(project=project)
            view_dict['rse_name'] = f"RSE Team (all RSEs)"
        else:
            rse = get_object_or_404(RSE, id=form.cleaned_data['rse'])
            allocations = RSEAllocation.objects.filter(rse=rse, project=project)
            tses = TimeSheetEntry.objects.filter(rse=rse, project=project)
            view_dict['rse_name'] = f"{rse.user.first_name} {rse.user.last_name}"
    view_dict['form'] = form
    

    # project expected days
    project_days = []
    project_days_sum = 0
    working_day = project.working_days / (project.end - project.start).days  # average fractional day for project
    # project allocated days
    allocated_days = []
    allocated_days_sum = 0
    # rse time sheet hours
    timesheet_days = []
    timesheet_days_sum = 0

    # 0 day
    project_days.append([project.start, 0])
    allocated_days.append([project.start, 0])
    timesheet_days.append([project.start, 0])

    # iterate through days on project to build dataset for graphing
    for start_date, end_date, duration in daterange(project.start, project.end, delta=granularity):

        # project expected days
        project_days_sum += working_day*duration
        project_days.append([end_date, project_days_sum])
        
        # project allocated days by allocations which are active on current
        active = allocations.filter(start__lte=start_date, end__gt=end_date)
        for a in active:
            # allocated day need to be converted into equivalent working days
            allocated_days_sum += a.working_days(start_date, end_date)
        allocated_days.append([end_date, allocated_days_sum])

        # timesheet entries
        tses_for_day = tses.filter(date__gte=start_date, date__lt=end_date)
        for tse in tses_for_day:
            date = tse.date
            # accumulate time
            if tse.all_day:
                timesheet_days_sum += 1
            else:
                timesheet_days_sum += (datetime.combine(date.today(), tse.end_time) - datetime.combine(date.today(), tse.start_time)).seconds / (60*60*settings.WORKING_HOURS_PER_DAY) # convert hours to fractional days
        timesheet_days.append([end_date, timesheet_days_sum])

    # add datasets to dict
    view_dict['allocated_days'] = allocated_days
    view_dict['project_days'] = project_days
    view_dict['timsheet_days'] = timesheet_days
    
    # settings required in view for displaying fractional days w.r.t. hours
    view_dict['WORKING_HOURS_PER_DAY'] = settings.WORKING_HOURS_PER_DAY
    view_dict['project_working_days'] = project.working_days





    return render(request, 'time_project.html', view_dict)
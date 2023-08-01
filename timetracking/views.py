from datetime import datetime, timedelta
from dateutil import parser
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
from rse.forms import *


def timesheetentry_json(timesheetentry) -> dict:
    """ Helper function to convert a TimeSheetEntry object into a json dict with nice date and time formatting """
    data = {}
    data['id'] = timesheetentry.id
    data['project'] = timesheetentry.project.id
    data['rse'] = timesheetentry.rse.id
    data['date'] = timesheetentry.date.strftime(r'%Y-%m-%d')
    data['all_day'] = timesheetentry.all_day
    data['start_time'] = timesheetentry.start_time.strftime(r'%H:%M:%S')
    data['end_time'] = timesheetentry.start_time.strftime(r'%H:%M:%S')

    return data

def json_error_response(message:str, raise_server_error: bool = True) -> JsonResponse:
    """ Helper function for generating a json response with an error code"""
    response = JsonResponse({"Error": message})
    if raise_server_error:
        response.status_code = 400
    return response

def daterange(start_date, end_date, delta: str ='days'):
    """
    Generator function for iterating between two dates
    Delta can break the time period down by days weeks or months
    """

    if delta == 'day':
        days = int ((end_date - start_date).days)
        for n in range(days):
            yield (start_date + timedelta(n), start_date + timedelta(n+1), 1)
    if delta == 'week':
        weeks = int ((end_date - start_date).days/7)
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
    Renders the timesheet page for a given RSE user.
    Further queries to the database are handled through the AJAX Responsive URLS
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
    Gets a JSON set of time sheet events for a given date time period.
    This view is used to populate th JS FulCalendar display.
    """
    

    start_str = request.GET.get('start', None)
    end_str = request.GET.get('end', None)

    # check for start and end paramaters
    if not start_str or not end_str:
        return json_error_response("Query requires 'start' and 'end' GET parameters")

    # format date
    try:
        start = parser.parse(start_str)
        end = parser.parse(end_str)
    except (ValueError ):
        return json_error_response("GET parameters 'start' and 'end' could not be parsed")

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
    Gets a JSON set of projects (funded only) for a given time period and RSE
    If the RSE id is -1 (value from template which represents whole team) then all projects are returned.
    """

    start_str = request.GET.get('start', None)
    end_str = request.GET.get('end', None)
    filter_str = request.GET.get('filter', 'A')

    # check for start and end paramaters
    if not start_str or not end_str:
        return json_error_response("Query requires 'start' and 'end' GET parameters")

    # format date
    try:
        start = parser.parse(start_str) # r"%Y-%m-%d"
        end = parser.parse(end_str) # r"%Y-%m-%d"
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
        projects =  Project.objects.filter(start__lt=end, end__gt=start, status=Project.FUNDED)
    # Filter projects allocated to the RSE
    else:
        # get any allocations that fall within query period
        project_ids = RSEAllocation.objects.filter(rse__id=rse_id, start__lt=end, end__gt=start).values_list('project_id').distinct()
        projects = Project.objects.filter(id__in=project_ids, status=Project.FUNDED)

    # merge rgb property with selected project fields
    output = [dict(model_to_dict(p, fields=['id', 'name', 'start', 'end']), **p.colour_rbg) for p in projects]

    return JsonResponse(list(output), safe=False)

@login_required
def timesheet_add(request: HttpRequest) -> HttpResponse:
    """
    Adds a timesheet entry (e.g. as a result of external drag drop in JS FulCalendar library)
    Returns a JSON response of object and raises an error code if the edit fails.
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
            return json_error_response(error_str, raise_server_error=False) # not a server side error
    
    return json_error_response("Unable to create new Timesheet Entry")


@login_required
def timesheet_edit(request: HttpRequest) -> HttpResponse:
    """
    Edit a timesheet entry (e.g. as a result of drag drop or resize in JS FulCalendar library)
    Returns a JSON response and raises an error code if the edit fails.
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
            # construct an error string based off validation field values
            # requires double join as each field may have multiple error strings
            error_str = ". ".join(". ".join(error) for error in form.errors.values())
            return json_error_response("Timesheet entry could not be edited. " + error_str, raise_server_error=False) # not a server side error
    
    return json_error_response("Unable to edit Timesheet Entry")


class timesheet_delete(UserPassesTestMixin, DeleteView):
    """
    DeletView class for deleteing TimeSheetEntry object.
    Overriding the test_func prevents users from deleteing entries which do not belong to them.
    """
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
    """
    This view presents the recorded (from time sheets), scheduled (from allocations) and project total effort committed.
    Data is generated fro the ChartJS template into three sets of plots by iterating dat regions (in days, weeks, or months)
    """
    view_dict = {}

    # get time breakdown
    commitment_data = []

    #get the project
    project = get_object_or_404(Project, id=project_id)
    rse = None
    view_dict['project'] = project

    # create the form used fro filtering by RSE or granularity of report
    if len(request.GET):
        form = ProjectTimeViewOptionsForm(request.GET, project=project)
        if form.is_valid():
            granularity = form.cleaned_data['granularity'] 
            # load data depending on RSE selection
            if form.cleaned_data['rse'] == "":
                allocations = RSEAllocation.objects.filter(project=project)
                tses = TimeSheetEntry.objects.filter(project=project)
                view_dict['rse_name'] = f"RSE Team (all RSEs)"
            else:
                rse = get_object_or_404(RSE, id=form.cleaned_data['rse'])
                allocations = RSEAllocation.objects.filter(rse=rse, project=project)
                tses = TimeSheetEntry.objects.filter(rse=rse, project=project)
                view_dict['rse_name'] = f"{rse.user.first_name} {rse.user.last_name}"
    else:
        # default granularity for unbound form (i.e. first load without form submission)
        d = project.duration
        if d < 14:
            granularity = 'day'
        elif d < 60:
            granularity = 'week'
        else:
            granularity = 'month'
        # create unbound form (this is the only way to use initial value for a choice field) and load data
        form = ProjectTimeViewOptionsForm(project=project, initial={'granularity': granularity})
        allocations = RSEAllocation.objects.filter(project=project)
        tses = TimeSheetEntry.objects.filter(project=project)
        view_dict['rse_name'] = f"RSE Team (all RSEs)"

    view_dict['form'] = form
    

    # project expected days
    project_days = []
    project_days_sum = 0
    working_day = project.working_days / (project.end - project.start).days  # average fractional day for project (varies for service projects)
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

    # iterate through days on project to build datasets for graphing
    for start_date, end_date, duration in daterange(project.start, project.end, delta=granularity):
        # project expected days
        project_days_sum += working_day*duration
        project_days.append([end_date, project_days_sum])
        
        # project allocated days by allocations which are active on current
        active = allocations.filter(start__lte=end_date, end__gt=start_date)
        for a in active:
            # allocated day need to be converted into equivalent working days
            allocated_days_sum += a.working_days(start_date, end_date)
        allocated_days.append([end_date, allocated_days_sum])

        # timesheet entries
        tses_for_day = tses.filter(date__gte=start_date, date__lt=end_date)
        timesheet_days_sum += TimeSheetEntry.working_days(tses=tses_for_day)
        timesheet_days.append([end_date, timesheet_days_sum])

    # add datasets to dict
    view_dict['allocated_days'] = allocated_days
    view_dict['project_days'] = project_days
    view_dict['timsheet_days'] = timesheet_days

    # Summary data
    view_dict['today_expected'] = project.scheduled_working_days_to_today(rse=rse)
    view_dict['today_delivered'] = TimeSheetEntry.working_days(tses=tses.filter(date__gte=project.start, date__lte=timezone.now().date()))
    view_dict['today_remaining'] = view_dict['today_expected'] - view_dict['today_delivered']
    try:
        view_dict['today_percent'] = view_dict['today_delivered']*100.0 / view_dict['today_expected']
    except ZeroDivisionError:
        view_dict['today_percent'] = 0
    view_dict['total_expected'] = project.working_days
    view_dict['total_delivered'] =  TimeSheetEntry.working_days(tses)
    view_dict['total_remaining'] = view_dict['total_expected'] - view_dict['total_delivered']
    view_dict['total_percent'] = view_dict['total_delivered'] * Decimal(100.0) / view_dict['total_expected'] # no need to catch div by 0 as total_expected can not be 0

    return render(request, 'time_project.html', view_dict)

@login_required
def time_projects(request: HttpRequest) -> HttpResponse:
    """
    View for all funded projects to provide a link for the full breakdown with graphing. 
    Project objects are amended by adding scheduled and recorded time to the object for display in the template.
    """

    # view dict
    view_dict = {}  # type: Dict[str, object]
    
    if request.method == 'GET':
        form = ProjectsFilterForm(request.GET)
    view_dict['form'] = form
       
    # funded projects only
    now = timezone.now().date()
    projects = Project.objects.filter(status=Project.FUNDED)

    #append recorded and scheduled days
    for p in projects:
        p.scheduled = p.scheduled_working_days_to_today()
        p.recorded = TimeSheetEntry.working_days(tses=TimeSheetEntry.objects.filter(project=p, date__gte=p.start, date__lte=timezone.now().date()))
        try:
            p.progress = p.recorded/p.scheduled*100
        except ZeroDivisionError:
            p.progress = 0

    view_dict['projects'] = projects
    
    return render(request, 'time_projects.html', view_dict)

from datetime import datetime
import itertools as it

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.db.models import Max, Min

from .models import *


def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')


@login_required
def projects(request: HttpRequest) -> HttpResponse:
    """
    Filters to be handled client side with DataTables
    """
    
    projects = Project.objects.all()
    
    return render(request, 'projects.html', { "projects": projects })



@login_required
def project_view(request: HttpRequest, project_id) -> HttpResponse:
    # Get the project
    proj = get_object_or_404(Project, pk=project_id)

    #TODO
    # Dict for view
    view_dict = {}

    # Get allocations for project
    allocations = RSEAllocation.objects.filter(project=proj)
    view_dict['allocations'] = allocations

    # Calculate commitments
    view_dict['project_days'] = proj.project_days()
    view_dict['committed_days'] = proj.committed_days()

    # Add proj to dict
    view_dict['project'] = proj
    
    # Project type
    view_dict['service'] = False
    if isinstance(proj, ServiceProject):
        view_dict['service'] = True

    return render(request, 'project_view.html', view_dict)


@login_required
def rse_view(request: HttpRequest, rse_username: str) -> HttpResponse:
    # Get the user
    user = get_object_or_404(User, username=rse_username)

    # Dict for view
    view_dict = {}

    # Get RSE if exists
    rse = get_object_or_404(RSE, user=user)
    view_dict['rse'] = rse

    # Query parameters for allocation query (has optional range query)
    q = Q()

    # Date range from GET
    from_date = None
    until_date = None
    if request.method == 'GET' and 'dateRange' in request.GET:
        try:
            from_date = datetime.strptime(request.GET['dateRange'].split(' - ')[0], '%d/%m/%Y').date()
            q &= Q(end__gte=from_date)
            until_date = datetime.strptime(request.GET['dateRange'].split(' - ')[1], '%d/%m/%Y').date()
            q &= Q(start__lte=until_date)
        except ValueError:
            pass

    # Get allocations for RSE
    q &= Q(rse=rse)
    allocations = RSEAllocation.objects.filter(q)
    view_dict['allocations'] = allocations

    # Clip allocations by filter date
    f_bnone = lambda f, a, b: a if b is None else f(a, b)  # lambda function returns a if b is None or f(a,b) if b is not none
    starts = [[f_bnone(max, item.start, from_date), item.percentage, item] for item in allocations]
    ends = [[f_bnone(min, item.end, until_date), -item.percentage, item] for item in allocations]

    # Create list of start and end dates and sort
    events = sorted(starts + ends, key=lambda x: x[0])
    # accumulate effort
    pdates, deltas, allocs = zip(*events)
    effort = list(it.accumulate(deltas))

    # Set date range to min and max from allocations if none was specified
    if from_date is None:
        from_date = pdates[0]
    if until_date is None:
        until_date = pdates[-1]

    # add plot events for changes in FTE
    plot_events = list(zip(pdates, effort, allocs))
    view_dict['plot_events'] = plot_events

    # Calculate commitment summary
    # TODO: August inflation
    #staff_cost = rse.staff_cost(from_date, until_date)
    #staff_recovered = sum([a.staff_cost(from_date, until_date)
    #                       for a in allocations])

    # Overview data
    view_dict['report_duration'] = (pdates[-1] - pdates[0]).days
    #view_dict['staff_cost'] = staff_cost
    #view_dict['staff_recovered'] = staff_recovered
    #view_dict['staff_recovered_percent'] = (staff_recovered / staff_cost) * 100
    #view_dict['staff_shortfall'] = staff_cost - staff_recovered

    # Date range (may be from first and last project or request GET data)
    view_dict['filter_date'] = f"{from_date:%d/%m/%Y} - {until_date:%d/%m/%Y}"

    return render(request, 'rse_view.html', view_dict)


@login_required
def team_view(request: HttpRequest) -> HttpResponse:
    # Dict for view
    view_dict = {}

    # Get min and max dates of allocations
    max_date = RSEAllocation.objects.aggregate(Max('end'))['end__max']
    min_date = RSEAllocation.objects.aggregate(Min('start'))['start__min']
    view_dict['max_date'] = max_date
    view_dict['min_date'] = min_date

    # Construct q query with date range of one exists
    q = Q()
    from_date = min_date
    until_date = max_date
    if request.method == 'GET' and 'filter_year' in request.GET:
        try:
            from_date = datetime.strptime(request.GET['filter_year'].split(' - ')[0], '%d/%m/%Y').date()
            q &= Q(end__gte=from_date)
            until_date = datetime.strptime(request.GET['filter_year'].split(' - ')[1], '%d/%m/%Y').date()
            q &= Q(start__lte=until_date)
        except ValueError:
            pass
            
    # Set the filter date range
    view_dict['filter_from'] = from_date
    view_dict['filter_until'] = until_date

    # Get RSE allocations grouped by RSE
    rses = {}
    for rse in RSE.objects.all():
        #q &= Q(rse=rse)
        rses[rse] = RSEAllocation.objects.filter(q, rse=rse)
    view_dict['rses'] = rses
    
    # Get available financial years
    view_dict['years'] = FinancialYear.objects.all()

    return render(request, 'team_view.html', view_dict)

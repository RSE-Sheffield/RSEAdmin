from datetime import datetime
import itertools as it

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import (
    Project,
    RSE,
    RSEAllocation,
    User,
    )


def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')


@login_required
def projects(request: HttpRequest) -> HttpResponse:
    
    return render(request, 'projects.html')



@login_required
def project_view(request: HttpRequest, project_id) -> HttpResponse:
    # Get the project
    proj = get_object_or_404(Project, pk=project_id)

    # Dict for view
    view_dict = {}

    # Get allocations for project
    allocations = RSEAllocation.objects.filter(project=proj)
    view_dict['allocations'] = allocations

    # Calculate commitments
    view_dict['proj_days'] = proj.duration
    view_dict['committed_days'] = sum(a.duration for a in allocations)

    # Add proj to dict
    view_dict['proj'] = proj

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
    staff_cost = rse.staff_cost(from_date, until_date)
    staff_recovered = sum([a.staff_cost(from_date, until_date)
                           for a in allocations])

    # Overview data
    view_dict['report_duration'] = (pdates[-1] - pdates[0]).days
    view_dict['staff_cost'] = staff_cost
    view_dict['staff_recovered'] = staff_recovered
    view_dict['staff_recovered_percent'] = (staff_recovered / staff_cost) * 100
    view_dict['staff_shortfall'] = staff_cost - staff_recovered

    # Date range (may be from first and last project or request GET data)
    view_dict['filter_date'] = f"{from_date:%d/%m/%Y} - {until_date:%d/%m/%Y}"

    return render(request, 'rse_view.html', view_dict)


@login_required
def team_view(request: HttpRequest) -> HttpResponse:
    # Dict for view
    view_dict = {}

    # Get RSE if exists
    rses = {}
    for rse in RSE.objects.all():
        rses[rse] = RSEAllocation.objects.filter(rse=rse)
    view_dict['rses'] = rses

    return render(request, 'team_view.html', view_dict)

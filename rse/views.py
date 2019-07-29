from datetime import datetime
import itertools as it

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.db.models import Max, Min

from .models import *
from .forms import *


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
	
    # Construct q query and check the filter range form
    q = Q()
    if request.method == 'GET':
        form = FilterDateRangeForm(request.GET)
        if form.is_valid():
            filter_range = form.cleaned_data["filter_range"]
            from_date = filter_range[0]
            q &= Q(end__gte=from_date)
            until_date = filter_range[1]
            q &= Q(start__lte=until_date)
    else:
        form = FilterDateRangeForm()
    

    # Get RSE allocations grouped by RSE based off Q filter and save the form
    q &= Q(rse=rse)
    allocations = RSEAllocation.objects.filter(q)
    view_dict['allocations'] = allocations
    view_dict['form'] = form

    # Get the commitment summary (date, effort, RSEAllocation)
    plot_events = RSEAllocation.commitment_summary(allocations, from_date, until_date)
    view_dict['plot_events'] = plot_events
	
    return render(request, 'rse_view.html', view_dict)


@login_required
def team_view(request: HttpRequest) -> HttpResponse:
    # Dict for view
    view_dict = {}

    # Construct q query and check the filter range form
    q = Q()
    if request.method == 'GET':
        form = FilterDateRangeForm(request.GET)
        if form.is_valid():
            filter_range = form.cleaned_data["filter_range"]
            from_date = filter_range[0]
            q &= Q(end__gte=from_date)
            until_date = filter_range[1]
            q &= Q(start__lte=until_date)
    else:
        form = FilterDateRangeForm()
    

    # Get RSE allocations grouped by RSE based off Q filter and save the form
    rses = {}
    for rse in RSE.objects.all():
        rses[rse] = RSEAllocation.objects.filter(q, rse=rse)
    view_dict['rses'] = rses
    view_dict['form'] = form


    return render(request, 'team_view.html', view_dict)

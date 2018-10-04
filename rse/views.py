from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, get_list_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.db.models import Max, Min
import itertools as it
from datetime import datetime
from django.db.models import Q

from .models import *

def index(request):
    return render(request, 'index.html')
    
@login_required
def project_view(request, project_id):
    # get the project
    proj = get_object_or_404(Project, pk=project_id)
    
    #dict for view
    dict = {}
    
    # get allocations for project
    allocations = RSEAllocation.objects.filter(project = proj)
    dict['allocations'] = allocations
    
    # calculate commitments
    dict['proj_days'] = proj.duration
    dict['committed_days'] = sum(a.duration for a in allocations)
    
    # add proj to dict
    dict['proj'] = proj
    
    return render(request, 'project_view.html', dict)
    
@login_required
def rse_view(request, rse_username):
    # get the user
    user = get_object_or_404(User, username=rse_username)
    
    #dict for view
    dict = {}
    
    #get RSE if exists
    rse = get_object_or_404(RSE, user=user)
    dict['rse'] = rse 
    
    # Query parameters for allocation query (has optional range query)
    q = Q()

    # Date range from GET
    from_date = None
    until_date = None
    if request.method == 'GET':
        if  'dateRange' in request.GET:
            try:
                from_date = datetime.strptime(request.GET['dateRange'].split(' - ')[0], '%d/%m/%Y').date()
                q &= Q(end__gte=from_date)
                until_date = datetime.strptime(request.GET['dateRange'].split(' - ')[1], '%d/%m/%Y').date()
                q &= Q(start__lte=until_date)
            except ValueError:
                pass
    
  

    # get allocations for rse
    q &= Q(rse=rse)
    allocations = RSEAllocation.objects.filter(q)
    dict['allocations'] = allocations
    
    # Clip allocations by filter date
    f_bnone = lambda f, a, b: a if b is None else f(a, b) #lambda function returns a if b is None or f(a,b) if b is not none
    starts = [[f_bnone(max, item.start, from_date), item.percentage] for item in allocations]
    ends = [[f_bnone(min, item.end, until_date), -item.percentage] for item in allocations]
    
    # create list of start and end dates and sort
    events = sorted(starts + ends, key=lambda x: x[0])
    # accumulate effort
    pdates, deltas = zip(*events)
    effort = list(it.accumulate(deltas))
    
    # Set date range to min and max from allocations if none was specified
    if from_date is None:
        from_date = pdates[0]
    if until_date is None:
        until_date = pdates[-1]
    
    # add plot events for changes in FTE
    plot_events = list(zip(pdates, effort))    
    dict['plot_events'] = plot_events
    
    # Calculate commitment summary 
    # TODO: August inflation
    staff_cost = rse.staffCost(from_date, until_date)
    staff_recovered = sum([a.staffCost(from_date, until_date) for a in allocations])
    
    # Overview data
    dict['report_duration'] = (pdates[-1] - pdates[0]).days
    dict['report_duration_billable'] = dict['report_duration'] * 220/360
    dict['staff_cost'] = staff_cost
    dict['staff_recovered'] = staff_recovered
    dict['staff_recovered_percent'] = (staff_recovered / staff_cost)*100
    dict['staff_shortfall'] = staff_cost - staff_recovered
    
    #date range (may be from first and last project or request GET data)
    dict['filter_date'] = from_date.strftime("%d/%m/%Y") + ' - ' + until_date.strftime("%d/%m/%Y")
        
    return render(request, 'rse_view.html', dict)
    
@login_required
def team_view(request):

    #dict for view
    dict = {}
    
    #get RSE if exists
    rses = {}
    for rse in RSE.objects.all():
        rses[rse] = RSEAllocation.objects.filter(rse=rse)
    dict['rses'] = rses
   
        
    return render(request, 'team_view.html', dict)
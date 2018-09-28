from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, get_list_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.db.models import Max, Min
import itertools as it

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

    # get allocations for rse
    allocations = RSEAllocation.objects.filter(rse = rse)
    dict['allocations'] = allocations
    
    # create list of start and end dates and sort
    starts = [[item.start, item.percentage] for item in allocations]
    ends = [[item.end, -item.percentage] for item in allocations]
    events = sorted(starts + ends, key=lambda x: x[0])
    # accumulate effort
    pdates, deltas = zip(*events)
    effort = list(it.accumulate(deltas))
    
    # add plot events for changes in FTE
    plot_events = list(zip(pdates, effort))    
    dict['plot_events'] = plot_events
    
    # Calculate commitment summary 
    #TODO: Calculation should not be able to span financial year?
    durations = [(d1 - d2).days for d1,d2 in zip(pdates[1:], pdates[:-1])]
    fte = [(duration*percentage/100) for duration,percentage in zip(durations, list(effort)[:-1])]
    # TODO: Salary should be based off grade points and change with financial year
    salary_per_day = 30000/220 # estimated
    staff_cost = (pdates[-1] - pdates[0]).days * salary_per_day
    staff_recovered = sum([fte*salary_per_day for fte in fte])
    
    # Overview data
    dict['report_duration'] = (pdates[-1] - pdates[0]).days
    dict['report_duration_billable'] = dict['report_duration'] * 220/360
    dict['salary_per_day'] = salary_per_day
    dict['staff_cost'] = staff_cost
    dict['staff_recovered'] = staff_recovered
    dict['staff_recovered_percent'] = (staff_recovered / staff_cost)*100
    dict['staff_shortfall'] = staff_cost - staff_recovered
        
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
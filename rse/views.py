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
    
    # create list of start and end dates
    starts = [[item.start, item.percentage] for item in allocations]
    ends = [[item.end, -item.percentage] for item in allocations]
    # sort date events
    events = sorted(starts + ends, key=lambda x: x[0])
    # 
    pdates, deltas = zip(*events)
    effort = it.accumulate(deltas)
    plot_events = list(zip(pdates, effort))    
    
    dict['plot_events'] = plot_events
    
    plot_events = [[e[0], (e[1])] for e in events]
   
        
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
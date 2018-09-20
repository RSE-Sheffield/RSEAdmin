from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, get_list_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.db.models import Max, Min

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
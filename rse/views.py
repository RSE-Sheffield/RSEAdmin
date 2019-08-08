from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
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

    # Dict for view
    view_dict = {}

    # Get allocations for project
    allocations = RSEAllocation.objects.filter(project=proj)
    view_dict['allocations'] = allocations


    # Add proj to dict
    view_dict['project'] = proj
    
        
    # Get unique RSE ids allocated to project and build list of (RSE, [RSEAllocation]) objects for commitment graph
    allocation_unique_rses = allocations.values('rse').distinct()
    commitment_data = []
    for a in allocation_unique_rses:
        rse_allocations = allocations.filter(rse__id=a['rse'])
        rse = RSE.objects.get(id=a['rse'])
        commitment_data.append((rse, RSEAllocation.commitment_summary(rse_allocations)))
    view_dict['commitment_data'] = commitment_data
	

    return render(request, 'project.html', view_dict)

@login_required
def project_new(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}
    
    # process or create form
    if request.method == 'POST':
        form = AllocatedProjectForm(request.POST)
        if form.is_valid():
            # Save to DB (add project as not a displayed field)
            new_proj = form.save(commit=False)
            new_proj.creator = request.user
            new_proj.created = datetime.now().date()
            new_proj.save()
            # Go to the project view
            return HttpResponseRedirect(reverse_lazy('project_view', kwargs={'project_id': new_proj.id}))
    else:
        form = AllocatedProjectForm()

    view_dict['form'] = form
    
    return render(request, 'project_new.html', view_dict)
 
@login_required
def project_edit(request: HttpRequest, project_id) -> HttpResponse:
    
    # Get the project (as generic project to ensure correct ID)
    proj = get_object_or_404(Project, pk=project_id)
    
    # Dict for view
    view_dict = {}

    if request.method == 'POST':
        form = AllocatedProjectForm(request.POST, instance=proj)
        if form.is_valid():
            # Save to DB (add project as not a displayed field)
            form.save()
            # Go to the project view
            return HttpResponseRedirect(reverse_lazy('project_view', kwargs={'project_id': project_id}))
    else:
        form = AllocatedProjectForm(instance=proj)
    view_dict['form'] = form
    
    return render(request, 'project_new.html', view_dict)
 

 
@login_required
def project_allocations(request: HttpRequest, project_id) -> HttpResponse:
    # Get the project
    proj = get_object_or_404(Project, pk=project_id)
    
    # Dict for view
    view_dict = {}
    view_dict['project'] = proj
    
    # Get allocations for project
    allocations = RSEAllocation.objects.filter(project=proj)
    view_dict['allocations'] = allocations

    # Create new allocation form (this will fill in start date and end date automatically based of any previous commitments
    if request.method == 'POST':
        form = ProjectAllocationForm(request.POST, project=proj)
        if form.is_valid():
            # Save to DB (add project as not a displayed field)
            a = form.save(commit=False)
            a.project = proj
            a.save()
    else:
        form = ProjectAllocationForm(project=proj)

    view_dict['form'] = form
    
	

    return render(request, 'project_allocations.html', view_dict)


class project_allocations_view_delete(DeleteView):
    """ POST only special delete view which redirects to project allocation view """
    model = RSEAllocation
    
    def get_success_url(self):
        return reverse_lazy('project_allocations_view', kwargs={'project_id': self.object.project.id})
    
@login_required
def commitment_view(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}

    # Construct q query and check the project filter form
    q = Q()
    from_date = None
    until_date = None
    if request.method == 'GET':
        form = FilterProjectForm(request.GET)
        if form.is_valid():
            filter_range = form.cleaned_data["filter_range"]
            from_date = filter_range[0]
            q &= Q(end__gte=from_date)
            until_date = filter_range[1]
            q &= Q(start__lte=until_date)

            # apply status type query
            status = form.cleaned_data["status"]
            if status != 'A':
                q &= Q(project__status=status)
    else:
        form = FilterProjectForm()
        
    # Get RSE allocations grouped by RSE based off Q filter and save the form
    allocations = RSEAllocation.objects.filter(q)
    view_dict['form'] = form
        
    # Get unique RSE ids allocated to project and build list of (RSE, [RSEAllocation]) objects for commitment graph
    allocation_unique_rses = allocations.values('rse').distinct()
    commitment_data = []
    for a in allocation_unique_rses:
        rse_allocations = allocations.filter(rse__id=a['rse'])
        rse = RSE.objects.get(id=a['rse'])
        commitment_data.append((rse, RSEAllocation.commitment_summary(rse_allocations, from_date, until_date)))
    view_dict['commitment_data'] = commitment_data
	

    return render(request, 'commitments.html', view_dict)


@login_required
def rseid_view(request: HttpRequest, rse_id: int) -> HttpResponse:
    rse = get_object_or_404(RSE, id=rse_id)
    
    return rse_view(request, rse.user.username)

@login_required
def rse_view(request: HttpRequest, rse_username: str) -> HttpResponse:
    # Get the user
    user = get_object_or_404(User, username=rse_username)

    # Dict for view
    view_dict = {}

    # Get RSE if exists
    rse = get_object_or_404(RSE, user=user)
    view_dict['rse'] = rse
	
    # Construct q query and check the project filter form
    q = Q()
    from_date = None
    until_date = None
    if request.method == 'GET':
        form = FilterProjectForm(request.GET)
        if form.is_valid():
            filter_range = form.cleaned_data["filter_range"]
            from_date = filter_range[0]
            q &= Q(end__gte=from_date)
            until_date = filter_range[1]
            q &= Q(start__lte=until_date)

            # apply status type query
            status = form.cleaned_data["status"]
            if status != 'A':
                q &= Q(project__status=status)
    else:
        form = FilterProjectForm()
    

    # Get RSE allocations grouped by RSE based off Q filter and save the form
    q &= Q(rse=rse)
    allocations = RSEAllocation.objects.filter(q)
    view_dict['allocations'] = allocations
    view_dict['form'] = form

    # Get the commitment summary (date, effort, RSEAllocation)
    if allocations:
        view_dict['commitment_data'] = [(rse, RSEAllocation.commitment_summary(allocations, from_date, until_date))]
	
    return render(request, 'rse.html', view_dict)


@login_required
def team_view(request: HttpRequest) -> HttpResponse:
    # Dict for view
    view_dict = {}

    # Construct q query and check the project filter form
    q = Q()
    if request.method == 'GET':
        form = FilterProjectForm(request.GET)
        if form.is_valid():
            filter_range = form.cleaned_data["filter_range"]
            from_date = filter_range[0]
            q &= Q(end__gte=from_date)
            until_date = filter_range[1]
            q &= Q(start__lte=until_date)

            # apply status type query
            status = form.cleaned_data["status"]
            if status != 'A':
                q &= Q(project__status=status)
    else:
        form = FilterProjectForm()
    

    # Get RSE allocations grouped by RSE based off Q filter and save the form
    rses = {}
    for rse in RSE.objects.all():
        rses[rse] = RSEAllocation.objects.filter(q, rse=rse)
    view_dict['rses'] = rses
    view_dict['form'] = form


    return render(request, 'team.html', view_dict)

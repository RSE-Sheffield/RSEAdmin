from datetime import datetime
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import get_object_or_404, render
from django.db.models import Max, Min, ProtectedError

from .models import *
from .forms import *


def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')


################################
### Projects and Allocations ###
################################

@login_required
def projects(request: HttpRequest) -> HttpResponse:
    """
    Filters to be handled client side with DataTables
    """
    
    projects = Project.objects.all()
    
    return render(request, 'projects.html', { "projects": projects })



@login_required
def project(request: HttpRequest, project_id) -> HttpResponse:
    # Get the project
    proj = get_object_or_404(Project, pk=project_id)

    # Dict for view
    view_dict = {}
    view_dict['project'] = proj
        
    # Get allocations for project
    allocations = RSEAllocation.objects.filter(project=proj)
    view_dict['allocations'] = allocations
        
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
        form = ProjectTypeForm(request.POST)
        if form.is_valid():
            type = form.cleaned_data['type']
            if type == 'A':
                return project_new_allocated(request)
            else:
                return project_new_service(request)
    else:
        form = ProjectTypeForm()

    view_dict['form'] = form
    
    return render(request, 'project_new.html', view_dict)


@login_required
def project_new_allocated(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}
    
    # process or create form
    if request.method == 'POST' and 'project_submit' in request.POST:
        form = AllocatedProjectForm(request.POST)
        if form.is_valid():
            # Save to DB (add project as not a displayed field)
            new_proj = form.save()
            # If there is a url to go to next then go there otherwise go to project view
            next = request.GET.get('next', None)
            if next:
                return HttpResponseRedirect(next)
            else:
                return HttpResponseRedirect(reverse_lazy('project', kwargs={'project_id': new_proj.id}))
    else:
        form = AllocatedProjectForm()
        # If request has a client id then automatically set this in the initial form data
        client_id = request.GET.get('client', None)
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                form.initial['client'] = client
            except:
                pass
        form.initial['creator'] = request.user
        form.initial['created'] = timezone.now().date()

    view_dict['form'] = form
    
    return render(request, 'project_allocated_new.html', view_dict)

@login_required
def project_new_service(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}
    
    # process or create form
    if request.method == 'POST' and 'project_submit' in request.POST:
        form = ServiceProjectForm(request.POST)
        if form.is_valid():
            # Save to DB (add project as not a displayed field)
            new_proj = form.save()
            # If there is a url to go to next then go there otherwise go to project view
            next = request.GET.get('next', None)
            if next:
                return HttpResponseRedirect(next)
            else:
                return HttpResponseRedirect(reverse_lazy('project', kwargs={'project_id': new_proj.id}))
    else:
        form = ServiceProjectForm()
        # If request has a client id then automatically set this in the initial form data
        client_id = request.GET.get('client', None)
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                form.initial['client'] = client
            except:
                pass
        form.initial['creator'] = request.user
        form.initial['created'] = timezone.now().date()

    view_dict['form'] = form
    
    return render(request, 'project_service_new.html', view_dict)

@login_required
def project_allocated_new(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}
    
    # process or create form
    if request.method == 'POST':
        form = AllocatedProjectForm(request.POST)
        if form.is_valid():
            # Save to DB (add project as not a displayed field)
            new_proj = form.save()
            # If there is a url to go to next then go there otherwise go to project view
            next = request.GET.get('next', None)
            if next:
                return HttpResponseRedirect(next)
            else:
                return HttpResponseRedirect(reverse_lazy('project', kwargs={'project_id': new_proj.id}))
    else:
        form = AllocatedProjectForm()
        # If request has a client id then automatically set this in the initial form data
        client_id = request.GET.get('client', None)
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                form.initial['client'] = client
            except:
                pass
        form.initial['creator'] = request.user
        form.initial['created'] = timezone.now().date()

    view_dict['form'] = form
    
    return render(request, 'project_new.html', view_dict)
 
@login_required
def project_edit(request: HttpRequest, project_id) -> HttpResponse:
    
    # Get the project (as generic project to ensure correct ID)
    proj = get_object_or_404(Project, pk=project_id)
    
    # Dict for view
    view_dict = {}
    
    # depending on project type change the form and template
    if isinstance(proj, AllocatedProject):
        formclass = AllocatedProjectForm
        template = 'project_allocated_new.html'
    else :
        formclass = ServiceProjectForm
        template = 'project_service_new.html'

    if request.method == 'POST':
        form = formclass(request.POST, instance=proj)
        if form.is_valid():
            # Save to DB (add project as not a displayed field)
            form.save()
            # Go to the project view
            return HttpResponseRedirect(reverse_lazy('project', kwargs={'project_id': project_id}))
    else:
        form = formclass(instance=proj)
    view_dict['form'] = form
    
    # Add edit field to indicate delete should be available
    view_dict['edit'] = True
    
    return render(request, template, view_dict)
 

 
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


class project_allocations_delete(DeleteView):
    """ POST only special delete view which redirects to project allocation view """
    model = RSEAllocation
    
    def get(self, request, *args, **kwargs):
        """ disable this view when arriving by get (i.e. only allow post) """
        raise Http404("Page does not exist")
    
    def get_success_url(self):
        return reverse_lazy('project_allocations', kwargs={'project_id': self.object.project.id})
    
class project_delete(DeleteView):
    """ POST only special delete view which redirects to project allocation view """
    model = Project
    
    def get(self, request, *args, **kwargs):
        """ disable this view when arriving by get (i.e. only allow post) """
        raise Http404("Page does not exist")
    
    def get_success_url(self):
        return reverse_lazy('projects')
    

###############
### Clients ###
###############

    
@login_required
def clients(request: HttpRequest) -> HttpResponse:
    """
    Filters to be handled client side with DataTables
    """
    
    clients = Client.objects.all()
    
    return render(request, 'clients.html', { "clients": clients })

    
@login_required
def client(request: HttpRequest, client_id) -> HttpResponse:
    # Get the project
    client = get_object_or_404(Client, pk=client_id)

    # Dict for view
    view_dict = {}
    view_dict['client'] = client

    # Get allocations for project
    projects = Project.objects.filter(client=client)
    view_dict['projects'] = projects

    return render(request, 'client.html', view_dict)

@login_required
def client_new(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}
    
    # process or create form
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            # Save to DB (add project as not a displayed field)
            new_client = form.save()
            # Go to the clients view or to next location
            next = request.GET.get('next', None)
            if next:
                return HttpResponseRedirect(f"{next}?client={new_client.id}")
            else:
                return HttpResponseRedirect(reverse_lazy('client', kwargs={'client_id': new_client.id}))
    else:
        form = ClientForm()

    view_dict['form'] = form
    
    return render(request, 'client_new.html', view_dict)
 
@login_required
def client_edit(request: HttpRequest, client_id) -> HttpResponse:
    
    # Get the project (as generic project to ensure correct ID)
    client = get_object_or_404(Client, pk=client_id)
    
    # Dict for view
    view_dict = {}

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            # Save to DB (add project as not a displayed field)
            form.save()
            # Go to the project view
            return HttpResponseRedirect(reverse_lazy('project', kwargs={'client_id': client_id}))
    else:
        form = ClientForm(instance=client)
    view_dict['form'] = form
    
    # Add edit field to indicate delete should be available
    view_dict['edit'] = True
    
    return render(request, 'client_new.html', view_dict)
 
class client_delete(DeleteView):
    """ POST only special delete view which redirects to clients list view """
    model = Client
    
    def get(self, request, *args, **kwargs):
        """ disable this view when arriving by get (i.e. only allow post) """
        raise Http404("Page does not exist")
    
    def get_success_url(self):
        return reverse_lazy('clients')
        
    #def post(self, request, *args, **kwargs):
    #    """  Custom error handling for forbidden delete (due to on_delete.PROTECTED) when client has active projects """
    #    try:
    #        return self.delete(request, *args, **kwargs)
    #    except ProtectedError:
    #        return HttpResponseServerError("Unable to delete client with existing projects")
            
       
########################
   

@login_required
def rse(request: HttpRequest, rse_username: str) -> HttpResponse:
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
    
    # RSE in dictinary with allocations
    rses = {}
    rses[rse] = allocations
    view_dict['rses'] = rses

    # Get the commitment summary (date, effort, RSEAllocation)
    if allocations:
        view_dict['commitment_data'] = [(rse, RSEAllocation.commitment_summary(allocations, from_date, until_date))]
	
    return render(request, 'rse.html', view_dict)

@login_required
def rseid(request: HttpRequest, rse_id: int) -> HttpResponse:
    r = get_object_or_404(RSE, id=rse_id)
    
    return rse(request, r.user.username)

@login_required
def rses(request: HttpRequest) -> HttpResponse:
    """
    Filters to be handled client side with DataTables
    """
    
    rses = RSE.objects.all()
    
    return render(request, 'rses.html', { "rses": rses })


@login_required
def team(request: HttpRequest) -> HttpResponse:
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

@login_required
def commitment(request: HttpRequest) -> HttpResponse:

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


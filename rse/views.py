from datetime import datetime
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import get_object_or_404, render
from django.db.models import Max, Min, ProtectedError
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth.forms import AdminPasswordChangeForm

from .models import *
from .forms import *



@login_required
def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')


@user_passes_test(lambda u: u.is_superuser)
def user_new(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}
    
    # process or create form
    if request.method == 'POST':
        form = UserTypeForm(request.POST)
        if form.is_valid():
            type = form.cleaned_data['user_type']
            if type == 'R':
                return HttpResponseRedirect(reverse_lazy('user_new_rse'))
            else:
                return HttpResponseRedirect(reverse_lazy('user_new_admin'))
                 
    else:
        # default option is administrator view
        form = UserTypeForm()
    view_dict['form'] = form

    return render(request, 'user_new.html', view_dict)
    
    
@user_passes_test(lambda u: u.is_superuser)
def user_new_rse(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}
    
    # process or create form
    if request.method == 'POST':        
        user_form = NewUserForm(request.POST) 
        rse_form = NewRSEUserForm(request.POST) 
        # process admin user
        if user_form.is_valid() and rse_form.is_valid(): 
            user = user_form.save()
            rse = rse_form.save(commit=False)
            rse.user = user
            rse.save()
            messages.add_message(request, messages.SUCCESS, f'New RSE user {user.username} created.')
            return HttpResponseRedirect(reverse_lazy('index'))
                
    else:
        user_form = NewUserForm()
        rse_form = NewRSEUserForm() 
        
    view_dict['user_form'] = user_form
    view_dict['rse_form'] = rse_form

    return render(request, 'user_new_rse.html', view_dict)

@user_passes_test(lambda u: u.is_superuser)
def user_edit_rse(request: HttpRequest, rse_id) -> HttpResponse:

    # Get the RSE
    rse = get_object_or_404(RSE, pk=rse_id)

    # Dict for view
    view_dict = {}
    
    # process or create form
    if request.method == 'POST':        
        user_form = EditUserForm(request.POST, instance=rse.user) 
        rse_form = NewRSEUserForm(request.POST, instance=rse) 
        # process admin user
        if user_form.is_valid() and rse_form.is_valid(): 
            user = user_form.save()
            rse = rse_form.save(commit=False)
            rse.user = user
            rse.save()
            messages.add_message(request, messages.SUCCESS, f'RSE user {user.username} detais updated.')
            return HttpResponseRedirect(reverse_lazy('index'))
                
    else:
        user_form = EditUserForm(instance=rse.user)
        rse_form = NewRSEUserForm(instance=rse) 
        
    view_dict['user_form'] = user_form
    view_dict['rse_form'] = rse_form
    view_dict['edit'] = True

    return render(request, 'user_new_rse.html', view_dict)
  
    
@user_passes_test(lambda u: u.is_superuser)
def user_new_admin(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}
    
    # process or create form
    if request.method == 'POST':        
        user_form = NewUserForm(request.POST) 
        # process admin user
        if user_form.is_valid(): 
            user = user_form.save()
            messages.add_message(request, messages.SUCCESS, f'New admin user {user.username} created.')
            return HttpResponseRedirect(reverse_lazy('index'))
                
    else:
        user_form = NewUserForm()
        
    view_dict['user_form'] = user_form

    return render(request, 'user_new_admin.html', view_dict)

@user_passes_test(lambda u: u.is_superuser)
def user_edit_admin(request: HttpRequest, user_id) -> HttpResponse:

    # Get the User
    user = get_object_or_404(User, pk=user_id)
    
    # Redirect if user is an RSE rather than admin user
    try:
        rse = RSE.objects.get(user=user)
        return HttpResponseRedirect(reverse_lazy('user_edit_rse', kwargs={'rse_id': rse.id}))
    except RSE.DoesNotExist:
        pass


    # Dict for view
    view_dict = {}
    
    # process or create form
    if request.method == 'POST':        
        user_form = EditUserForm(request.POST, instance=user) 
        # process admin user
        if user_form.is_valid(): 
            user = user_form.save()
            messages.add_message(request, messages.SUCCESS, f'Admin user {user.username} details updated.')
            return HttpResponseRedirect(reverse_lazy('index'))
                
    else:
        user_form = EditUserForm(instance=user)
        
    view_dict['user_form'] = user_form
    view_dict['edit'] = True

    return render(request, 'user_new_admin.html', view_dict)

@user_passes_test(lambda u: u.is_superuser)
def user_change_password(request: HttpRequest, user_id) -> HttpResponse:
    # Get the User
    user = get_object_or_404(User, pk=user_id)
    
    # Dict for view
    view_dict = {}
    
    # process or create form
    if request.method == 'POST':        
        password_form = AdminPasswordChangeForm(user, request.POST) 
        # process admin user
        if password_form.is_valid(): 
            user = password_form.save()
            messages.add_message(request, messages.SUCCESS, f'User {user.username} password updated.')
            return HttpResponseRedirect(reverse_lazy('index'))
                
    else:
        password_form = AdminPasswordChangeForm(user)
        
    # modify the css and label attributes
    password_form.fields['password1'].widget.attrs['class'] = 'form-control'
    password_form.fields['password1'].label = "New Password:"
    password_form.fields['password2'].widget.attrs['class'] = 'form-control'
    password_form.fields['password2'].label = "New Password (again):"
        
    view_dict['form'] = password_form
    view_dict['user'] = user

    return render(request, 'user_change_password.html', view_dict)

def users(request: HttpRequest) -> HttpResponse:
    users = User.objects.all()
    
    return render(request, 'users.html', { "users": users })

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
            messages.add_message(request, messages.SUCCESS, f'New project {new_proj.name} created.')
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
            messages.add_message(request, messages.SUCCESS, f'New project {new_proj.name} created.')
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
            project = form.save()
            messages.add_message(request, messages.SUCCESS, f'Project {project.name} details successfully updated.')
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

    # Create new allocation form (this will fill in start date and end date automatically based of any previous commitments)
    # Only for super users
    if request.user.is_superuser:
        if request.method == 'POST':
            form = ProjectAllocationForm(request.POST, project=proj)
            if form.is_valid():
                # Save to DB (add project as not a displayed field)
                a = form.save(commit=False)
                a.project = proj
                a.save()
                messages.add_message(request, messages.SUCCESS, f'Allocation created.')
        else:
            form = ProjectAllocationForm(project=proj)

        view_dict['form'] = form
    
	

    return render(request, 'project_allocations.html', view_dict)


class project_allocations_delete(UserPassesTestMixin, DeleteView):
    """ POST only special delete view which redirects to project allocation view """
    model = RSEAllocation
    success_message = "Project allocation deleted successfully."
    
    def test_func(self):
        """ Only for super users """
        return self.request.user.is_superuser
        
    def get(self, request, *args, **kwargs):
        """ disable this view when arriving by get (i.e. only allow post) """
        raise Http404("Page does not exist")
    
    def get_success_url(self):
        return reverse_lazy('project_allocations', kwargs={'project_id': self.object.project.id})
        
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(project_allocations_delete, self).delete(request, *args, **kwargs)
    
class project_delete(UserPassesTestMixin, DeleteView):
    """ POST only special delete view which redirects to project allocation view """
    model = Project
    success_message = "Project deleted successfully."
    
    def test_func(self):
        """ Only for super users """
        return self.request.user.is_superuser
        
    def get(self, request, *args, **kwargs):
        """ disable this view when arriving by get (i.e. only allow post) """
        raise Http404("Page does not exist")
    
    def get_success_url(self):
        return reverse_lazy('projects')
        
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(project_delete, self).delete(request, *args, **kwargs)
    

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
            client = form.save()
            messages.add_message(request, messages.SUCCESS, f'Client {client.name} details successfully updated.')
            # Go to the project view
            return HttpResponseRedirect(reverse_lazy('project', kwargs={'client_id': client_id}))
    else:
        form = ClientForm(instance=client)
    view_dict['form'] = form
    
    # Add edit field to indicate delete should be available
    view_dict['edit'] = True
    
    return render(request, 'client_new.html', view_dict)
 
class client_delete(UserPassesTestMixin, DeleteView):
    """ POST only special delete view which redirects to clients list view """
    model = Client
    success_message = "Client deleted successfully."
    
    def test_func(self):
        """ Only for super users """
        return self.request.user.is_superuser
     
     
    def get(self, request, *args, **kwargs):
        """ disable this view when arriving by get (i.e. only allow post) """
        raise Http404("Page does not exist")
    
    def get_success_url(self):
        return reverse_lazy('clients')
        
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(client_delete, self).delete(request, *args, **kwargs)
        
       
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


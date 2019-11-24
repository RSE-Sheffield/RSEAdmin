from datetime import datetime, timedelta
from typing import Dict

from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import get_object_or_404, render
from django.db.models import Max, Min, ProtectedError 
from django.db import IntegrityError
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.http import JsonResponse
from django.conf import settings


from .models import *
from .forms import *

#################
### Homepage ####
#################


@user_passes_test(lambda u: u.is_superuser)
def index_admin(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    now = timezone.now().date()
    soon = now + timedelta(days=settings.HOME_PAGE_DAYS_SOON)
    view_dict['now'] = now

    # HIGHTLIGHT: team capacity
    rses = RSE.objects.filter(employed_from__lte=now, employed_until__gt=now)
    try:
        average_capacity = sum(rse.current_capacity for rse in rses) / rses.count()
    except ZeroDivisionError:
        average_capacity = 0

    view_dict['rses'] = rses
    view_dict['average_capacity'] = average_capacity

    # RSE capacity
    rses_capacity_low = [rse for rse in rses if rse.current_capacity < settings.HOME_PAGE_RSE_MIN_CAPACITY_WARNING_LEVEL]
    view_dict['rses_capacity_low'] = rses_capacity_low

    # settings
    view_dict['HOME_PAGE_RSE_MIN_CAPACITY_WARNING_LEVEL'] = settings.HOME_PAGE_RSE_MIN_CAPACITY_WARNING_LEVEL
    view_dict['HOME_PAGE_DAYS_SOON'] = settings.HOME_PAGE_DAYS_SOON
    

    # HIGHTLIGHT: active projects
    active_funded_projects = Project.objects.filter(start__lte=now, end__gt=now, status=Project.FUNDED).count()
    view_dict['active_funded_projects'] = active_funded_projects

    # HIGHTLIGHT: projects under review
    review_projects = Project.objects.filter(status=Project.REVIEW).count()
    view_dict['review_projects'] = review_projects

    # HIGHTLIGHT: Service projects with outstanding invoices
    outstanding_invoices = ServiceProject.objects.filter(internal=False, invoice_received=None).count()
    view_dict['outstanding_invoices'] = outstanding_invoices

    # Latest projects added 
    lastest_projects = Project.objects.all().order_by('-created')[0:settings.HOME_PAGE_NUMBER_ITEMS]
    view_dict['lastest_projects'] = lastest_projects

    # Projects starting 
    starting_projects = Project.objects.filter(start__gt=now).order_by('start')[0:settings.HOME_PAGE_NUMBER_ITEMS]
    view_dict['starting_projects'] = starting_projects

    # WARNINGS
    warning_starting_not_funded =  Project.objects.filter(Q(status=Project.PREPARATION) | Q(status=Project.REVIEW)).filter(start__gt=now, start__lte=soon).count()
    view_dict['warning_starting_not_funded'] = warning_starting_not_funded
    warning_service_started_not_invoiced =  ServiceProject.objects.filter(internal=False, start__lte=now, end__gt=now, invoice_received=None).count()
    view_dict['warning_service_started_not_invoiced'] = warning_service_started_not_invoiced

    # DANGERS
    danger_started_not_funded =  Project.objects.filter(Q(status=Project.PREPARATION) | Q(status=Project.REVIEW)).filter(start__lte=now, end__gte=now).count()
    view_dict['danger_started_not_funded'] = danger_started_not_funded
    danger_service_ended_not_invoiced =  ServiceProject.objects.filter(internal=False, end__lt=now, invoice_received=None).count()
    view_dict['danger_service_ended_not_invoiced'] = danger_service_ended_not_invoiced

    return render(request, 'index_admin.html', view_dict)


@login_required
def index_rse(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    # get the RSE
    rse = get_object_or_404(RSE, user=request.user)
    view_dict['rse'] = rse

    now = timezone.now().date()
    soon = now + timedelta(days=settings.HOME_PAGE_DAYS_SOON)
    view_dict['now'] = now

    # HIGHLIGHT: Current Capacity
    highlight_current_capacity = rse.current_capacity
    view_dict['highlight_current_capacity'] = highlight_current_capacity
    view_dict['available_capacity'] = 100.0-highlight_current_capacity

    # HIGHLIGHT: Active allocations
    highlight_active_allocations = RSEAllocation.objects.filter(rse=rse, start__lte=now, end__gte=now, project__status=Project.FUNDED).count()
    view_dict['highlight_active_allocations'] = highlight_active_allocations

    # HIGHLIGHT: funded and possible projects (anything not rejected that has not completed)
    highlight_possible_allocations = RSEAllocation.objects.filter(rse=rse, end__gte=now).filter(Q(project__status=Project.REVIEW)|Q(project__status=Project.PREPARATION)|Q(project__status=Project.FUNDED)).count()
    view_dict['highlight_possible_allocations'] = highlight_possible_allocations

    # HIGHTLIGHT: active projects
    highlight_active_funded_projects = Project.objects.filter(start__lte=now, end__gt=now, status=Project.FUNDED).count()
    view_dict['highlight_active_funded_projects'] = highlight_active_funded_projects

    # active allocation progress
    active_allocations = RSEAllocation.objects.filter(rse=rse, start__lte=now, end__gte=now, project__status=Project.FUNDED)
    view_dict['active_allocations'] = active_allocations

    # first X non active projects due
    future_allocations = RSEAllocation.objects.filter(rse=rse, start__gte=now).filter(Q(project__status=Project.REVIEW)|Q(project__status=Project.PREPARATION)|Q(project__status=Project.FUNDED)).order_by('start')[0:settings.HOME_PAGE_NUMBER_ITEMS]
    view_dict['future_allocations'] = future_allocations

    # settings
    view_dict['HOME_PAGE_RSE_MIN_CAPACITY_WARNING_LEVEL'] = settings.HOME_PAGE_RSE_MIN_CAPACITY_WARNING_LEVEL
    view_dict['HOME_PAGE_DAYS_SOON'] = settings.HOME_PAGE_DAYS_SOON
    view_dict['MAX_END_DATE_FILTER_RANGE'] = Project.max_end_date()
    view_dict['MIN_START_DATE_FILTER_RANGE'] = Project.min_start_date()
    

    return render(request, 'index_rse.html', view_dict)



@login_required
def index(request: HttpRequest) -> HttpResponse:

    # catch admin users
    if request.user.is_superuser:
        return index_admin(request)
    else:
        return index_rse(request)




#########################
### Helper Functions ####
#########################

def append_project_and_allocation_costs(request: HttpRequest, project: Project, allocations: TypedQuerySet[RSEAllocation]):
    
    # calculate project budget and effort
    total_value = project.value()

    # service project
    if project.is_service:
        staff_budget = total_value
    # allocated project
    else:
        staff_budget = project.staff_budget()

    # calculate staff costs and overheads
    total_staff_cost = 0
    for a in allocations:
        # staff cost
        try:
            salary_value = a.staff_cost()
        except ValueError:
            salary_value = SalaryValue()
            messages.add_message(request, messages.ERROR, f'ERROR: RSE user {a.rse} does not have salary data for allocation on project {a.project} starting at {a.project.start} so will incur no cost.')
        a.staff_cost = salary_value.staff_cost
        a.project_budget_percentage = a.staff_cost / staff_budget * 100.0
        total_staff_cost += a.staff_cost


    # Set project fields
    # service project
    if project.is_service:
        project.total_value = total_value
        project.staff_cost = total_staff_cost
        project.percent_total_budget = project.staff_cost / total_value * 100.0
        project.remaining_surplus = total_value - total_staff_cost
    # allocated project
    else:   
        project.total_value = total_value
        project.staff_budget = staff_budget
        project.overhead = project.overhead_value()
        project.staff_cost = total_staff_cost
        project.percent_staff_budget = project.staff_cost / staff_budget * 100.0
        project.remaining_staff_budget = staff_budget - total_staff_cost
        




#######################
### Authentication ####
#######################

@user_passes_test(lambda u: u.is_superuser)
def user_new(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}  # type: Dict[str, object]
    
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
    view_dict = {}  # type: Dict[str, object]
    
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
            # create a salary grade change for RSE
            if rse_form.cleaned_data["salary_band"]:
                sgc = SalaryGradeChange(rse=rse, salary_band=rse_form.cleaned_data["salary_band"])
                sgc.save()
            messages.add_message(request, messages.SUCCESS, f'New RSE user {user.username} created.')
            # Go to view of RSE salary grade changes
            return HttpResponseRedirect(reverse_lazy('rse_salary', kwargs={'rse_username': user.username}))
                
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
    view_dict = {}  # type: Dict[str, object]
    
    # process or create form
    if request.method == 'POST':        
        user_form = EditUserForm(request.POST, instance=rse.user) 
        rse_form = EditRSEUserForm(request.POST, instance=rse) 
        # process admin user
        if user_form.is_valid() and rse_form.is_valid(): 
            user = user_form.save()
            rse = rse_form.save(commit=False)
            rse.user = user
            rse.save()
            messages.add_message(request, messages.SUCCESS, f'RSE user {user.username} details updated.')
            return HttpResponseRedirect(reverse_lazy('index'))
                
    else:
        user_form = EditUserForm(instance=rse.user)
        rse_form = EditRSEUserForm(instance=rse) 
        
    view_dict['user_form'] = user_form
    view_dict['rse_form'] = rse_form
    view_dict['edit'] = True

    return render(request, 'user_new_rse.html', view_dict)
  
    
@user_passes_test(lambda u: u.is_superuser)
def user_new_admin(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}  # type: Dict[str, object]
    
    # process or create form
    if request.method == 'POST':        
        user_form = NewUserForm(request.POST, force_admin=True) 
        # process admin user
        if user_form.is_valid(): 
            user = user_form.save()
            messages.add_message(request, messages.SUCCESS, f'New admin user {user.username} created.')
            return HttpResponseRedirect(reverse_lazy('index'))
                
    else:
        user_form = NewUserForm(force_admin=True)
        
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
    view_dict = {}  # type: Dict[str, object]
    
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
    view_dict = {}  # type: Dict[str, object]
    
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

@user_passes_test(lambda u: u.is_superuser)
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

    # view dict
    view_dict = {}  # type: Dict[str, object]
    
    if request.method == 'GET':
        form = ProjectsFilterForm(request.GET)
    view_dict['form'] = form
       
    projects = Project.objects.all()
    view_dict['projects'] = projects
    
    return render(request, 'projects.html', view_dict)



@login_required
def project(request: HttpRequest, project_id) -> HttpResponse:
    # Get the project
    proj = get_object_or_404(Project, pk=project_id)

    # Dict for view
    view_dict = {}  # type: Dict[str, object]
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

    # append salary and costs information for template
    append_project_and_allocation_costs(request, proj, allocations)

	

    return render(request, 'project.html', view_dict)


@login_required
def project_new(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}  # type: Dict[str, object]
    
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
    view_dict = {}  # type: Dict[str, object]
    
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
    view_dict = {}  # type: Dict[str, object]
    
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
    view_dict = {}  # type: Dict[str, object]
    
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
 

 
@user_passes_test(lambda u: u.is_superuser)
def project_allocations_edit(request: HttpRequest, project_id) -> HttpResponse:
    # Get the project
    proj = get_object_or_404(Project, pk=project_id)
    
    # Dict for view
    view_dict = {}  # type: Dict[str, object]
    view_dict['project'] = proj
    
    # Create new allocation form for effort
    if request.method == 'POST':
        form = ProjectAllocationForm(request.POST, project=proj)
        if form.is_valid():
            # Save to DB (add project as not a displayed field)
            a = form.save(commit=False)
            a.project = proj
            a.save()
            messages.add_message(request, messages.SUCCESS, f'New allocation created.')
            # reset the form
            form = ProjectAllocationForm(project=proj)
    else:
        form = ProjectAllocationForm(project=proj)
    
    # Get allocations for project
    allocations = RSEAllocation.objects.filter(project=proj)
    view_dict['allocations'] = allocations
    
    # append salary and costs information for template
    append_project_and_allocation_costs(request, proj, allocations)

    view_dict['form'] = form

    return render(request, 'project_allocations_edit.html', view_dict)

@user_passes_test(lambda u: u.is_superuser)
def project_allocations(request: HttpRequest, project_id) -> HttpResponse:
    # Get the project
    proj = get_object_or_404(Project, pk=project_id)
    
    # Dict for view
    view_dict = {}  # type: Dict[str, object]
    view_dict['project'] = proj
    
    # Get allocations for project
    allocations = RSEAllocation.objects.filter(project=proj)
    view_dict['allocations'] = allocations

    # append salary and costs information for template
    append_project_and_allocation_costs(request, proj, allocations)


    return render(request, 'project_allocations.html', view_dict)


class project_allocations_delete(UserPassesTestMixin, DeleteView):
    """ POST only special delete view which redirects to project allocation view """
    model = RSEAllocation
    success_message = "Project allocation marked as deleted."
    
    def test_func(self):
        """ Only for super users """
        return self.request.user.is_superuser
        
    def get(self, request, *args, **kwargs):
        """ disable this view when arriving by get (i.e. only allow post) """
        raise Http404("Page does not exist")
    
    def get_success_url(self):
        return reverse_lazy('project_allocations_edit', kwargs={'project_id': self.object.project.id})
        
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        self.object = self.get_object()
        success_url = self.get_success_url()
        # do not actually delete but flag as deleted
        self.object.deleted_date = timezone.now()
        self.object.save()
        return HttpResponseRedirect(success_url)
    
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
    view_dict = {}  # type: Dict[str, object]
    view_dict['client'] = client

    # Get allocations for project
    projects = Project.objects.filter(client=client)
    view_dict['projects'] = projects

    return render(request, 'client.html', view_dict)

@login_required
def client_new(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}  # type: Dict[str, object]
    
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
    view_dict = {}  # type: Dict[str, object]

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            # Save to DB (add project as not a displayed field)
            client = form.save()
            messages.add_message(request, messages.SUCCESS, f'Client {client.name} details successfully updated.')
            # Go to the project view
            return HttpResponseRedirect(reverse_lazy('client', kwargs={'client_id': client_id}))
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
    view_dict = {}  # type: Dict[str, object]

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
            if status in 'PRFX':
                q &= Q(project__status=status)
            elif status == 'L':
                q &= Q(project__status='F')|Q(project__status='R')
            elif status == 'U':
                q &= Q(project__status='F')|Q(project__status='R')|Q(project__status='P')
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

    # calculate grade point (only displayed for superusers)
    for rse in rses:
        try:
            rse.grade = rse.futureSalaryBand(date=timezone.now().date()).short_str
        except:
            rse.grade = "No Data"
    
    return render(request, 'rses.html', { "rses": rses })

def ajax_salary_band_by_year(request):
    """ 
    Simple responsive AJAX query to return options (for html options drop down) displaying salary bands per year.
    Not required to be post logged in (publically available information)
    """
    year = request.GET.get('year')
    sbs = SalaryBand.objects.filter(year=year).order_by('year')
    return render(request, 'includes/salaryband_options.html', {'sbs': sbs})

@user_passes_test(lambda u: u.is_superuser)
def rse_salary(request: HttpRequest, rse_username: str) -> HttpResponse:
    
     # Get the user
    user = get_object_or_404(User, username=rse_username)

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    # Get RSE if exists
    rse = get_object_or_404(RSE, user=user)
    view_dict['rse'] = rse

    # get salary grade changes
    sgcs = SalaryGradeChange.objects.filter(rse=rse)
    view_dict['sgcs'] = sgcs

    # salary grade change form
    if request.method == 'POST':
        form = SalaryGradeChangeForm(request.POST, rse=rse)
        if form.is_valid():
            sgc = form.save()
            messages.add_message(request, messages.SUCCESS, f'Salary Grade Change {sgc} successfully added.')
    else:
        form = SalaryGradeChangeForm(rse=rse)
    view_dict['form'] = form
    
    return render(request, 'rse_salary.html', view_dict)


class rse_salarygradechange_delete(UserPassesTestMixin, DeleteView):
    """ POST only special delete view which redirects to project allocation view """
    model = SalaryGradeChange
    success_message = "Salary grade change deleted successfully."

    def test_func(self):
        """ Only for super users """
        return self.request.user.is_superuser
        
    def get(self, request, *args, **kwargs):
        """ disable this view when arriving by get (i.e. only allow post) """
        raise Http404("Page does not exist")

    def get_success_url(self):
        return reverse_lazy('rse_salary', kwargs={'rse_username': self.get_object().rse.user.username})
        
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(rse_salarygradechange_delete, self).delete(request, *args, **kwargs)
    

@login_required
def commitment(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

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
            if status in 'PRFX':
                q &= Q(project__status=status)
            elif status == 'L':
                q &= Q(project__status='F')|Q(project__status='R')
            elif status == 'U':
                q &= Q(project__status='F')|Q(project__status='R')|Q(project__status='P')
    else:
        form = FilterProjectForm()
        
    # Get RSE allocations grouped by RSE based off Q filter and save the form
    allocations = RSEAllocation.objects.filter(q)
    view_dict['form'] = form
        
    # Get unique RSE ids allocated to project and build list of (RSE, [RSEAllocation]) objects for commitment graph
    allocation_unique_rses = allocations.values('rse').distinct()
    commitment_data = []
    rse_allocations = {}
    for a in allocation_unique_rses:
        r_a = allocations.filter(rse__id=a['rse'])
        rse = RSE.objects.get(id=a['rse'])
        rse_allocations[rse] = r_a
        commitment_data.append((rse, RSEAllocation.commitment_summary(r_a, from_date, until_date)))
    view_dict['commitment_data'] = commitment_data
    view_dict['rse_allocations'] = rse_allocations
	

    return render(request, 'commitments.html', view_dict)

#################################
### Salary and Grade Changes ####
#################################

@user_passes_test(lambda u: u.is_superuser)
def financialyears(request: HttpRequest) -> HttpResponse:
    
    # Dict for view
    view_dict = {}  # type: Dict[str, object]
    
    # Get all financial years
    years = FinancialYear.objects.all()
    if not years:
        return HttpResponseServerError("No financial years in database")
    view_dict['years'] = years
    
    # Calculate the default year. i.e. the current current financial year
    now = timezone.now()
    if now.month > 7:
        default_year = now.year
    else:
        default_year = now.year-1
        
    # Set year from get or use current financial year
    y = request.GET.get('year', default_year)
    try:
        year = FinancialYear.objects.get(year=y)
    except FinancialYear.DoesNotExist:
        messages.add_message(request, messages.ERROR, f'The {y} financial year does not exist in the database.')
        year = years[0]
    view_dict['year'] = year
    

    
    # Get all salary bands for the financial year
    salary_bands = SalaryBand.objects.filter(year=year).order_by('-grade', '-grade_point')
    view_dict['salary_bands'] = salary_bands
 
    return render(request, 'financialyears.html', view_dict)


@user_passes_test(lambda u: u.is_superuser)
def financialyear_edit(request: HttpRequest, year_id: int) -> HttpResponse:
    
    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    # Set year from get or use current financial year
    year = get_object_or_404(FinancialYear, pk=year_id)
    view_dict['year'] = year

        # Form handling for new salary bands
    if request.method == 'POST':
        sb_form = NewSalaryBandForm(request.POST, year=year)
        if sb_form.is_valid():
            sb_form.save()
    else:
        sb_form = NewSalaryBandForm(year=year)
    view_dict['sb_form'] = sb_form
        
    # Get all salary bands for the financial year
    salary_bands = SalaryBand.objects.filter(year=year).order_by('-grade', '-grade_point')
    view_dict['salary_bands'] = salary_bands
 
    return render(request, 'financialyear_edit.html', view_dict)

@user_passes_test(lambda u: u.is_superuser)
def financialyear_new(request: HttpRequest) -> HttpResponse:
    
    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    if request.method == 'POST':
        form = NewFinancialYearForm(request.POST)
        if form.is_valid():
            year = form.save()
            return HttpResponseRedirect(reverse_lazy('financialyear_edit', kwargs={'year_id': year}))
    else:
        form = NewFinancialYearForm()
    view_dict['form'] = form
 
    return render(request, 'financialyear_new.html', view_dict)

class financialyear_delete(UserPassesTestMixin, DeleteView):
    """ POST only special delete view which redirects to project allocation view """
    model = FinancialYear
    success_message = "Financial year deleted successfully."
    protected_message = "Financial year cannot be deleted as it has salary grade points."
    
    def test_func(self):
        """ Only for super users """
        return self.request.user.is_superuser
        
    def get(self, request, *args, **kwargs):
        """ disable this view when arriving by get (i.e. only allow post) """
        raise Http404("Page does not exist")

    def post(self, request, *args, **kwargs):
        """ Use the post function to handle protected error (i.e. the financial year is used by an allocated project or salary grade change) """
        try:
            return self.delete(request, *args, **kwargs)
        except (ProtectedError, IntegrityError) as error :
            # delete any success messages
            system_messages = messages.get_messages(request)
            for message in system_messages:
                # This iteration is necessary
                pass
            system_messages.used = True
            # set a new error message
            messages.error(self.request, self.protected_message)
            # return to edit view of 
            return HttpResponseRedirect(reverse_lazy('financialyear_edit', kwargs={'year_id': self.get_object()}))
    
    def get_success_url(self):
        return reverse_lazy('financialyears')
        
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(financialyear_delete, self).delete(request, *args, **kwargs)
    

@user_passes_test(lambda u: u.is_superuser)
def salaryband_edit(request: HttpRequest, sb_id: int) -> HttpResponse:

    salary_band = get_object_or_404(SalaryBand, id=sb_id)

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    if request.method == 'POST':
        sb_form = NewSalaryBandForm(request.POST, instance=salary_band)
        if sb_form.is_valid():
            sb_form.save()
            # If there is a url to go to next then go there otherwise go to project view
            next = request.GET.get('next', None)
            if next:
                return HttpResponseRedirect(next)
            else:
                return HttpResponseRedirect(reverse_lazy('financialyear'))
    else:
        sb_form = NewSalaryBandForm(instance=salary_band)

    view_dict["form"] = sb_form

    return render(request, 'salaryband_edit.html', view_dict)
 
class financialyear_salaryband_delete(UserPassesTestMixin, DeleteView):
    """ POST only special delete view which redirects to project allocation view """
    model = SalaryBand
    success_message = "Salary Band deleted successfully."
    protected_message = "Salary Band cannot be deleted as it is used by exitsing projects or salary grade changes."
    
    def test_func(self):
        """ Only for super users """
        return self.request.user.is_superuser
        
    def get(self, request, *args, **kwargs):
        """ disable this view when arriving by get (i.e. only allow post) """
        raise Http404("Page does not exist")

    def post(self, request, *args, **kwargs):
        """ Use the post function to handle protected error (i.e. the salary band is used by an allocated prject or salary grade change) """
        try:
            return self.delete(request, *args, **kwargs)
        except (ProtectedError, IntegrityError) as error :
            # delete any success messages
            system_messages = messages.get_messages(request)
            for message in system_messages:
                # This iteration is necessary
                pass
            system_messages.used = True
            # set a new error message
            messages.error(self.request, self.protected_message)
            return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        if self.next:
            return self.next
        else:
            return reverse_lazy('financialyears')
        
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        self.next = request.GET.get('next', None)
        return super(financialyear_salaryband_delete, self).delete(request, *args, **kwargs)
    

##################
### Reporting ####
##################

@user_passes_test(lambda u: u.is_superuser)
def allocations_recent(request: HttpRequest) -> HttpResponse:
    view_dict = {} 

    # create filter form
    recent = timezone.now() - timedelta(days=settings.HOME_PAGE_DAYS_RECENT)
    if request.method == 'GET':
        if 'from_date' in request.GET:
            form = FilterDateForm(request.GET)
        else:
            # create unbound form if no request data
            form = FilterDateForm()
        if form.is_valid():
            recent = form.cleaned_data['from_date']
    view_dict['form'] = form
            
    # get recent allocations
    q = Q(created_date__gte=recent) | Q(deleted_date__gte=recent)
    allocations = RSEAllocation.objects.all(deleted=True).filter(q)
    view_dict['allocations'] = allocations

    return render(request, 'allocations_recent.html', view_dict)


@user_passes_test(lambda u: u.is_superuser)
def costdistributions(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    # Construct q query for allocation query
    q = Q()
    # filter to exclude internal projects (these dont have a cost distrubution)
    # filter to only include chargable service projects (or allocated projects)
    # additional query on allocatedproject_internal is required to include any elibable allocated projects (is_instance can be used on member)
    q &= Q(project__internal=False)
    q &= Q(project__serviceproject__charged=True) | Q(project__allocatedproject__internal=False)
    # filter by funded only projects
    q &= Q(project__status='F')

    # filter to include allocations active today
    from_date = timezone.now().date()
    until_date = from_date + timedelta(days=1)
    q &= Q(end__gte=from_date)
    q &= Q(start__lte=until_date)

    # save date range
    view_dict['from_date'] = from_date
    view_dict['until_date'] = until_date
           
    # Get RSE allocations grouped by RSE based off Q filter and save the form
    allocations = RSEAllocation.objects.filter(q)

    # Get Unique projects from allocations
    allocation_unique_project_ids = allocations.values('project').distinct()
    allocation_unique_projects = Project.objects.filter(id__in=allocation_unique_project_ids)
    view_dict['projects'] = allocation_unique_projects
        
    # Gett the allocations per active RSE
    rse_allocations = {}
    for rse in RSE.objects.all() :
        if rse.current_employment:
            r_a = allocations.filter(rse=rse)
            rse_allocations[rse] = r_a
    view_dict['rse_allocations'] = rse_allocations
	
    return render(request, 'costdistributions.html', view_dict)

@user_passes_test(lambda u: u.is_superuser)
def costdistribution(request: HttpRequest, rse_username: str) -> HttpResponse:

    user = get_object_or_404(User, username=rse_username)

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    # Get RSE if exists
    rse = get_object_or_404(RSE, user=user)
    view_dict['rse'] = rse

    # Construct q query and check the project filter form
    q = Q()
    q &= Q(rse=rse)
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
            if status in 'PRFX':
                q &= Q(project__status=status)
            elif status == 'L':
                q &= Q(project__status='F')|Q(project__status='R')
            elif status == 'U':
                q &= Q(project__status='F')|Q(project__status='R')|Q(project__status='P')

    # filter to exclude internal projects (these dont have a cost distribution)
    # filter to only include chargable service projects (or allocated projects)
    # additional query on allocatedproject_internal is required to include any eligible allocated projects (is_instance can be used on member)
    q &= Q(project__internal=False)
    q &= Q(project__serviceproject__charged=True) | Q(project__allocatedproject__internal=False)
        
    # Get RSE allocations grouped by RSE based off Q filter and save the form
    allocations = RSEAllocation.objects.filter(q)
    view_dict['form'] = form

    # Get Unique projects from allocations
    allocation_unique_project_ids = allocations.values('project').distinct()
    allocation_unique_projects = Project.objects.filter(id__in=allocation_unique_project_ids)
    view_dict['projects'] = allocation_unique_projects
        
    # Get a commitment summary for the RSE
    commitments = RSEAllocation.commitment_summary(allocations, from_date, until_date)
    view_dict['commitments'] = commitments # (tuple of date, total FTE effort, [allocations])

    return render(request, 'costdistribution.html', view_dict)


@user_passes_test(lambda u: u.is_superuser)
def rses_staffcosts(request: HttpRequest) -> HttpResponse:
    """
    View reports on staff costs
    """

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    # Construct q query and check the project filter form
    q = Q()
    from_date = Project.min_start_date()
    until_date = Project.max_end_date()
    if request.method == 'GET':
        form = FilterProjectForm(request.GET)
        if form.is_valid():
            filter_range = form.cleaned_data["filter_range"]
            from_date = filter_range[0]
            q &= Q(end__gte=from_date)
            until_date = filter_range[1]
            q &= Q(start__lt=until_date)

            # apply status type query
            status = form.cleaned_data["status"]
            if status in 'PRFX':
                q &= Q(project__status=status)
            elif status == 'L':
                q &= Q(project__status='F')|Q(project__status='R')
            elif status == 'U':
                q &= Q(project__status='F')|Q(project__status='R')|Q(project__status='P')

    # save the form
    view_dict['form'] = form

    rses_costs = {}
    total_staff_salary = total_recovered_staff_cost = total_internal_project_staff_cost = total_non_recovered_cost = total_staff_liability = 0
    for rse in (rse for rse in RSE.objects.all() if rse.current_employment):
        # get any allocations for rse
        allocations = RSEAllocation.objects.filter(rse=rse).filter(q)
        try:
            staff_salary = rse.staff_cost(from_date=from_date, until_date=until_date).staff_cost
        except ValueError:
            # no salary data fro date range so warn and calculate from first available point
            try:
                first_sgc = rse.firstSalaryGradeChange().salary_band.year.start_date()
                staff_salary = rse.staff_cost(from_date=first_sgc, until_date=until_date).staff_cost
                messages.add_message(request, messages.WARNING, f'WARNING: RSE user {rse} does not have salary data until {first_sgc} and will incur no cost until this point.')
            except ValueError:
                staff_salary = 0
                messages.add_message(request, messages.ERROR, f'ERROR: RSE user {rse} does not have any salary information and will incur no cost.')
        recovered_staff_cost = 0
        internal_project_staff_cost = 0
        for a in allocations:
            # staff cost
            try:
                value = a.staff_cost(start=from_date, end=until_date).staff_cost
            except ValueError:
                value = 0
                messages.add_message(request, messages.ERROR, f'ERROR: RSE user {a.rse} does not have salary data for allocation on project {a.project} starting at {from_date} so will incur no cost.')
            # sum staff cost from allocation
            if (a.project.internal):    # internal
                internal_project_staff_cost += value
            elif isinstance(a.project, AllocatedProject) or (isinstance(a.project, ServiceProject) and a.project.charged == True): # allocated or chargable service
                recovered_staff_cost += value
        non_recovered_cost =  staff_salary - recovered_staff_cost
        staff_liability =  staff_salary - recovered_staff_cost - internal_project_staff_cost
        rses_costs[rse] = {'staff_salary': staff_salary, 'recovered_staff_cost': recovered_staff_cost, 'internal_project_staff_cost': internal_project_staff_cost, 'non_recovered_cost': non_recovered_cost, 'staff_liability': staff_liability}
        # sum totals
        total_staff_salary += staff_salary
        total_recovered_staff_cost += recovered_staff_cost
        total_internal_project_staff_cost += internal_project_staff_cost
        total_non_recovered_cost += non_recovered_cost
        total_staff_liability += staff_liability

    view_dict['rse_costs'] = rses_costs

    view_dict['total_staff_salary'] = total_staff_salary
    view_dict['total_recovered_staff_cost'] = total_recovered_staff_cost
    view_dict['total_internal_project_staff_cost'] = total_internal_project_staff_cost
    view_dict['total_non_recovered_cost'] = total_non_recovered_cost
    view_dict['total_staff_liability'] = total_staff_liability
    
    return render(request, 'rses_staffcosts.html', view_dict)


@user_passes_test(lambda u: u.is_superuser)
def rse_staffcost(request: HttpRequest, rse_username) -> HttpResponse:
    """
    View reports on a single rse staff cost (all projects and allocations)
    """
    # Get the user
    user = get_object_or_404(User, username=rse_username)

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    # Get RSE if exists
    rse = get_object_or_404(RSE, user=user)
    view_dict['rse'] = rse

    # Construct q query and check the project filter form
    q = Q()
    from_date = Project.min_start_date()
    until_date = Project.max_end_date()
    if request.method == 'GET':
        form = FilterProjectForm(request.GET)
        if form.is_valid():
            filter_range = form.cleaned_data["filter_range"]
            from_date = filter_range[0]
            q &= Q(end__gte=from_date)
            until_date = filter_range[1]
            q &= Q(start__lt=until_date)

            # apply status type query
            status = form.cleaned_data["status"]
            if status in 'PRFX':
                q &= Q(status=status)
            elif status == 'L':
                q &= Q(status='F')|Q(status='R')
            elif status == 'U':
                q &= Q(status='F')|Q(status='R')|Q(status='P')

    # save the form
    view_dict['form'] = form

    # Get only non internal, allocated or charged service projects
    q &= Q(instance_of=AllocatedProject) | Q(Q(instance_of=ServiceProject) & Q(serviceproject__charged=True))
    projects = Project.objects.filter(q)

    # actual staff salary costs
    try:
        staff_salary = rse.staff_cost(from_date=from_date, until_date=until_date).staff_cost
    except ValueError:
        # no salary data fro date range so warn and calculate from first available point
            try:
                first_sgc = rse.firstSalaryGradeChange().salary_band.year.start_date()
                staff_salary = rse.staff_cost(from_date=first_sgc, until_date=until_date).staff_cost
                messages.add_message(request, messages.WARNING, f'WARNING: RSE user {rse} does not have salary data until {first_sgc} and will incur no cost until this point.')
            except ValueError:
                staff_salary = 0
                messages.add_message(request, messages.ERROR, f'ERROR: RSE user {rse} does not have any salary information and will incur no cost.')
    project_costs = {}
    recovered_staff_cost = 0
    internal_project_staff_cost = 0
    # group costs by project
    for p in projects:
        # Get all staff costs for the project and rse
        try:
            staff_cost = p.staff_cost(from_date=from_date, until_date=until_date, rse=rse, consider_internal=True)
        except ValueError:
            staff_cost = SalaryValue()
            messages.add_message(request, messages.ERROR, f'ERROR: Project {p} has allocations with missing salary data for {rse} in the time period starting at {from_date}.')
        # only include projects with staff effort
        if staff_cost.staff_cost > 0:
            if (p.internal):    # internal or recovered staff costs
                internal_project_staff_cost += staff_cost.staff_cost
            else:
                recovered_staff_cost += staff_cost.staff_cost
            project_costs[p] = staff_cost

    view_dict['project_costs'] = project_costs
    view_dict['total_staff_salary'] = staff_salary
    view_dict['total_recovered_staff_cost'] = recovered_staff_cost
    view_dict['total_internal_project_staff_cost'] = internal_project_staff_cost
    view_dict['total_non_recovered_cost'] = staff_salary - recovered_staff_cost - internal_project_staff_cost
    view_dict['total_staff_liability'] = staff_salary - recovered_staff_cost
    
    return render(request, 'rse_staffcost.html', view_dict)


@user_passes_test(lambda u: u.is_superuser)
def serviceoutstanding(request: HttpRequest) -> HttpResponse:
    """
    View for any outstanding service projects (invoice not received)
    """

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    if request.method == 'GET':
        form = ServiceOutstandingFilterForm(request.GET)
    view_dict['form'] = form
       

    # Get Service projects in date range
    projects = ServiceProject.objects.filter(internal=False)
    view_dict['projects'] = projects


    return render(request, 'serviceoutstanding.html', view_dict)

@user_passes_test(lambda u: u.is_superuser)
def serviceincome(request: HttpRequest) -> HttpResponse:
    """
    View reports on service income and staff expenditure.
    Internal projects are not considered.
    """

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    # Construct q query and check the project filter form
    q = Q()
    from_date = Project.min_start_date()
    until_date = Project.max_end_date()
    if request.method == 'GET':
        form = FilterProjectForm(request.GET)
        if form.is_valid():
            filter_range = form.cleaned_data["filter_range"]
            from_date = filter_range[0]
            q &= Q(end__gte=from_date)
            until_date = filter_range[1]
            q &= Q(start__lt=until_date)

            # apply status type query
            status = form.cleaned_data["status"]
            if status in 'PRFX':
                q &= Q(status=status)
            elif status == 'L':
                q &= Q(status='F')|Q(status='R')
            elif status == 'U':
                q &= Q(status='F')|Q(status='R')|Q(status='P')

    # save the form
    view_dict['form'] = form

    # only non internal service projects
    q &= Q(internal=False)
    projects = ServiceProject.objects.filter(q)

    # Get costs associated with each project
    project_costs = {}
    total_value = 0
    total_staff_cost = 0
    total_surplus = 0
    for p in projects:
        # project has a value if invoice received in accounting period
        value = 0 
        if p.invoice_received and p.invoice_received > from_date and p.invoice_received <= until_date:  # test if the invoice received was within specified period
            value = p.value()
        # project has a staff cost if it has been charged
        staff_cost = 0
        if p.charged == True:
            try:
                p_costs = p.staff_cost(from_date=from_date, until_date=until_date)
            except ValueError:
                staff_cost = SalaryValue()
                messages.add_message(request, messages.ERROR, f'ERROR: Project {p} has allocations with missing RSE salary data in the time period starting at {from_date}.')
            staff_cost = p_costs.staff_cost
        # surplus is the balance in the accounting period
        surplus = value - staff_cost
        # add project and project costs to dictionary and calculate sums
        project_costs[p] = {'value': value, 'staff_cost': staff_cost, 'surplus': surplus}
        total_value += value
        total_staff_cost += staff_cost
        total_surplus +=  surplus
    # Add project data and sums to view dict
    view_dict['project_costs'] = project_costs
    view_dict['total_value'] = total_value
    view_dict['total_staff_cost'] = total_staff_cost
    view_dict['total_surplus'] = total_surplus
	

    return render(request, 'serviceincome.html', view_dict)



@user_passes_test(lambda u: u.is_superuser)
def projects_income_summary(request: HttpRequest) -> HttpResponse:
    """
    View reports on allocated project income and staff expenditure.
    Internal projects are not considered.
    """

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    # Construct q query and check the project filter form
    q = Q()
    from_date = Project.min_start_date()
    until_date = Project.max_end_date()
    if request.method == 'GET':
        form = FilterProjectForm(request.GET)
        if form.is_valid():
            filter_range = form.cleaned_data["filter_range"]
            from_date = filter_range[0]
            q &= Q(end__gte=from_date)
            until_date = filter_range[1]
            q &= Q(start__lt=until_date)

            # apply status type query
            status = form.cleaned_data["status"]
            if status in 'PRFX':
                q &= Q(status=status)
            elif status == 'L':
                q &= Q(status='F')|Q(status='R')
            elif status == 'U':
                q &= Q(status='F')|Q(status='R')|Q(status='P')

    # save the form
    view_dict['form'] = form

    # only non internal allocated projects or charged service projects
    q &= Q(internal=False)
    q &= Q(instance_of=AllocatedProject) | Q(Q(instance_of=ServiceProject) & Q(serviceproject__charged=True))
    projects = Project.objects.filter(q)

    # Get costs associated with each allocated project
    project_costs = {}
    total_staff_cost = 0
    total_overhead = 0
    for p in projects:
        try:
            p_costs = p.staff_cost(from_date=from_date, until_date=until_date)
        except ValueError:
            p_costs = SalaryValue()
            messages.add_message(request, messages.ERROR, f'ERROR: Project {p} has allocations with missing RSE salary data in the time period starting at {from_date}.')
        staff_cost = p_costs.staff_cost
        overhead = p.overhead_value(from_date=from_date, until_date=until_date)
        # add project and project costs to dictionary and calculate sums
        project_costs[p] = {'staff_cost': staff_cost, 'overhead': overhead}
        total_staff_cost += staff_cost
        total_overhead +=  overhead

    # Add project data and sums to view dict
    view_dict['project_costs'] = project_costs
    view_dict['total_staff_cost'] = total_staff_cost
    view_dict['total_overhead'] = total_overhead
	
    return render(request, 'projects_income_summary.html', view_dict)


@user_passes_test(lambda u: u.is_superuser)
def project_staffcosts(request: HttpRequest, project_id: int) -> HttpResponse:
    """
    View reports on breakdown of staff costs between a particular period
    """

    # Get the project
    project = get_object_or_404(Project, pk=project_id)
    
    # Dict for view
    view_dict = {}  # type: Dict[str, object]
    view_dict['project'] = project

    # Get the date range from the filter form
    from_date = Project.min_start_date()
    until_date = Project.max_end_date()
    if request.method == 'GET':
        form = FilterDateRangeForm(request.GET)
        if form.is_valid():
            filter_range = form.cleaned_data["filter_range"]
            from_date = filter_range[0]
            until_date = filter_range[1]

    # save the form
    view_dict['form'] = form

    # Get the project costs
    try:
        costs = project.staff_cost(from_date=from_date, until_date=until_date, consider_internal=True)
    except ValueError:
        costs = SalaryValue()
        messages.add_message(request, messages.ERROR, f'ERROR: Project {project} has allocations with missing RSE salary data in the time period starting at {from_date}.')
    view_dict['costs'] = costs
	
    return render(request, 'project_staffcosts.html', view_dict)


@user_passes_test(lambda u: u.is_superuser)
def project_remaining_days(request: HttpRequest, project_id: int, rse_id: int, start: str, percent: int) -> HttpResponse:
    """
    Responsive query to get the number of remaining days on an allocated project.
    Required to autocomplete days when creating a new RSE allocation by budget on an allocated project
    """

    # get the RSE and project
    try:
        rse = RSE.objects.get(id=rse_id)
        project = AllocatedProject.objects.get(id=project_id)
    except ObjectDoesNotExist:
        JsonResponse({'days': 0})

    # get start date as a date
    start_date = datetime.strptime(start, '%d-%m-%Y').date()

    # get remaining staff budget for project
    allocations = RSEAllocation.objects.filter(project=project)
    # sum staff time contributions so far from existing allocations
    staff_cost = 0
    for a in allocations:
        try:
            staff_cost += a.staff_cost().staff_cost
        except ValueError:
            staff_cost = 0
            messages.add_message(request, messages.ERROR, f'ERROR: RSE user {a.rse} does not have salary data for allocation on project {a.project} starting at {from_date} so will incur no cost.')
    remaining_budget = project.staff_budget() - staff_cost

    # get the remaining FTE days for rse given remaining budget
    try:
        # get the last salary grade change before the start date of the project
        last_sgc = rse.lastSalaryGradeChange(date=start_date)
        # get the salary band of the rse at the start date
        sb = last_sgc.salary_band_at_future_date(start_date)
        # project salary to find remaining days
        days = sb.days_from_budget(start_date, float(remaining_budget), float(percent))
    except ValueError:
        return JsonResponse({'days': 0})

    return JsonResponse({'days': days})

@user_passes_test(lambda u: u.is_superuser)
def projects_internal_summary(request: HttpRequest) -> HttpResponse:
    """
    View reports on allocated project income and staff expenditure.
    Internal projects are not considered.
    """

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    # Construct q query and check the project filter form
    q = Q()
    from_date = Project.min_start_date()
    until_date = Project.max_end_date()
    if request.method == 'GET':
        form = FilterProjectForm(request.GET)
        if form.is_valid():
            filter_range = form.cleaned_data["filter_range"]
            from_date = filter_range[0]
            q &= Q(end__gte=from_date)
            until_date = filter_range[1]
            q &= Q(start__lt=until_date)

            # apply status type query
            status = form.cleaned_data["status"]
            if status in 'PRFX':
                q &= Q(status=status)
            elif status == 'L':
                q &= Q(status='F')|Q(status='R')
            elif status == 'U':
                q &= Q(status='F')|Q(status='R')|Q(status='P')

    # save the form
    view_dict['form'] = form

    # only internal projects
    q &= Q(internal=True)
    projects = Project.objects.filter(q)

    # Get costs associated with each internal project
    project_costs = {}
    total_staff_cost = 0
    for p in projects:
        try:
            p_costs = p.staff_cost(from_date=from_date, until_date=until_date, consider_internal=True)
        except ValueError:
            p_costs = SalaryValue()
            messages.add_message(request, messages.ERROR, f'ERROR: Project {p} has allocations with missing RSE salary data in the time period starting at {from_date}.')
        staff_cost = p_costs.staff_cost
        # add project and project costs to dictionary and calculate sums
        project_costs[p] = {'staff_cost': staff_cost}
        total_staff_cost += staff_cost

    # Add project data and sums to view dict
    view_dict['project_costs'] = project_costs
    view_dict['total_staff_cost'] = total_staff_cost
	
    return render(request, 'projects_internal_summary.html', view_dict)

@user_passes_test(lambda u: u.is_superuser)
def financial_summary(request: HttpRequest) -> HttpResponse:
    """
    Profit loss summary of the group as a whole
    """

    # Dict for view
    view_dict = {}  # type: Dict[str, object]

    # Construct q query and check the project filter form
    q = Q()
    from_date = Project.min_start_date()
    until_date = Project.max_end_date()
    if request.method == 'GET':
        form = FilterProjectForm(request.GET)
        if form.is_valid():
            filter_range = form.cleaned_data["filter_range"]
            from_date = filter_range[0]
            q &= Q(end__gte=from_date)
            until_date = filter_range[1]
            q &= Q(start__lt=until_date)

            # apply status type query
            status = form.cleaned_data["status"]
            if status in 'PRFX':
                q &= Q(status=status)
            elif status == 'L':
                q &= Q(status='F')|Q(status='R')
            elif status == 'U':
                q &= Q(status='F')|Q(status='R')|Q(status='P')

    # save the form
    view_dict['form'] = form

    # all projects
    projects = Project.objects.filter(q)

    salary_costs = 0
    recovered_staff_costs = 0
    internal_project_staff_costs = 0
    overheads = 0
    service_income = 0
    
    # Salary Costs (all RSEs)
    for rse in (rse for rse in RSE.objects.all() if rse.current_employment): # for all currently employed RSEs
        try:
            salary_costs += rse.staff_cost(from_date=from_date, until_date=until_date).staff_cost
        except ValueError:
            # no salary data fro date range so warn and calculate from first available point
            try:
                first_sgc = rse.firstSalaryGradeChange().salary_band.year.start_date()
                salary_costs += rse.staff_cost(from_date=first_sgc, until_date=until_date).staff_cost
                messages.add_message(request, messages.WARNING, f'WARNING: RSE user {rse} does not have salary data until {first_sgc} and will incur no cost until this point.')
            except ValueError:
                messages.add_message(request, messages.ERROR, f'ERROR: RSE user {rse} does not have any salary information and will incur no cost.')


    # Project Costs and Service Income (all project in date range)
    for p in projects:
        project_recovered_costs = 0
        # Internal Project Costs
        if (p.internal):
            try:
                internal_project_staff_costs += p.staff_cost(from_date=from_date, until_date=until_date, consider_internal=True).staff_cost
            except ValueError:
                messages.add_message(request, messages.ERROR, f'ERROR: Project {p} has allocations with missing RSE salary data in the time period starting at {from_date}.')
        # Recovered Staff Costs (allocated or charged service projects)
        elif isinstance(p, AllocatedProject) or (isinstance(p, ServiceProject) and p.charged == True):  
            try:
                project_recovered_costs = p.staff_cost(from_date=from_date, until_date=until_date).staff_cost
            except ValueError:
                project_recovered_costs = 0
                messages.add_message(request, messages.ERROR, f'ERROR: Project {p} has allocations with missing RSE salary data in the time period starting at {from_date}.')
            recovered_staff_costs += project_recovered_costs
            # accumulate overheads
            overheads += p.overhead_value(from_date=from_date, until_date=until_date)
        # Service income
        if isinstance(p, ServiceProject) and p.invoice_received and p.invoice_received > from_date and p.invoice_received <= until_date:  # test if the invoice received was within specified period
            # income from service project less any recovered staff cost
            service_income += float(p.value() - project_recovered_costs)
    
    # Liability
    non_recovered_cost = salary_costs - recovered_staff_costs
    income_total = internal_project_staff_costs + service_income + overheads

    view_dict['salary_costs'] = salary_costs
    view_dict['recovered_staff_costs'] = recovered_staff_costs
    view_dict['non_recovered_cost'] = non_recovered_cost
    view_dict['internal_project_staff_costs'] = internal_project_staff_costs
    view_dict['service_income'] = service_income
    view_dict['overheads'] = overheads
    view_dict['income_total'] = income_total
    view_dict['balance'] = income_total - non_recovered_cost

    return render(request, 'financial_summary.html', view_dict)

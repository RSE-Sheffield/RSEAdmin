from datetime import datetime, timedelta
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


from .models import *
from .forms import *


#########################
### Helper Functions ####
#########################

def append_project_and_allocation_costs(project: Project, allocations: TypedQuerySet[RSEAllocation]):
    
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
        salary_value = a.staff_cost()
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
    view_dict = {}
    
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

    # append salary and costs information for template
    append_project_and_allocation_costs(proj, allocations)
	

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
 

 
@user_passes_test(lambda u: u.is_superuser)
def project_allocations_edit(request: HttpRequest, project_id) -> HttpResponse:
    # Get the project
    proj = get_object_or_404(Project, pk=project_id)
    
    # Dict for view
    view_dict = {}
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
    append_project_and_allocation_costs(proj, allocations)

    view_dict['form'] = form

    return render(request, 'project_allocations_edit.html', view_dict)

@user_passes_test(lambda u: u.is_superuser)
def project_allocations(request: HttpRequest, project_id) -> HttpResponse:
    # Get the project
    proj = get_object_or_404(Project, pk=project_id)
    
    # Dict for view
    view_dict = {}
    view_dict['project'] = proj
    
    # Get allocations for project
    allocations = RSEAllocation.objects.filter(project=proj)
    view_dict['allocations'] = allocations

    # append salary and costs information for template
    append_project_and_allocation_costs(proj, allocations)


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
        return reverse_lazy('project_allocations_edit', kwargs={'project_id': self.object.project.id})
        
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
    view_dict = {}

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
    view_dict = {}
    
    # Get all financial years
    years = FinancialYear.objects.all()
    if years is None:
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
        messages.add_message(request, messages.DANGER, f'The {y} financial year does not exist in the database.')
        year = years[0]
    view_dict['year'] = year
    

    
    # Get all salary bands for the financial year
    salary_bands = SalaryBand.objects.filter(year=year).order_by('-grade', '-grade_point')
    view_dict['salary_bands'] = salary_bands
 
    return render(request, 'financialyears.html', view_dict)


@user_passes_test(lambda u: u.is_superuser)
def financialyear_edit(request: HttpRequest, year_id: int) -> HttpResponse:
    
    # Dict for view
    view_dict = {}

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
    view_dict = {}

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
    view_dict = {}

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
def costdistributions(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}

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
    view_dict = {}

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
    else:
        form = FilterProjectForm()

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
def serviceoutstanding(request: HttpRequest) -> HttpResponse:
    """
    View for any outstanding service projects (invoice not received)
    """

    # Dict for view
    view_dict = {}
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
    view_dict = {}

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
    else:
        form = FilterProjectForm()

    # save the form
    view_dict['form'] = form

    # Only get non internal service projects
    q &= Q(project__serviceproject__internal=False)
    # Get allocations based off Q filter and save the form
    allocations = RSEAllocation.objects.filter(q)
    allocation_unique_project_ids = allocations.values('project').distinct()

    # construct a query which filters for projects with allocations within time period (based off the unique ids)
    # OR where invoice is received within time period (no from or until date assume that it is received)
    qp = Q()
    qp &= Q(id__in=allocation_unique_project_ids) | (Q(invoice_received__gte=from_date) & Q(invoice_received__lt=until_date))
    allocation_unique_projects = ServiceProject.objects.filter(qp)

    # Get costs associated with each project
    project_costs = {}
    total_staff_cost = 0
    total_value = 0
    total_margin = 0
    for p in allocation_unique_projects:
        # get associated allocations
        p_a = allocations.filter(project=p)
        p_data = {}
        staff_cost = 0
        overhead = 0
        cost_breakdown = []
        # loop over allocations and calculate staff cost, overheads and the cost breakdown
        for a in p_a:
            salary_value = a.staff_cost(from_date, until_date)
            staff_cost += salary_value.staff_cost
            cost_breakdown += salary_value.cost_breakdown
        # calculate income value
        value = 0
        if p.invoice_received: # test that value is not null
            if  p.invoice_received > from_date and p.invoice_received <= until_date:  # test if the invoice received was within specified period
                value = p.value()
        # margin (overheads)
        margin = value - staff_cost
        # sum value, staff cost and calculate remainder (income)
        p_data['staff_cost'] = staff_cost 
        p_data['value'] = value
        p_data['margin'] = value - staff_cost
        p_data['cost_breakdown'] = cost_breakdown
        # add project and project costs to dictionary and calculate sums
        project_costs[p] = p_data
        total_staff_cost += staff_cost
        total_value +=  value
        total_margin += margin
    # Add project data and sums to view dict
    view_dict['project_costs'] = project_costs
    view_dict['total_staff_cost'] = total_staff_cost
    view_dict['total_value'] = total_value
    view_dict['total_margin'] = total_margin
	

    return render(request, 'serviceincome.html', view_dict)



@user_passes_test(lambda u: u.is_superuser)
def projectincome_summary(request: HttpRequest) -> HttpResponse:
    """
    View reports on allocated project income and staff expenditure.
    Internal projects are not considered.
    """

    # Dict for view
    view_dict = {}

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
    else:
        form = FilterProjectForm()

    # save the form
    view_dict['form'] = form

    # Only get non internal allocated projects
    q &= Q(project__allocatedproject__internal=False)
    # Get allocations based off Q filter and save the form
    allocations = RSEAllocation.objects.filter(q)
    allocation_unique_project_ids = allocations.values('project').distinct()

    # construct a query which filters for projects with allocations within time period (based off the unique ids)
    qp = Q(id__in=allocation_unique_project_ids)
    allocation_unique_projects = AllocatedProject.objects.filter(qp)

    # Get costs associated with each allocated project
    project_costs = {}
    total_staff_cost = 0
    total_overhead = 0
    for p in allocation_unique_projects:
        # get associated allocations
        p_a = allocations.filter(project=p)
        p_costs = p.staff_cost(from_date=from_date, until_date=until_date, allocations=p_a)
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
	
    return render(request, 'projectincome_summary.html', view_dict)

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
        staff_cost += a.staff_cost().staff_cost
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
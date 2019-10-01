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

    # filter to exclude internal projects (these dont have a cost distrubution)
    # filter to only include chargable service projects (or allocated projects)
    # additional query on allocatedproject_internal is required to include any elibable allocated projects (is_instance can be used on member)
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
def serviceincome(request: HttpRequest) -> HttpResponse:


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

    # Only get non internal service projects
    q &= Q(project__serviceproject__internal=False)
        
    # Get RSE allocations grouped by RSE based off Q filter and save the form
    allocations = RSEAllocation.objects.filter(q)
    view_dict['form'] = form

    # Get Unique projects from allocations
    allocation_unique_project_ids = allocations.values('project').distinct()
    allocation_unique_projects = Project.objects.filter(id__in=allocation_unique_project_ids)
    view_dict['projects'] = allocation_unique_projects

    # Get costs assiciated with each project
    for p in allocation_unique_projects:
        # get assiciated allocations
        p_a = allocations.filter(project=p)
        # sum value, staff cost and calculate remainder
        value = sum(a.cost for a in p_a)
	

    return render(request, 'serviceincome.html', view_dict)

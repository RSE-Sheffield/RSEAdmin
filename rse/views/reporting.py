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


from rse.models import *
from rse.forms import *
from rse.views.helper import *
 
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


    # filter to include allocations active today
    from_date = timezone.now().date()
    until_date = from_date + timedelta(days=1)
    q &= Q(end__gte=from_date)
    q &= Q(start__lte=until_date)

    # filter to only include chargable service projects (or allocated projects)
    # additional query on status is required to include any elidible allocated projects (as is_instance can not be used on member)
    q &= Q(project__serviceproject__charged=True) | Q(project__directlyincurredproject__isnull=False)
    # filter by funded only projects
    q &= Q(project__status='F')

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

    # internal project are included
    # filter to only include chargable service projects (or any directly incurred projects)
    # additional query (isnull) is required to include any eligible directly incurred projects (as is_instance can not be used on member)
    q &= Q(project__serviceproject__charged=True) | Q(project__directlyincurredproject__isnull=False)
        
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
        req_get_copy = request.GET.copy()

        # Set default status to 'Funded'
        req_get_copy['status'] = req_get_copy.get('status') or 'F'
        # Set default in employment status to 'Yes'
        req_get_copy['rse_in_employment'] = req_get_copy.get('rse_in_employment') or 'Yes'

        # Set default start and end date to current FY
        if req_get_copy.get('filter_range') is None:
            req_get_copy['filter_range'] = create_default_filter_range()
            
        form = FilterProjectForm(req_get_copy)
        
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
                
            rse_in_employment = form.cleaned_data["rse_in_employment"]

    # save the form
    view_dict['form'] = form

    rses_costs = {}
    total_staff_salary = total_recovered_staff_cost = total_internal_project_staff_cost = total_non_recovered_cost = total_staff_liability = 0
    
    rses = RSE.objects.all()
    
    # Filter RSEs by employment status
    if rse_in_employment != 'All':
        in_employment = True if rse_in_employment == 'Yes' else False
        filtered_rses_id = [rse.id for rse in rses if rse.current_employment == in_employment]
        rses = rses.filter(id__in=filtered_rses_id)

    for rse in (rse for rse in rses if rse.employed_in_period(from_date, until_date)):
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
                
            # allocated or chargeable service
            elif isinstance(a.project, DirectlyIncurredProject) or (isinstance(a.project, ServiceProject) and a.project.charged == True): 
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
    q &= Q(instance_of=DirectlyIncurredProject) | Q(Q(instance_of=ServiceProject) & Q(serviceproject__charged=True))
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
    q &= Q(instance_of=DirectlyIncurredProject) | Q(Q(instance_of=ServiceProject) & Q(serviceproject__charged=True))
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
        project = DirectlyIncurredProject.objects.get(id=project_id)
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
        days = rse.days_from_budget(start_date, float(remaining_budget), float(percent))
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
    for rse in (rse for rse in RSE.objects.all() if rse.employed_in_period(from_date, until_date)): # for all currently employed RSEs
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
        elif isinstance(p, DirectlyIncurredProject) or (isinstance(p, ServiceProject) and p.charged == True):  
            try:
                project_recovered_costs = p.staff_cost(from_date=from_date, until_date=until_date).staff_cost
            except ValueError:
                project_recovered_costs = 0
                messages.add_message(request, messages.ERROR, f'ERROR: Project {p} has allocations with missing RSE salary data in the time period starting at {from_date}.')
            recovered_staff_costs += project_recovered_costs
            # accumulate overheads
            overheads += p.overhead_value(from_date=from_date, until_date=until_date)
        # Service income
        if isinstance(p, ServiceProject):
            # value of project if invoice received in account period
            value = 0
            if p.invoice_received and p.invoice_received > from_date and p.invoice_received <= until_date:
                value = p.value()
            # surplus is value less any recovered (i.e. staff costs)
            surplus = value - project_recovered_costs
            # income from service project less any recovered staff cost
            service_income += surplus
    
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

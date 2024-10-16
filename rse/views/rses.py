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

import logging

logger = logging.getLogger(__name__)

from rse.models import *
from rse.forms import *
from rse.views.helper import *

############
### RSEs ###
############
   

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
        req_get_copy = request.GET.copy()
        # Set default status to 'Funded'
        req_get_copy['status'] = req_get_copy.get('status') or 'F'
        # Set default in employment status to 'All'
        req_get_copy['rse_in_employment'] = req_get_copy.get('rse_in_employment') or 'All'

        form = FilterProjectForm(req_get_copy)
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
    # if allocations:
    view_dict['stacked_commitment_data'] = [(rse, RSEAllocation.stacked_commitment_summary(allocations, from_date, until_date))]
    view_dict['from_date'] = from_date
    view_dict['until_date'] = until_date

	
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
    selected = request.GET.get('selected')
    sbs = SalaryBand.objects.filter(year=year).order_by('grade', 'grade_point')
    view_dict = {}
    view_dict['sbs'] = sbs
    if selected is not None and selected.isnumeric():
        view_dict['selected'] = int(selected)
    return render(request, 'includes/salaryband_options.html', view_dict)

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
        req_get_copy = request.GET.copy()

        # Set default status to 'Funded'
        req_get_copy['status'] = req_get_copy.get('status') or 'F'
        # Set default in employment status to 'Yes'
        req_get_copy['rse_in_employment'] = req_get_copy.get('rse_in_employment') or 'Yes'

        # Set default start and end date to current FY
        if req_get_copy.get('filter_range') is None:
            req_get_copy['filter_range'] = create_default_filter_range()

        # the 'initial' property doesn't work here because this is a bound form
        form = FilterProjectForm(req_get_copy)

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
                
            rse_in_employment = form.cleaned_data["rse_in_employment"]
                
    else:
        form = FilterProjectForm()
        
    # Get RSE allocations grouped by RSE based off Q filter and save the form
    allocations = RSEAllocation.objects.filter(q)
    view_dict['form'] = form
    
    # Filter by employment status
    if rse_in_employment != 'All':
        in_employment = True if rse_in_employment == 'Yes' else False
        
        # remove allocations from RSEs doesn't meet the criteria
        unique_rses_id = set([allocation.rse.id for allocation in allocations if allocation.rse.current_employment == in_employment])
        allocations = allocations.filter(rse__id__in=unique_rses_id)
   
        
    # Get unique RSE ids allocated to project and build list of (RSE, [RSEAllocation]) objects for commitment graph
    allocation_unique_rses = allocations.values('rse').distinct()

    stacked_commitment_data = []
    rse_allocations = {}
    num_allocations = 1 if len(rse_allocations) < 1 else len(rse_allocations)
    
    for a in allocation_unique_rses:
        r_a = allocations.filter(rse__id=a['rse'])
        rse = RSE.objects.get(id=a['rse'])
        rse_allocations[rse] = r_a
        stacked_commitment_data.append((rse, RSEAllocation.stacked_commitment_summary(r_a, from_date, until_date)))

    stacked_commitment_summary = RSEAllocation.stacked_commitment_summary(rse_allocations.values(),
                                                                          from_date,
                                                                          until_date,
                                                                          percent_scaling=1.0/num_allocations)
    stacked_commitment_data.append(({"user": {"first_name": "All selected"}}, stacked_commitment_summary))

    view_dict['stacked_commitment_data'] = stacked_commitment_data
    view_dict['rse_allocations'] = rse_allocations
    view_dict['from_date'] = from_date
    view_dict['until_date'] = until_date

    return render(request, 'commitments.html', view_dict)


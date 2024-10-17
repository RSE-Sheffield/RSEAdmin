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

    sb_form = NewSalaryBandForm(year=year)
    rate_form = UpdateRatesForm(instance=year)
    
    # Form handling for new salary bands and rate updates
    if request.method == 'POST':
        if 'sb_form' in request.POST:
            sb_form = NewSalaryBandForm(request.POST, year=year)
            if sb_form.is_valid():
                sb_form.save()
        
        if 'rate_form' in request.POST:
            rate_form = UpdateRatesForm(request.POST, instance=year)
            if rate_form.is_valid():
                rate_form.save()
                messages.add_message(request, message='Rates updated successfully.', level=messages.SUCCESS)

    view_dict['sb_form'] = sb_form
    view_dict['rate_form'] = rate_form
    
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
        """ Use the post function to handle protected error (i.e. the financial year is used by an directly incurred project or salary grade change) """
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
        """ Use the post function to handle protected error (i.e. the salary band is used by a directly incurred project or salary grade change) """
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
    

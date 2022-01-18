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
    rses = [x for x in RSE.objects.filter() if x.current_employment]
    try:
        average_capacity = sum(rse.current_capacity for rse in rses) / len(rses)
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
    danger_service_ended_not_invoiced =  ServiceProject.objects.filter(status=Project.FUNDED, internal=False, end__lt=now, invoice_received=None).count()
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




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
        # catch div by zero if duration is 0
        a.project_budget_percentage =  (a.staff_cost / staff_budget * 100.0) if staff_budget != 0 else 100
        total_staff_cost += a.staff_cost


    # Set project fields
    # service project
    if project.is_service:
        project.total_value = total_value
        project.staff_cost = total_staff_cost
        project.percent_total_budget = project.staff_cost / total_value * 100.0 if total_value!= 0 else 0
        project.remaining_surplus = total_value - total_staff_cost
    # allocated project
    else:   
        project.total_value = total_value
        project.staff_budget = staff_budget
        project.overhead = project.overhead_value()
        project.staff_cost = total_staff_cost
        # catch div by zero if duration is 0
        project.percent_staff_budget = project.staff_cost / staff_budget * 100.0 if staff_budget != 0 else 0
        project.remaining_staff_budget = staff_budget - total_staff_cost
        


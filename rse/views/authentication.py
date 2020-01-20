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
            sgc = SalaryGradeChange(rse=rse, date=rse_form.cleaned_data["employed_from"], salary_band=rse_form.cleaned_data["salary_band"])
            sgc.save()
            # confirmation message
            messages.add_message(request, messages.SUCCESS, f'New RSE user {user.username} created.')
            # Go to view of RSE salary grade changes
            return HttpResponseRedirect(reverse_lazy('rse_salary', kwargs={'rse_username': user.username}))
                
    else:
        user_form = NewUserForm()
        rse_form = NewRSEUserForm() 
        
    view_dict['user_form'] = user_form
    view_dict['rse_form'] = rse_form
    view_dict['edit'] = False   # form is nor new RSE not edit

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

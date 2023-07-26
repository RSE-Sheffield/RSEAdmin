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
    # Notify user of the new change
    messages.add_message(
        request, 
        level=messages.WARNING, 
        message="'Allocated' project type is renamed to 'Directly Incurred' as" \
                " 'Allocated' generally refer to an academic member of staff" \
                " rather than charged to the grant."
    )
        
    # Dict for view
    view_dict = {}  # type: Dict[str, object]
    
    # process or create form
    if request.method == 'POST':
        form = ProjectTypeForm(request.POST)
        if form.is_valid():
            type = form.cleaned_data['type']
            if type == 'D':
                return project_new_directly_incurred(request)
            else:
                return project_new_service(request)
    else:
        form = ProjectTypeForm()

    view_dict['form'] = form
    
    return render(request, 'project_new.html', view_dict)


@login_required
def project_new_directly_incurred(request: HttpRequest) -> HttpResponse:

    # Dict for view
    view_dict = {}  # type: Dict[str, object]
    
    # process or create form
    if request.method == 'POST' and 'project_submit' in request.POST:
        form = DirectlyIncurredProjectForm(request.POST)
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
        form = DirectlyIncurredProjectForm()
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
    
    return render(request, 'project_directly_incurred_new.html', view_dict)

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
    if isinstance(proj, DirectlyIncurredProject):
        formclass = DirectlyIncurredProjectForm
        template = 'project_directly_incurred_new.html'
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
    

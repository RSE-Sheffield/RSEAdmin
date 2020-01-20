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
        

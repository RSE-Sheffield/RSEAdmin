"""urlpatterns for the rse Django app."""
from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from . import views

urlpatterns = [
    ############################
    ### Time Tracking Pages ####
    ############################
    
    # Login using built in auth view
    url(r'^time/timesheet$', views.timesheet, name='timesheet'),

    #############################
    ### AJAX Responsive URLS ####
    #############################
    
    url(r'^time/timesheet/events$', views.timesheet_events, name='timesheet_events'),

    url(r'^time/timesheet/projects$', views.timesheet_projects, name='timesheet_projects'),

    url(r'^time/timesheet/add$', views.timesheet_add, name='timesheet_add'),

]

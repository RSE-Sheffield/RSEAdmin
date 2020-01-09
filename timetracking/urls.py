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
    
    # Responsive view to return all events/ time sheet entries (for a given rse)
    url(r'^time/timesheet/events$', views.timesheet_events, name='timesheet_events'),

    # Responsive view to return all projects (with a given set of dates in GET)
    url(r'^time/timesheet/projects$', views.timesheet_projects, name='timesheet_projects'),

    # Responsive view to add a time sheet entry
    url(r'^time/timesheet/add$', views.timesheet_add, name='timesheet_add'),

    # Responsive view to move or edit (resize) a time sheet entry
    url(r'^time/timesheet/edit$', views.timesheet_edit, name='timesheet_edit'),

    # Responsive view to move or edit (resize) a time sheet entry
    url(r'^time/timesheet/delete$', views.timesheet_delete.as_view(), name='timesheet_delete'),

    ########################
    ### Reporting Views ####
    ########################

    # Project commitment per person or team
    url(r'^time/project/(?P<project_id>[0-9]+)$', views.time_project, name='time_project'),

]

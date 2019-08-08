"""urlpatterns for the rse Django app."""
from django.conf.urls import url

from . import views


urlpatterns = [
    # main site index
    # ex: /training
    url(r'^$', views.index, name='index'),



    ################################
    ### Projects and Allocations ###
    ################################

    # Reporting: View All Projects (list view)
    url(r'^projects$', views.projects, name='projects'),

    # Project view
    url(r'^project/(?P<project_id>[0-9]+)$', views.project_view, name='project_view'),
    
    # Create Project view
    url(r'^project/new$', views.project_new, name='project_new'),
    
    # Edit Project view
    url(r'^project/(?P<project_id>[0-9]+)/edit$', views.project_edit, name='project_edit'),
    
    # Project allocation view
    url(r'^project/(?P<project_id>[0-9]+)/allocations$', views.project_allocations, name='project_allocations'),
    
    # Allocation delete (forwards to project allocation view)
    url(r'^project/allocations/(?P<pk>[0-9]+)/delete$', views.project_allocations_view_delete.as_view(), name='project_allocations_view_delete'),

    ###############
    ### Clients ###
    ###############

    # TODO

    #################
    ### Reporting ###
    #################


    # RSE team view all
    url(r'^team$', views.team_view, name='team_view'),
    
    # RSE team commitment view all
    url(r'^commitment$', views.commitment_view, name='commitment_view'),


    ############
    ### RSEs ###
    ############

    # RSE view
    url(r'^rse/(?P<rse_username>[\w]+)$', views.rse_view, name='rse_view'),
        
    # RSE allocation view by rse id
    url(r'^rse/id/(?P<rse_id>[0-9]+)$', views.rseid_view, name='rseid_view'),
    url(r'^rse/id/$', views.rseid_view, name='rseid_view'), # without id parameter
]

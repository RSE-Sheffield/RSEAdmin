"""urlpatterns for the rse Django app."""
from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from . import views


urlpatterns = [
    # main site index
    # ex: /training
    url(r'^$', views.index, name='index'),

    #######################
    ### Authentication ####
    #######################
    
    # Login using built in auth view
    url(r'^login/?$', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    
    # Logout using built in auth view
    url(r'^logout/?$', auth_views.LogoutView.as_view(), name='logout'),
    
    # change password using built in auth view
    url(r'^changepassword/?$', auth_views.PasswordChangeView.as_view(template_name='changepassword.html', success_url=reverse_lazy('index')), name='change_password'),
    
    # New user (choose type) view
    url(r'^user/new/?$', views.user_new, name='user_new'),
    
    # New rse user view
    url(r'^user/new/rse?$', views.user_new_rse, name='user_new_rse'),
    
    # New admin user view
    url(r'^user/new/admin?$', views.user_new_admin, name='user_new_admin'),
    


    ################################
    ### Projects and Allocations ###
    ################################

    # View All Projects (list view)
    url(r'^projects$', views.projects, name='projects'),

    # Create Allocated Project view
    url(r'^project/new$', views.project_new, name='project_new'),

    # Create Allocated Project view
    url(r'^project/allocated/new$', views.project_new_allocated, name='project_new_allocated'),
    
    # Create Service Project view
    url(r'^project/service/new$', views.project_new_service, name='project_new_service'),

    # Project view
    url(r'^project/(?P<project_id>[0-9]+)$', views.project, name='project'),
      
    # Edit Project view
    url(r'^project/(?P<project_id>[0-9]+)/edit$', views.project_edit, name='project_edit'),
    
    # Project allocation view
    url(r'^project/(?P<project_id>[0-9]+)/allocations$', views.project_allocations, name='project_allocations'),
    
    # Allocation delete (forwards to project allocation view)
    url(r'^project/allocations/(?P<pk>[0-9]+)/delete$', views.project_allocations_delete.as_view(), name='project_allocations_delete'),
    
    # Project delete
    url(r'^project/(?P<pk>[0-9]+)/delete$', views.project_delete.as_view(), name='project_delete'),

    ###############
    ### Clients ###
    ###############

    # View All Clients (list view)
    url(r'^clients$', views.clients, name='clients'),
    
    # View a client (and associated projects)
    url(r'^client/(?P<client_id>[0-9]+)$', views.client, name='client'),
    
    # Add a new client
    url(r'^client/new$', views.client_new, name='client_new'),
    
    # Edit a client (and associated projects)
    url(r'^client/(?P<client_id>[0-9]+)/edit$', views.client_edit, name='client_edit'),
    
    # Edit a client (and associated projects)
    url(r'^client/(?P<pk>[0-9]+)/delete$', views.client_delete.as_view(), name='client_delete'),


    ############
    ### RSEs ###
    ############

    # View a single RSE
    url(r'^rse/(?P<rse_username>[\w]+)$', views.rse, name='rse'),
    
    # RSE view list
    url(r'^rses$', views.rses, name='rses'),
        
    # RSE allocation view by rse id
    url(r'^rse/id/(?P<rse_id>[0-9]+)$', views.rseid, name='rseid'),
    url(r'^rse/id/$', views.rseid, name='rseid'), # without id parameter
       
    # RSE team view all
    url(r'^team$', views.team, name='team'),
    
    # RSE team commitment view all
    url(r'^commitment$', views.commitment, name='commitment'),
    
    # Add RSE View
    

]

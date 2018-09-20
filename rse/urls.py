from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [

	# main site index
	# ex: /training
    url(r'^$', views.index, name='index'),
    
    
    # project allocation view
    #url(r'^project/all', views.project_view, name='project_viewall'),
    
    # project allocation view
    url(r'^project/(?P<project_id>[0-9]+)$', views.project_view, name='project_view'),
    
    #rse allocation view
    url(r'^rse/all', views.team_view, name='team_view'),
    
    #team allocation view
    url(r'^rse/(?P<rse_username>[\w]+)$', views.rse_view, name='rse_view'),
    
]
"""urlpatterns for the rse Django app."""
from django.conf.urls import url

from . import views


urlpatterns = [
    # main site index
    # ex: /training
    url(r'^$', views.index, name='index'),

    # Reporting: View All Projects (list view)
    url(r'^projects', views.projects, name='projects'),

    # Project allocation view
    url(r'^project/(?P<project_id>[0-9]+)$', views.project_view, name='project_view'),

    # RSE team view all
    url(r'^rse/all', views.team_view, name='team_view'),

    # RSE allocation view
    url(r'^rse/(?P<rse_username>[\w]+)$', views.rse_view, name='rse_view'),
]

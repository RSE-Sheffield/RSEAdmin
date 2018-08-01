from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [

	# main site index
	# ex: /training
    url(r'^$', views.index, name='index'),
    
]
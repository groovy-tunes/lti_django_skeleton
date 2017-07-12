from django.contrib import admin
from django.conf.urls import url

from . import views
from ltilaunch.views import LaunchView


urlpatterns = [
    url(r'^config$', views.ConfigView.as_view(),
        name='lti_config'),
    url(r'^launch$', LaunchView.as_view(),
        name='lti_launch'),
    url(r'^index/(?P<a_id>[0-9]+)/(?P<a_g_id>[0-9]+)$', views.index,
        name='lti_index'),
    url(r'^select$', LaunchView.as_view(tool_provider_url='/select'),
        name='lti_select'),
]

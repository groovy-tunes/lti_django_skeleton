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
    url(r'^launch/select$', LaunchView.as_view(tool_provider_url='lti_select'),
		    name='lti_launch_select'),
    url(r'^select$', views.select,
        name='lti_select'),
    url(r'^check_assignments$', views.check_assignments,
        name='lti_check_assignments'),
    url(r'^save_code$', views.save_code,
        name='lti_save_code'),
    url(r'^save_events', views.save_events,
        name='lti_save_events'),
    url(r'^save_correct$', views.save_correct,
        name='lti_save_correct')
    url(r'^get_submission_code/(?P<submission_id>[0-9]+)$', views.get_submission_code,
        name='get_submission_code')
]

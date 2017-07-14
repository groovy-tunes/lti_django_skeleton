from django.contrib import admin
from django.conf.urls import url

from . import views
from ltilaunch.views import LaunchView


urlpatterns = [
    url(r'^config$', views.ConfigView.as_view(),
        name='lti_config'),
    url(r'^launch$', LaunchView.as_view(tool_provider_url='get_submission_code'),
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
        name='lti_save_correct'),
    url(r'^save_presentation$', views.save_presentation,
        name='lti_save_presentation'),
    url(r'^get_submission_code/(?P<submission_id>[0-9]+)$', views.get_submission_code,
        name='lti_get_submission_code'),
    url(r'^assignment/new/(?P<menu>[a-zA-Z]*)$', views.new_assignment,
        name='lti_new_assignment'),
    #TESTING
    url(r'^launch/(?P<id>[0-9]+)$', LaunchView.as_view(tool_provider_url='get_submission_code'),
        name='lti_launch_test')
]

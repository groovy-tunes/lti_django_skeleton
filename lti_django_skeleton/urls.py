from django.contrib import admin
from django.conf.urls import url

from . import views
from ltilaunch.views import LaunchView


urlpatterns = [
    url(r'^config$', views.ConfigView.as_view(),
        name='lti_config'),
    url(r'^launch$', LaunchView.as_view(tool_provider_url='assignment/new/'),
        name='lti_launch'),
    url(r'^$', views.index,
        name='lti_index'),
    url(r'^index$', views.index,
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
    url(r'^assignment/remove/(?P<assignment_id>[0-9]+)$', views.remove_assignment,
        name='lti_remove_assignment'),
    url(r'^assignment/get/(?P<assignment_id>[0-9]+)$', views.get_assignment,
        name='lti_get_assignment'),
    url(r'^select_builtin_assignment$', views.select_builtin_assignment,
        name='lti_select_builtin_assignment'),
    url(r'^edit_assignment/(?P<assignment_id>[0-9]+)$', views.edit_assignment,
        name='lti_edit_assignment'),
    url(r'^batch_edit$', views.batch_edit,
        name='lti_batch_edit'),
    url(r'^dashboard$', views.dashboard,
        name='lti_dashboard'),
    url(r'^share$', views.share,
        name='lti_share'),
    url(r'^shared$', views.shared,
        name='lti_shared'),
    url(r'^grade$', views.grade,
        name='lti_grade')
]

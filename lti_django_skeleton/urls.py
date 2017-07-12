from django.contrib import admin
from django.conf.urls import url

from . import views
from ltilaunch.views import LaunchView


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^config$', views.ConfigView.as_view(),
        name='lti_config'),
    url(r'^launch$', LaunchView.as_view(),
        name='lti_launch'),
    url(r'^index/(?P<a_id>[0-9]+)/(?P<a_g_id>[0-9]+)$', views.index,
        name='lti_index'),
]

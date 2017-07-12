from django.conf.urls import url

from .views import LaunchView, ConfigView, ReturnRedirectView

urlpatterns = [
    url(r'^testlaunch', LaunchView.as_view(), name='testlaunch'),
    url(r'^config/(?P<slug>\w+)/$',
        ConfigView.as_view(template_name='config.xml'),
        name='lti_config_view'),
    url(r'^redirect',
        ReturnRedirectView.as_view(),
        name='redirect_view')
]


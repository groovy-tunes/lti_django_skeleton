from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^lti/', (include('lti_django_skeleton.urls'))),
]

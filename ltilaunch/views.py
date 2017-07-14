from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from django.contrib.auth import login, authenticate
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.template.response import SimpleTemplateResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, ListView, View
from django.shortcuts import redirect

from . import LTIUSER_SESSION_KEY
from .models import lti_launch_return_url, LTIToolProvider, get_lti_user, \
    LTIUser
from .utils import absolute_url_for_path, as_https

def unauthorized_response():
    result = SimpleTemplateResponse(template="lti_launch_failure.html")
    result.status_code = 401
    result['WWW-Authenticate'] = 'OAuth realm=""'
    return result


class LaunchView(View):
    tool_provider_url = '/'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(LaunchView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        return self.authorize(request)

    def authorize(self, request):
        result = unauthorized_response()
        lti_user = authenticate(launch_request=request)
        if lti_user:
            login(request, lti_user)
            self._set_session_data(request)
            result = redirect(self.tool_provider_url)
        return result

    @staticmethod
    def _set_session_data(request):
        lti_user = get_lti_user(request.POST)
        request.session[LTIUSER_SESSION_KEY] = lti_user.pk


class ReturnRedirectView(View):
    def get(self, request):
        if not request.user.is_authenticated():
            result = unauthorized_response()
        else:
            # FIXME: not sure what best default behavior is
            result = HttpResponseNotFound()
            return_url = lti_launch_return_url(request.user)
            if return_url:
                parsed = urlparse(return_url)
                launch_q = list(parse_qs(parsed.query).items())
                return_q = list(request.GET.items())
                new_q = urlencode(launch_q + return_q, doseq=True)
                url = urlunparse(
                    (parsed[0],
                     parsed[1],
                     parsed[2],
                     parsed[3],
                     new_q,
                     parsed[5]))
                result = HttpResponseRedirect(url, status=303)
        return result


class ConfigView(DetailView):
    content_type = "application/xml"
    model = LTIToolProvider
    slug_field = "name"

    def get_context_data(self, **kwargs):
        context = super(ConfigView, self).get_context_data(**kwargs)
        launch_url = absolute_url_for_path(
            request=self.request, path=self.object.launch_path)
        context['launch_url'] = launch_url
        context['secure_launch_url'] = as_https(launch_url)
        context['icon'] = self.object.icon_url
        context['secure_icon'] = as_https(self.object.icon_url)
        return context


class DevLoginView(ListView):
    tool_provider_url = '/'
    model = LTIUser
    template_name = "devlogin.html"

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(DevLoginView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        result = unauthorized_response()
        lti_user = LTIUser.objects.get(id=request.POST["lti_user_id"])
        if lti_user:
            user = authenticate(dev_lti_user=lti_user)
            login(request, user,
                  backend="ltilaunch.auth.DevLTILaunchBackend")
            request.session[LTIUSER_SESSION_KEY] = lti_user.pk
            result = HttpResponseRedirect(self.tool_provider_url, status=303)
        return result

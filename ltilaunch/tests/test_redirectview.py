from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import override_settings, TestCase
from django.utils.timezone import now

from ltilaunch.models import LTIUser, LTIToolConsumer


@override_settings(ROOT_URLCONF="ltilaunch.test_urls")
class RedirectViewTestCase(TestCase):
    fixtures = ["ltilaunch"]

    def setUp(self):
        self.user = User.objects.get(id=1)
        self.consumer = LTIToolConsumer.objects.create(
            name="whatever"
        )
        self.lti_user = LTIUser.objects.create(
            user=self.user,
            lti_user_id="irrelevant",
            lti_tool_consumer=self.consumer,
            last_launch_parameters={"launch_presentation_return_url":
                                    "http://example.com/test?foo=bar"},
            last_launch_time=now())

    def test_launch_return(self):
        self.client.force_login(self.user, "ltilaunch.auth.LTILaunchBackend")
        url = reverse("redirect_view") + "?lti_msg=Test"
        resp = self.client.get(url, follow=False)
        self.assertRedirects(resp,
                             "http://example.com/test?foo=bar&lti_msg=Test",
                             fetch_redirect_response=False,
                             status_code=303)

    def test_requires_login(self):
        url = reverse("redirect_view")
        resp = self.client.get(url, follow=False)
        self.assertEqual(401, resp.status_code)

    def test_requires_ltiuser(self):
        self.lti_user.delete()
        self.client.force_login(self.user, "ltilaunch.auth.LTILaunchBackend")
        url = reverse("redirect_view")
        resp = self.client.get(url, follow=False)
        self.assertEqual(404, resp.status_code)

import oauthlib.oauth1
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings

from ltilaunch.models import LTIToolConsumer, LTIUser


@override_settings(ROOT_URLCONF='ltilaunch.test_urls',
                   AUTHENTICATION_BACKENDS=('ltilaunch.auth.LTILaunchBackend',))
class LaunchViewTestCase(TestCase):
    guid = "abcdefg"
    user_id = "user1"

    def setUp(self):
        self.consumer = LTIToolConsumer.objects.create(
            name="testconsumer",
            description="Test LTI Tool Consumer",
            tool_consumer_instance_guid=self.guid
        )
        self.key = self.consumer.oauth_consumer_key
        self.secret = self.consumer.oauth_consumer_secret
        self.uri = "https://testserver" + reverse("testlaunch")

    def test_wrong_consumer(self):
        oauth_signer = oauthlib.oauth1.Client(
            client_key="invalid",
            client_secret=self.secret,
            signature_type=oauthlib.oauth1.SIGNATURE_TYPE_BODY)
        params = {"tool_consumer_instance_guid": self.guid,
                  "user_id": self.user_id}
        self._failure(oauth_signer, params)

    def test_bad_signature(self):
        oauth_signer = oauthlib.oauth1.Client(
            client_key=self.key,
            client_secret="invalid",
            signature_type=oauthlib.oauth1.SIGNATURE_TYPE_BODY)
        params = {"tool_consumer_instance_guid": self.guid,
                  "user_id": self.user_id}
        self._failure(oauth_signer, params)

    def test_guid_mismatch(self):
        oauth_signer = oauthlib.oauth1.Client(
            client_key=self.key,
            client_secret=self.secret,
            signature_type=oauthlib.oauth1.SIGNATURE_TYPE_BODY)
        params = {"tool_consumer_instance_guid": "not the right thing",
                  "user_id": self.user_id}
        self._failure(oauth_signer, params)

    def test_guid_mismatch_ok(self):
        self.consumer.match_guid_and_consumer = False
        self.consumer.save()
        oauth_signer = oauthlib.oauth1.Client(
            client_key=self.key,
            client_secret=self.secret,
            signature_type=oauthlib.oauth1.SIGNATURE_TYPE_BODY)
        params = {"user_id": self.user_id,
                  "music": "response"}
        self._successful(oauth_signer, params)

    def test_success(self):
        oauth_signer = oauthlib.oauth1.Client(
            client_key=self.key,
            client_secret=self.secret,
            signature_type=oauthlib.oauth1.SIGNATURE_TYPE_BODY)
        params = {"tool_consumer_instance_guid": self.guid,
                  "user_id": self.user_id,
                  "music": "response"}
        self._successful(oauth_signer, params)

    def test_same_user(self):
        self.test_success()
        self.test_success()
        self.assertEqual(1, LTIUser.objects.count())

    def _successful(self, oauth_signer, params):
        uri, headers, body = oauth_signer.sign(
            self.uri,
            http_method="POST",
            body=params,
            headers={"Content-Type": "application/x-www-form-urlencoded"})
        resp = self.client.post(
            uri, body,
            headers=headers,
            secure=True,
            content_type="application/x-www-form-urlencoded")
        self.assertIsNotNone(resp, "response should not be None")
        users = LTIUser.objects.filter(lti_user_id=self.user_id)
        self.assertEqual(1, len(users), "user should exist")
        # check cool json stuff
        results = LTIUser.objects.filter(
            last_launch_parameters__music='response')
        self.assertEqual(1, len(results),
                         "should be able to search by LTI launch data")
        self.assertRedirects(resp, '/', status_code=303,
                             fetch_redirect_response=False)
        self.assertIn('sessionid', resp.client.cookies)

    def _failure(self, oauth_signer, params):
        uri, headers, body = oauth_signer.sign(
            self.uri,
            http_method="POST",
            body=params,
            headers={"Content-Type": "application/x-www-form-urlencoded"})
        resp = self.client.post(
            uri, body,
            headers=headers,
            secure=True,
            content_type="application/x-www-form-urlencoded")
        self.assertIsNotNone(resp, "response should not be None")
        self.assertEquals(401, resp.status_code,
                          "response status should be 401 Unauthorized")
        self.assertNotIn('sessionid', resp.client.cookies)

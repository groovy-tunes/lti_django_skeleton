from django.contrib.admin import AdminSite
from django.test import TestCase
from django.test.client import RequestFactory

from ltilaunch.admin import LTIToolConsumerAdmin, LTIToolProviderAdmin
from ltilaunch.models import LTIToolConsumer, LTIToolProvider


class LTIToolConsumerAdminTestCase(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def test_form_widgets(self):
        admin = LTIToolConsumerAdmin(LTIToolConsumer, AdminSite())
        req = self.request_factory.get('/')
        form = admin.get_form(req)
        self.assertIsNotNone(form)
        for field in ('tool_consumer_instance_guid',
                      'oauth_consumer_secret',
                      'oauth_consumer_key'):
            self.assertIn(field, form.base_fields)
            widget = form.base_fields[field].widget
            self.assertEquals(1, widget.attrs['rows'])


class LTIToolProviderAdminTestCase(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def test_form_widgets(self):
        admin = LTIToolProviderAdmin(LTIToolProvider, AdminSite())
        req = self.request_factory.get('/')
        form = admin.get_form(req)
        self.assertIsNotNone(form)
        self.assertIn('launch_path', form.base_fields)
        widget = form.base_fields['launch_path'].widget
        self.assertEquals(1, widget.attrs['rows'])

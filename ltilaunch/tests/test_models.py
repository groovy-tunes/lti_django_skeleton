from django.test import TestCase

from ltilaunch.models import LTIToolConsumer, LTIToolProvider


class LTIToolConsumerTestCase(TestCase):
    def test_name(self):
        c = LTIToolConsumer.objects.create(
            name="foo",
            oauth_consumer_key="bar",
            oauth_consumer_secret="thud"
        )
        self.assertEquals(c.name, str(c))


class LTIToolProviderTestCase(TestCase):
    def test_name(self):
        c = LTIToolProvider.objects.create(
            name="foo",
            display_name="bar",
            launch_path="/thud"
        )
        self.assertEquals(c.name, str(c))
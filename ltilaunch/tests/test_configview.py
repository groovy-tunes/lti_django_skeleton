import xml.etree.ElementTree as ET

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import override_settings, TestCase

from ltilaunch.models import LTIToolProvider

XMLNS = {
    "ims": "http://www.imsglobal.org/xsd/imslticc_v1p0",
    "blti": "http://www.imsglobal.org/xsd/imsbasiclti_v1p0"
}


@override_settings(ROOT_URLCONF='ltilaunch.test_urls')
class ConfigViewTestCase(TestCase):
    fixtures = ['ltilaunch']

    def setUp(self):
        self.provider = LTIToolProvider.objects.create(
            description="test",
            name="test",
            launch_path="/test",
            visibility="members"
        )
        self.site = Site.objects.all()[0]

    def test_config_view(self):
        url = reverse('lti_config_view', kwargs=dict(slug="test"))
        resp = self.client.get(url)
        self.assertEqual(200, resp.status_code)
        self.assertEqual("application/xml", resp['Content-Type'])
        doc = ET.fromstring(resp.content)
        urls = doc.findall("blti:secure_launch_url", XMLNS)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://{}/test".format(self.site.domain),
                         urls[0].text)

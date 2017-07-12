from django.test import TestCase

from ltilaunch.auth import LTILaunchBackend


class LTILaunchBackendTestCase(TestCase):
    fixtures = ['ltilaunch']

    def setUp(self):
        self.backend = LTILaunchBackend()

    def test_user_found(self):
        self.assertIsNotNone(self.backend.get_user(1))

    def test_user_not_found(self):
        self.assertIsNone(self.backend.get_user(3))

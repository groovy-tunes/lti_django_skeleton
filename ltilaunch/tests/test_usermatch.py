from django.test import TestCase

from ltilaunch.models import (LTIToolConsumer, LTIToolConsumerGroup,
                              get_or_create_lti_user)


class LTIUserMatcherTestCase(TestCase):
    def test_same_group(self):
        group = LTIToolConsumerGroup.objects.create(name="group")
        consumer1 = LTIToolConsumer.objects.create(
            name="testconsumer1",
            tool_consumer_instance_guid="testconsumer1",
            matcher_class_name="ltilaunch.usermatch.LTIUserMatcher",
            consumer_group=group
        )
        consumer2 = LTIToolConsumer.objects.create(
            name="testconsumer2",
            tool_consumer_instance_guid="testconsumer2",
            matcher_class_name="ltilaunch.usermatch.LTIUserMatcher",
            consumer_group=group
        )
        lti_launch1 = {
            "tool_consumer_instance_guid": "testconsumer1",
            "user_id": "alice"
        }
        lti_launch2 = {
            "tool_consumer_instance_guid": "testconsumer2",
            "user_id": "alice"
        }
        lti_launch3 = {
            "tool_consumer_instance_guid": "testconsumer2",
            "user_id": "bob"
        }
        lti_launch4 = {
            "tool_consumer_instance_guid": "testconsumer2",
            "user_id": "bob"
        }
        alice1 = get_or_create_lti_user(consumer1, lti_launch1)
        self.assertIsNotNone(alice1)
        alice2 = get_or_create_lti_user(consumer2, lti_launch2)
        self.assertIsNotNone(alice2)
        self.assertEqual(alice1.user.pk, alice2.user.pk)
        bob1 = get_or_create_lti_user(consumer1, lti_launch3)
        bob2 = get_or_create_lti_user(consumer2, lti_launch4)
        self.assertEqual(bob1.user.pk, bob2.user.pk)
        self.assertNotEqual(alice1.user.pk, bob1.user.pk)


class CanvasCustomUserMatcherTestCase(TestCase):
    def test_match_canvas_id(self):
        group = LTIToolConsumerGroup.objects.create(name="group")
        consumer1 = LTIToolConsumer.objects.create(
            name="testconsumer1",
            tool_consumer_instance_guid="testconsumer1",
            matcher_class_name="ltilaunch.usermatch.CanvasCustomUserMatcher",
            consumer_group=group
        )
        consumer2 = LTIToolConsumer.objects.create(
            name="testconsumer2",
            tool_consumer_instance_guid="testconsumer2",
            matcher_class_name="ltilaunch.usermatch.CanvasCustomUserMatcher",
            consumer_group=group
        )
        lti_launch1 = {
            "tool_consumer_instance_guid": "testconsumer1",
            "user_id": "aliceABC",
            "custom_canvas_user_login_id": "alice"

        }
        lti_launch2 = {
            "tool_consumer_instance_guid": "testconsumer2",
            "user_id": "aliceXYZ",
            "custom_canvas_user_login_id": "alice",
            "lis_person_sourcedid": "1234"
        }

        alice1 = get_or_create_lti_user(consumer1, lti_launch1)
        self.assertIsNotNone(alice1)
        alice2 = get_or_create_lti_user(consumer2, lti_launch2)
        self.assertIsNotNone(alice2)
        self.assertEqual(alice1.user.pk, alice2.user.pk)

        lti_mobile = {
            "tool_consumer_instance_guid": "testconsumer2",
            "user_id": "aliceDEF",
            "custom_canvas_user_login_id": "$Canvas.user.loginId",
            "lis_person_sourcedid": "1234"
        }

        alice3 = get_or_create_lti_user(consumer2, lti_mobile)
        self.assertIsNotNone(alice3)
        self.assertEqual(alice1.user.pk, alice3.user.pk)

    def test_no_consumer_groups(self):
        consumer1 = LTIToolConsumer.objects.create(
            name="testconsumer1",
            tool_consumer_instance_guid="testconsumer1",
            matcher_class_name="ltilaunch.usermatch.CanvasCustomUserMatcher"
        )
        lti_launch1 = {
            "tool_consumer_instance_guid": "testconsumer1",
            "user_id": "aliceABC",
            "custom_canvas_user_login_id": "alice",
            "lis_person_sourcedid": "1234"
        }
        lti_launch2 = {
            "tool_consumer_instance_guid": "testconsumer1",
            "user_id": "aliceXYZ",
            "custom_canvas_user_login_id": "$Canvas.user.loginId",
            "lis_person_sourcedid": "1234"
        }

        alice1 = get_or_create_lti_user(consumer1, lti_launch1)
        alice2 = get_or_create_lti_user(consumer1, lti_launch2)
        self.assertIsNotNone(alice1)
        self.assertIsNotNone(alice2)
        self.assertEqual(alice1.user.pk, alice2.user.pk)

        # we should not devolve into matching user data without respect for
        # consumer! i.e. 'alice' @iu.edu is not the same person as 'alice'
        # @umich.edu!
        other_consumer = LTIToolConsumer.objects.create(
            name="testconsumer2",
            tool_consumer_instance_guid="testconsumer2",
            matcher_class_name="ltilaunch.usermatch.CanvasCustomUserMatcher"
        )

        other_launch = {
            "tool_consumer_instance_guid": "testconsumer2",
            "user_id": "aliceABC",
            "custom_canvas_user_login_id": "alice",
            "lis_person_sourcedid": "1234"
        }

        other_alice = get_or_create_lti_user(other_consumer, other_launch)
        self.assertIsNotNone(other_alice)
        self.assertNotEqual(alice1.user.pk, other_alice.user.pk,
                            "users from different consumers should not match"
                            " without being in the same consumer group")

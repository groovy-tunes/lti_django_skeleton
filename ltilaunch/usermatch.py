from pydoc import locate
from django.db import models

from ltilaunch.models import LTIToolConsumer


class LTIUserMatcher:
    lti_user_model = "ltilaunch.models.LTIUser"

    def _scope_to_consumer_group(self,
                                 lti_consumer: LTIToolConsumer):
        all_users = locate(self.lti_user_model).objects.all() # type: models.query.QuerySet
        group = lti_consumer.consumer_group
        if group:
            consumers = LTIToolConsumer.objects.filter(consumer_group=group)
        else:
            consumers = LTIToolConsumer.objects.filter(pk=lti_consumer.pk)
        return all_users.filter(lti_tool_consumer__in=consumers)

    def get_matching_user(self,
                          lti_consumer: LTIToolConsumer,
                          launch_data: dict):
        """Return a Django user for the given launch data.

        Uses the users_for_launch method to execute a query against the LTI
        user database.

        :param lti_consumer: an LTIConsumer object for the launch data
        :param launch_data: a dict containing LTI launch parameters
        :return: a User object, or None if no users match the launch data
        """
        other_users = self._scope_to_consumer_group(lti_consumer)
        results = self.users_for_launch(other_users, launch_data)
        if results.exists():
            return results[0].user
        else:
            return None

    def users_for_launch(self,
                         lti_users: models.query.QuerySet,
                         launch_data: dict):
        """Match the given launch data to known LTI users.

        Override this method to provide custom user search logic against the
        LTI user database.  The returned result should contain either
        zero or one result.

        :param lti_users: a query set scoped to a LTIToolConsumerGroup
        :param launch_data: a dict containing LTI launch parameters
        :return: a query set containing Django user(s) for launch data
        """
        return lti_users.filter(lti_user_id=launch_data["user_id"])


class CanvasCustomUserMatcher(LTIUserMatcher):
    def users_for_launch(self,
                         lti_users: models.query.QuerySet,
                         launch_data: dict):
        result = lti_users.none()
        canvas_id = launch_data.get("custom_canvas_user_login_id")
        if canvas_id and canvas_id != "$Canvas.user.loginId":
            result = lti_users.filter(
                last_launch_parameters__custom_canvas_user_login_id=canvas_id)
        if not result.exists():
            lis_id = launch_data.get("lis_person_sourcedid")
            if lis_id:
                result = lti_users.filter(
                    last_launch_parameters__lis_person_sourcedid=lis_id)
        return result

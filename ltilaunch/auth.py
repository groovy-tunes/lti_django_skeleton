import logging

from django.contrib.auth import get_user_model

from .utils import headers_from_request
from .models import get_or_create_lti_user, LTIToolConsumer
from .oauth import validate_lti_launch

logger = logging.getLogger(__name__)


class DevLTILaunchBackend:
    @staticmethod
    def authenticate(dev_lti_user=None):
        return dev_lti_user.user if dev_lti_user else None

    @staticmethod
    def get_user(user_id):
        um = get_user_model()
        try:
            return um.objects.get(pk=user_id)
        except um.DoesNotExist:
            return None


class LTILaunchBackend:
    required_keys = {'oauth_consumer_key',
                     'user_id'}

    def authenticate(self, launch_request=None):
        result = None
        if launch_request:
            if launch_request.POST.keys() >= self.required_keys:
                result = self._find_lti_user(launch_request)
        return result

    @staticmethod
    def _find_lti_user(launch_request):
        consumer_key = launch_request.POST['oauth_consumer_key']
        lti_user_id = launch_request.POST['user_id']
        tool_guid = launch_request.POST.get(
            'tool_consumer_instance_guid', '')
        result = None
        try:
            consumer = LTIToolConsumer.objects.get(
                oauth_consumer_key=consumer_key)
        except LTIToolConsumer.DoesNotExist:
            logger.error("no LTI consumer found for OAuth consumer key '%s'",
                         consumer_key)
        else:
            guid_mismatch = consumer.tool_consumer_instance_guid != tool_guid
            if consumer.match_guid_and_consumer and guid_mismatch:
                logger.error(
                    "OAuth consumer key '%s' and tool consumer instance GUID "
                    "'%s' do not match", consumer_key, tool_guid)
            else:
                is_valid, req = validate_lti_launch(
                    consumer,
                    launch_request.build_absolute_uri(),
                    launch_request.body,
                    headers_from_request(launch_request))
                logger.debug("request: %s", req)
                if not is_valid:
                    logger.error(
                        "LTI launch not valid for OAuth consumer key '%s',"
                        " user_id '%s'", consumer_key, lti_user_id)
                else:
                    result = get_or_create_lti_user(
                        consumer, launch_request.POST).user
        return result

    @staticmethod
    def get_user(user_id):
        um = get_user_model()
        try:
            return um.objects.get(pk=user_id)
        except um.DoesNotExist:
            return None

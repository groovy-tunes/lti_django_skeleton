import logging
from pydoc import locate

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField, ArrayField
from django.db import models
from django.utils import timezone

from .utils import generate_random_string


logger = logging.getLogger(__name__)


class LTIToolConsumerGroup(models.Model):
    name = models.CharField(max_length=50, blank=False, unique=True)

    def __str__(self):  # pragma: no cover
        return self.name

    class Meta:
        verbose_name = "LTI tool consumer group"


class LTIToolConsumer(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    oauth_consumer_key = models.TextField(
        unique=True,
        default=generate_random_string,
        verbose_name="OAuth consumer key")
    oauth_consumer_secret = models.TextField(
        default=generate_random_string,
        verbose_name="OAuth consumer secret")
    tool_consumer_instance_guid = models.TextField(
        verbose_name="Tool consumer instance GUID")
    match_guid_and_consumer = models.BooleanField(
        default=True,
        verbose_name="Match GUID and OAuth consumer")
    recent_nonces = ArrayField(base_field=models.TextField(),
                               size=10, default=[])
    consumer_group = models.ForeignKey(LTIToolConsumerGroup,
                                       blank=True,
                                       null=True,
                                       on_delete=models.SET_NULL)
    matcher_class_name = models.CharField(max_length=160,
                                          blank=True,
                                          null=True)

    def __str__(self):
        return self.name

    def add_nonce(self, nonce):
        self.recent_nonces = [nonce] + self.recent_nonces[:9]
        self.save()

    class Meta:
        verbose_name = "LTI tool consumer"


class LTIUser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    lti_tool_consumer = models.ForeignKey(
        LTIToolConsumer, verbose_name="LTI tool consumer")
    lti_user_id = models.TextField(verbose_name="LTI user ID")
    last_launch_parameters = JSONField()
    last_launch_time = models.DateTimeField()


    def __str__(self):
        return self.person_name


    @property
    def last_launch_course_id(self):
        return self.last_launch_parameters.get("custom_canvas_course_id", None)


    @property
    def person_name(self):
        if "lis_person_name_full" in self.last_launch_parameters:
            return self.last_launch_parameters["lis_person_name_full"]
        else:
            return self.user.username


    @property
    def source_lms(self):
        return "{}".format(self.lti_tool_consumer.name)


    class Meta:
        unique_together = ('lti_tool_consumer', 'lti_user_id')
        verbose_name = "LTI user"


    def is_admin(self):
        roles = Role.objects.filter(user=self)
        return 'admin' in {role.name.lower() for role in roles}


    def is_instructor(self):
        roles = Role.objects.filter(user=self)
        return 'instructor' in {role.name.lower() for role in self.roles}


    @staticmethod
    def is_lti_instructor(given_roles):
        ROLES = ["urn:lti:role:ims/lis/TeachingAssistant",
                 "Instructor", "ContentDeveloper",
                 "urn:lti:role:ims/lis/Instructor",
                 "urn:lti:role:ims/lis/ContentDeveloper"]
        return any(role for role in ROLES if role in given_roles)


    @staticmethod
    def new_lti_user(service, lti_user_id, lti_email, lti_first_name, lti_last_name):
        new_user = LTIUser(first_name=lti_first_name, last_name=lti_last_name, email=lti_email,
                        password="", active=False, confirmed_at=None)
        new_user.save()
        return new_user


class LTIToolProvider(models.Model):
    VISIBILITY_ALL = ""
    VISIBILITY_ADMINS = "admins"
    VISIBILITY_MEMBERS = "members"
    VISIBILITY_CHOICES = ((VISIBILITY_ALL, "All"),
                          (VISIBILITY_ADMINS, "Admins"),
                          (VISIBILITY_MEMBERS, "Members"))

    name = models.SlugField(blank=False, unique=True)
    display_name = models.CharField(max_length=50)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES,
                                  blank=True)
    description = models.TextField()
    icon_url = models.URLField(blank=True)
    launch_path = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "LTI tool provider"


def get_or_create_lti_user(consumer, launch_data):
    lti_user_id = launch_data["user_id"]
    try:
        lti_user = LTIUser.objects.get(
            lti_tool_consumer=consumer,
            lti_user_id=lti_user_id)
        lti_user.last_launch_parameters = launch_data
        lti_user.last_launch_time = timezone.now()
    except LTIUser.DoesNotExist:
        user_model = get_user_model()
        djuser = None
        if consumer.matcher_class_name:
            matcher_class = locate(consumer.matcher_class_name)
            matcher = matcher_class()
            djuser = matcher.get_matching_user(consumer, launch_data)
        if djuser is None:
            djuser = user_model.objects.create_user(
                username=(consumer.tool_consumer_instance_guid[:14] +
                          lti_user_id[:14]))
        lti_user = LTIUser.objects.create(
            user=djuser,
            lti_user_id=lti_user_id,
            lti_tool_consumer=consumer,
            last_launch_parameters=launch_data,
            last_launch_time=timezone.now()
        )
    lti_user.save()
    return lti_user


def get_lti_user(launch_data):
    lti_user_id = launch_data["user_id"]
    lti_consumer_key = launch_data["oauth_consumer_key"]
    return LTIUser.objects.get(
        last_launch_parameters__user_id=lti_user_id,
        lti_tool_consumer__oauth_consumer_key=lti_consumer_key)


def lti_launch_return_url(user):
    result = None
    try:
        lti_user = LTIUser.objects.get(user=user)
    except LTIUser.DoesNotExist:
        logger.error("no LTIUser found for '%s'", user)
    else:
        result = lti_user.last_launch_parameters.get(
            'launch_presentation_return_url', None)
    return result

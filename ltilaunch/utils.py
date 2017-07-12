import re
import string

import random
from django.contrib.sites.shortcuts import get_current_site

ALPHANUMERIC = string.ascii_lowercase + string.ascii_uppercase + string.digits


def generate_random_string(length=40):
    rnd = random.SystemRandom()
    return "".join(rnd.choice(ALPHANUMERIC) for _ in range(length))


def absolute_url_for_path(request, path):
    site = get_current_site(request)
    return "http://{domain}{path}".format(
        domain=site.domain,
        path=path)


def as_https(url):
    return re.sub(r"^http:", "https:", url)


HEADER_KEY_RE = re.compile(r"^(HTTP_.+|CONTENT_TYPE|CONTENT_LENGTH)$")


def meta_key_to_header(meta_key):
    return re.sub("_", "-", re.sub("^HTTP_", "", meta_key)).title()


def headers_from_request(request):
    return dict(
        (meta_key_to_header(k), v) for k, v in request.META.items()
        if re.match(HEADER_KEY_RE, k) and not k.startswith("HTTP_X_FORWARDED"))

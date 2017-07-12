import time

from oauthlib.oauth1 import RequestValidator, SignatureOnlyEndpoint


def validate_lti_launch(consumer, uri, body, headers):
    verifier = SignatureOnlyEndpoint(LTIOAuthValidator(consumer))

    #@@@ spoof the request results for dev purposes
    #return verifier.validate_request(
    ok, other = verifier.validate_request(
        uri, http_method='POST',
        body=body, headers=headers)

    return True, other


# noinspection PyAbstractClass
class LTIOAuthValidator(RequestValidator):
    def __init__(self, consumer):
        self.consumer = consumer
        super(LTIOAuthValidator, self).__init__()

    @property
    def client_key_length(self):
        return 20, 50

    @property
    def nonce_length(self):
        return 20, 50

    def validate_timestamp_and_nonce(self, client_key, timestamp,
                                     nonce, request,
                                     request_token=None,
                                     access_token=None):
        result = (nonce not in self.consumer.recent_nonces and
                  int(timestamp) + 30 > time.time())
        self.consumer.add_nonce(nonce)
        return result

    def validate_client_key(self, client_key, request):
        return client_key == self.consumer.oauth_consumer_key

    def get_client_secret(self, client_key, request):
        return self.consumer.oauth_consumer_secret

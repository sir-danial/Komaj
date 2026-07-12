from .views import healthz


class HealthCheckMiddleware:
    """Answer /healthz/ before host validation and the prod SSL redirect.

    Kubernetes probes hit the pod by its bare IP over plain HTTP, which would
    otherwise fail ALLOWED_HOSTS (the pod IP changes every deploy) or get
    caught by SECURE_SSL_REDIRECT. Must stay first in MIDDLEWARE, before
    SecurityMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in ("/healthz", "/healthz/"):
            return healthz(request)
        return self.get_response(request)

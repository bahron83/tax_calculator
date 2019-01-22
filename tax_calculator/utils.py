from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder


try:
    import json
except ImportError:
    from django.utils import simplejson as json

def json_response(body=None, errors=None, url=None, redirect_to=None, exception=None,
                  content_type=None, status=None):
    """Create a proper JSON response. If body is provided, this is the response.
    If errors is not None, the response is a success/errors json object.
    If redirect_to is not None, the response is a success=True, redirect_to object
    If the exception is provided, it will be logged. If body is a string, the
    exception message will be used as a format option to that string and the
    result will be a success=False, errors = body % exception
    """
    if isinstance(body, HttpResponse):
        return body
    if content_type is None:
        content_type = "application/json"
    if errors:
        if isinstance(errors, str):
            errors = [errors]
        body = {
            'success': False,
            'errors': errors
        }
    elif redirect_to:
        body = {
            'success': True,
            'redirect_to': redirect_to
        }
    elif url:
        body = {
            'success': True,
            'url': url
        }
    elif exception:
        if body is None:
            body = "Unexpected exception %s" % exception
        else:
            body = body % exception
        body = {
            'success': False,
            'errors': [body]
        }
    elif body:
        pass
    else:
        raise Exception("must call with body, errors or redirect_to")

    if status is None:
        status = 200

    if not isinstance(body, str):
        body = json.dumps(body, cls=DjangoJSONEncoder)
    return HttpResponse(body, content_type=content_type, status=status)
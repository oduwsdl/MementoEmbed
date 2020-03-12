import logging
import json
import traceback

import requests_cache

from flask import render_template, request, make_response, Blueprint, current_app
from redis import RedisError

from mementoembed.mementoresource import NotAMementoError, MementoContentError, \
    MementoConnectionError, MementoTimeoutError, MementoInvalidURI, \
    MementoURINotAtArchiveFailure
from mementoembed.textprocessing import TextProcessingError
from .. import getURICache

module_logger = logging.getLogger('mementoembed.services.errors')

def attempt_cache_deletion(urim):

    baduris = ["", None]

    if urim not in baduris:
        getURICache(urim).cache.delete_url(urim)

def handle_errors(function_name, urim, preferences):

    try:
        return function_name(urim, preferences)

    except NotAMementoError as e:
        attempt_cache_deletion(urim)
        module_logger.warning("The submitted URI is not a memento, returning instructions")

        response = make_response(
            json.dumps({
                "urim": urim,
                "content":
                    render_template(
                    'make_your_own_memento.html',
                    urim = urim
                    ),
                "error details": repr(
                    traceback.format_exc())
                }, indent=4))
        response.headers['Content-Type'] = 'application/json'
        return response, 404

    except MementoURINotAtArchiveFailure as e:

        attempt_cache_deletion(urim)
        module_logger.warning("The submitted URI was not successfully located in an archive")

        response = make_response(
            json.dumps({
                "urim": urim,
                "content": e.user_facing_error,
                "response headers": dict(e.response.headers),
                "response status": e.response.status_code,
                "uri submitted": e.response.url,
                "error details": repr(traceback.format_exc())
            }, indent=4))
        response.headers['Content-Type'] = 'application/json'
        return response, 502

    except MementoTimeoutError as e:
        attempt_cache_deletion(urim)
        module_logger.exception("The submitted URI request timed out")
        response = make_response(
            json.dumps({
                "urim": urim,
                "content": e.user_facing_error,
                "error details": repr(traceback.format_exc())
            }, indent=4))
        response.headers['Content-Type'] = 'application/json'
        return response, 504

    except MementoInvalidURI as e:
        # no need to delete from cache, requests will throw an exception again
        # because the URI is invalid
        # attempt_cache_deletion(urim)
        module_logger.exception("The submitted URI is not valid")
        response = make_response(
            json.dumps({
                "urim": urim,
                "content": e.user_facing_error,
                "error details": repr(traceback.format_exc())
            }, indent=4))
        response.headers['Content-Type'] = 'application/json'
        return response, 400

    except MementoConnectionError as e:
        attempt_cache_deletion(urim)
        module_logger.exception("There was a problem connecting to the "
            "submitted URI: {}".format(e.user_facing_error))
        response = make_response(
            json.dumps({
                "urim": urim,
                "content": e.user_facing_error,
                "error details": repr(traceback.format_exc())
            }, indent=4))
        response.headers['Content-Type'] = 'application/json'
        return response, 502

    except (TextProcessingError, MementoContentError) as e:
        attempt_cache_deletion(urim)
        module_logger.exception("There was a problem processing the content of the submitted URI")
        response = make_response(
            json.dumps({
                "urim": urim,
                "content": e.user_facing_error,
                "error details": repr(traceback.format_exc())
            }, indent=4))
        response.headers['Content-Type'] = 'application/json'
        return response, 500

    except RedisError as e:
        attempt_cache_deletion(urim)
        module_logger.exception("A Redis problem has occured")
        response = make_response(
            json.dumps({
                "urim": urim,
                "content": "MementoEmbed could not connect to its database cache, please contact the system owner.",
                "error details": repr(traceback.format_exc())
            }, indent=4))
        response.headers['Content-Type'] = 'application/json'
        return response, 500

    except Exception:
        attempt_cache_deletion(urim)
        module_logger.exception("An unforeseen error has occurred")
        response = make_response(
            json.dumps({
                "urim": urim,
                "content": "An unforeseen error has occurred with MementoEmbed, please contact the system owner.",
                "error details": repr(traceback.format_exc())
            }, indent=4))
        response.headers['Content-Type'] = 'application/json'
        return response, 500

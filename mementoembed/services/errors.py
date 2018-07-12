import logging
import json
import traceback

import requests_cache

from flask import render_template, request, make_response, Blueprint, current_app
from redis import RedisError

from mementoembed.mementoresource import NotAMementoError, MementoContentError, \
    MementoConnectionError, MementoTimeoutError, MementoInvalidURI
from mementoembed.textprocessing import TextProcessingError

module_logger = logging.getLogger('mementoembed.services.errors')

def handle_errors(function_name, urim):

    try:

        return function_name(urim)

    except NotAMementoError as e:
        requests_cache.get_cache().delete_url(urim)
        module_logger.warning("The submitted URI is not a memento, returning instructions")
        return json.dumps({
            "content":
                render_template(
                'make_your_own_memento.html',
                urim = urim
                ),
            "error details": repr(traceback.format_exc())
            }), 404

    except MementoTimeoutError as e:
        requests_cache.get_cache().delete_url(urim)
        module_logger.exception("The submitted URI request timed out")
        return json.dumps({
            "content": e.user_facing_error,
            "error details": repr(traceback.format_exc())
        }, indent=4), 504            

    except MementoInvalidURI as e:
        requests_cache.get_cache().delete_url(urim)
        module_logger.exception("There submitted URI is not valid")
        return json.dumps({
            "content": e.user_facing_error,
            "error details": repr(traceback.format_exc())
        }, indent=4), 400

    except MementoConnectionError as e:
        requests_cache.get_cache().delete_url(urim)
        module_logger.exception("There was a problem connecting to the "
            "submitted URI: {}".format(e.user_facing_error))
        return json.dumps({
            "content": e.user_facing_error,
            "error details": repr(traceback.format_exc())
        }, indent=4), 502

    except (TextProcessingError, MementoContentError) as e:
        requests_cache.get_cache().delete_url(urim)
        module_logger.exception("There was a problem processing the content of the submitted URI")
        return json.dumps({
            "content": e.user_facing_error,
            "error details": repr(traceback.format_exc())
        }, indent=4), 500

    except RedisError as e:
        requests_cache.get_cache().delete_url(urim)
        module_logger.exception("A Redis problem has occured")
        return json.dumps({
            "content": "MementoEmbed could not connect to its database cache, please contact the system owner.",
            "error details": repr(traceback.format_exc())
        }, indent=4), 500

    except Exception:
        requests_cache.get_cache().delete_url(urim)
        module_logger.exception("An unforeseen error has occurred")
        return json.dumps({
            "content": "An unforeseen error has occurred with MementoEmbed, please contact the system owner.",
            "error details": repr(traceback.format_exc())
        }, indent=4), 500

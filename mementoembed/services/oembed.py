import logging
import json
import traceback

import htmlmin
import requests_cache
import dicttoxml

from flask import render_template, request, make_response, Blueprint, current_app
from redis import RedisError

from mementoembed.mementosurrogate import MementoSurrogate
from mementoembed.cachesession import CacheSession
from mementoembed.mementoresource import NotAMementoError, MementoContentError, \
    MementoConnectionError, MementoTimeoutError, MementoInvalidURI
from mementoembed.textprocessing import TextProcessingError
from mementoembed.version import __useragent__

from .socialcard import generate_social_card_html

module_logger = logging.getLogger('mementoembed.services.oembed')

bp = Blueprint('oembed', __name__)

@bp.route('/services/oembed', methods=['GET', 'HEAD'])
def oembed_endpoint():

    try:
        urim = request.args.get("url")
        responseformat = request.args.get("format")
        
        if request.args.get("image") == "no":
            imagechoice = False
        else:
            imagechoice = True

        module_logger.info("Starting oEmbed surrogate creation process")

        # JSON is the default
        if responseformat == None:
            responseformat = "json"

        if responseformat != "json":
            if responseformat != "xml":
                module_logger.error("Requested response format "
                    "is {}, which {} does not "
                    "support".format(responseformat, current_app.name))
                return "The provider cannot return a response in the requested format.", 501

        module_logger.debug("output format will be: {}".format(responseformat))
        
        httpcache = CacheSession(
            timeout=current_app.config['REQUEST_TIMEOUT_FLOAT'],
            user_agent=__useragent__,
            starting_uri=urim
            )
    
        s = MementoSurrogate(
            urim,
            httpcache
        )

        output = {}

        output["type"] = "rich"
        output["version"] = "1.0"

        output["url"] = urim
        output["provider_name"] = s.archive_name
        output["provider_uri"] = s.archive_uri

        urlroot = request.url_root
        urlroot = urlroot if urlroot[-1] != '/' else urlroot[0:-1]

        module_logger.debug("generating oEmbed output for {}".format(urim))
        output["html"] = generate_social_card_html(urim, s, urlroot, imagechoice)

        output["width"] = 500

        #TODO: fix this to the correct height!
        output["height"] = 200

        if responseformat == "json":
            response = make_response(json.dumps(output, indent=4))
            response.headers['Content-Type'] = 'application/json'
        else:
            response = make_response( dicttoxml.dicttoxml(output, custom_root='oembed') )
            response.headers['Content-Type'] = 'text/xml'

        module_logger.info("finished generating {} oEmbed output".format(responseformat))

        response.headers['Access-Control-Origin'] = '*'

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


    return response

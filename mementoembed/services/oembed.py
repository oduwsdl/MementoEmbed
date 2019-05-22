import logging
import json
import traceback

import htmlmin
import requests_cache
import dicttoxml

from flask import render_template, request, make_response, Blueprint, current_app
from redis import RedisError

from mementoembed.mementosurrogate import MementoSurrogate
from mementoembed.sessions import ManagedSession
from mementoembed.mementoresource import NotAMementoError, MementoContentError, \
    MementoConnectionError, MementoTimeoutError, MementoInvalidURI
from mementoembed.textprocessing import TextProcessingError
from mementoembed.version import __useragent__

from .product import generate_social_card_html
from .errors import handle_errors

module_logger = logging.getLogger('mementoembed.services.oembed')

bp = Blueprint('services.oembed', __name__)

def generate_oembed_response(urim):

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
    
    httpcache = ManagedSession(
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

    return response

@bp.route('/services/oembed')
def oembed_endpoint():

    try:
        urim = request.args.get("url")

        baduris = ["", None]

        if urim not in baduris:
            return handle_errors(generate_oembed_response, urim)
        else:
            return """Please submit a url argument.
For example: /services/oembed?url=https://web.archive.org/web/20180515130056/http://www.cs.odu.edu/~mln/""", 400

    except TypeError:
        return """Please submit a url argument.
For example: /services/oembed?url=https://web.archive.org/web/20180515130056/http://www.cs.odu.edu/~mln/""", 400


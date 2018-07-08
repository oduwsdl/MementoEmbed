import sys
import os
import json
import logging
import traceback

import htmlmin
import dicttoxml
import redis
import requests
import requests_cache

from time import strftime

from redis import RedisError
from flask import Flask, request, render_template, make_response
from flask.logging import default_handler

from .cachesession import CacheSession
from .mementosurrogate import MementoSurrogate
from .mementoresource import NotAMementoError, MementoContentError, \
    MementoConnectionError, MementoTimeoutError, MementoInvalidURI
from .textprocessing import TextProcessingError
from .version import __useragent__

application_logger = logging.getLogger(__name__)
access_logger = logging.getLogger('mementoembed_access')

__all__ = [
    "MementoSurrogate"
    ]

class MementoEmbedException(Exception):
    pass

class URIMFilter(logging.Filter):

    def filter(self, record):

        record.urim = "No requested URI"

        try:
            record.urim = request.args.get("url")
        except RuntimeError:
            # just use the defalt message if the flask request object isn't set
            pass
        
        return True

def test_file_access(filename):

    try:
        with open(filename, 'a'):
            os.utime(filename, times=None)
    except Exception as e:
        raise e

def setup_cache(config):

    if 'CACHEENGINE' in config:

        if config['CACHEENGINE'] == 'Redis':

            if 'CACHEHOST' in config:
                dbhost = config['CACHEHOST']
            else:
                dbhost = "localhost"

            if 'CACHEPORT' in config:
                dbport = config['CACHEPORT']
            else:
                dbport = "6379"

            if 'CACHEDB' in config:
                dbno = config['CACHEDB']
            else:
                dbno = "0"

            if 'CACHE_EXPIRETIME' in config:
                expiretime = int(config['CACHE_EXPIRETIME'])
            else:
                expiretime = 7 * 24 * 60 * 60

            application_logger.info("Using Redis as cache engine with host={}, "
                "port={}, database_number={}, and expiretime={}".format(
                    dbhost, dbport, dbno, expiretime
                ))

            try:
                rconn = redis.StrictRedis(host=dbhost, port=dbport, db=dbno)

                rconn.set("mementoembed_test_key", "success")
                rconn.delete("mementoembed_test_key")

            except redis.exceptions.RedisError as e:
                application_logger.exception("Logging exception in redis database setup")
                application_logger.critical("The Redis database settings are invalid, the application cannot continue")
                raise e

            requests_cache.install_cache('mementoembed', backend='redis', 
                expire_after=expiretime, connection=rconn)

        elif config['CACHEENGINE'] == 'SQLite':

            if 'CACHE_FILENAME' in config:
                cachefile = config['CACHE_FILENAME']
            else:
                cachefile = "mementoembed"

            application_logger.info("Setting up SQLite as cache engine with "
                "file named {}".format(cachefile))

            try:
                test_file_access("{}.sqlite".format(cachefile))
                requests_cache.install_cache(cachefile)
                application_logger.info("SQLite cache file {}.sqlite is writeable".format(cachefile))
            except Exception as e:
                application_logger.critical("SQLite cache file {}.sqlite is NOT WRITEABLE, "
                    "the application cannot continue".format(cachefile))
                raise e

        else:

            application_logger.info("With no other supported cache engines detected, "
                "setting up SQLite as cache engine with file named 'mementoembed'")

            requests_cache.install_cache('mementoembed_cache')

    else:
        requests_cache.install_cache('mementoembed')

    application_logger.info("Application request web cache has been successfuly configured")

def get_requests_timeout(config):

    if 'REQUEST_TIMEOUT' in config:
        try:
            timeout = float(config['REQUEST_TIMEOUT'])
        except Exception as e:
            application_logger.exception("REQUEST_TIMEOUT value is invalid")
            application_logger.critical("REQUEST_TIMEOUT value '{}' is invalid, "
                "application cannot continue".format(config['REQUEST_TIMEOUT']))
            raise e
    else:
        timeout = 20.0

    return timeout

def setup_logging_config(config):

    logfile = None
    
    if 'APPLICATION_LOGLEVEL' in config:
        loglevel = logging._nameToLevel[config['APPLICATION_LOGLEVEL']]

    else:
        loglevel = logging.INFO

    application_logger.setLevel(loglevel)
    application_logger.info("Logging with level {}".format(loglevel))

    if 'APPLICATION_LOGFILE' in config:
        logfile = config['APPLICATION_LOGFILE']

        try:
            test_file_access(logfile) # should throw if file is invalid

            if loglevel == logging.DEBUG:
                formatter = logging.Formatter(
                    '[%(asctime)s {} ] - %(levelname)s - [ %(urim)s ]: %(name)s - %(message)s'.format(
                        strftime('%z')
                    ))
            else:
                formatter = logging.Formatter(
                    '[%(asctime)s {} ] - %(levelname)s - [ %(urim)s ]: %(message)s'.format(
                        strftime('%z')
                    ))

            fh = logging.FileHandler(logfile)
            fh.addFilter(URIMFilter())
            fh.setLevel(loglevel)
            fh.setFormatter(formatter)
            application_logger.addHandler(fh)
            application_logger.info("=== Starting application ===")
            application_logger.info("Writing application log to file {} with level {}".format(
                logfile, logging.getLevelName(loglevel)))

        except Exception as e:
            message = "Cannot write to requested application logfile {}, " \
                "the application cannot continue".format(logfile)
            application_logger.critical(message)
            raise e

    formatter = logging.Formatter('%(message)s')

    if 'ACCESS_LOGFILE' in config:
        logfile = config['ACCESS_LOGFILE']

        try:
            test_file_access(logfile) # should throw if file is invalid

            handler = logging.FileHandler(logfile)
            handler.setFormatter(formatter)
            access_logger.addHandler(handler)
            access_logger.setLevel(logging.INFO)

            application_logger.info("Writing access log to {}".format(logfile))

        except Exception as e:
            message = "Cannot write to requested access logfile {}, " \
                "the application cannot continue".format(logfile)
            application_logger.exception(message)
            application_logger.critical(message)
            raise e

    application_logger.info("Logging has been successfully configured")

def create_app():

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('config.default')
    app.config.from_pyfile('application.cfg', silent=True)
    app.config.from_pyfile("/etc/mementoembed.cfg", silent=True)

    setup_logging_config(app.config)
    setup_cache(app.config)

    timeout = get_requests_timeout(app.config)

    application_logger.info("Requests timeout is set to {}".format(timeout))
    application_logger.info("All Configuration successfully loaded for MementoEmbed")
    application_logger.info("MementoEmbed is now initialized and ready to receive requests")

    #pylint: disable=unused-variable
    @app.after_request
    def after_request(response):

        ts = strftime('[%d/%b/%Y:%H:%M:%S %z]')

        # this should be the only place where access_logger is used
        access_logger.info(
            '%s - - %s %s %s %s',
            request.remote_addr,
            ts,
            request.method,
            request.full_path,
            response.status
        )

        return response

    #pylint: disable=unused-variable
    @app.route('/', methods=['GET', 'HEAD'])
    def front_page():
        return render_template('index.html')

    #pylint: disable=unused-variable
    @app.route('/services/oembed', methods=['GET', 'HEAD'])
    def oembed_endpoint():

        try:
            urim = request.args.get("url")
            responseformat = request.args.get("format")

            application_logger.info("Starting oEmbed surrogate creation process")

            # JSON is the default
            if responseformat == None:
                responseformat = "json"

            if responseformat != "json":
                if responseformat != "xml":
                    application_logger.error("Requested response format "
                        "is {}, which {} does not "
                        "support".format(responseformat, app.name))
                    return "The provider cannot return a response in the requested format.", 501

            application_logger.debug("output format will be: {}".format(responseformat))
            
            httpcache = CacheSession(
                timeout=timeout,
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

            application_logger.debug("generating oEmbed output for {}".format(urim))
            output["html"] = htmlmin.minify( render_template(
                "social_card.html",
                urim = urim,
                urir = s.original_uri,
                image = s.striking_image,
                archive_uri = s.archive_uri,
                archive_favicon = s.archive_favicon,
                archive_collection_id = s.collection_id,
                archive_collection_uri = s.collection_uri,
                archive_collection_name = s.collection_name,
                archive_name = s.archive_name,
                original_favicon = s.original_favicon,
                original_domain = s.original_domain,
                original_link_status = s.original_link_status,
                surrogate_creation_time = s.creation_time,
                memento_datetime = s.memento_datetime,
                me_title = s.title,
                me_snippet = s.text_snippet,
                server_domain = urlroot
            ), remove_empty_space=True, 
            remove_optional_attribute_quotes=False )

            output["width"] = 500

            #TODO: fix this to the correct height!
            output["height"] = 200

            if responseformat == "json":
                response = make_response(json.dumps(output, indent=4))
                response.headers['Content-Type'] = 'application/json'
            else:
                response = make_response( dicttoxml.dicttoxml(output, custom_root='oembed') )
                response.headers['Content-Type'] = 'text/xml'

            application_logger.info("finished generating {} oEmbed output".format(responseformat))

        except NotAMementoError as e:
            requests_cache.get_cache().delete_url(urim)
            application_logger.warning("The submitted URI is not a memento, returning instructions")
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
            application_logger.exception("The submitted URI request timed out")
            return json.dumps({
                "content": e.user_facing_error,
                "error details": repr(traceback.format_exc())
            }, indent=4), 504            

        except MementoInvalidURI as e:
            requests_cache.get_cache().delete_url(urim)
            application_logger.exception("There submitted URI is not valid")
            return json.dumps({
                "content": e.user_facing_error,
                "error details": repr(traceback.format_exc())
            }, indent=4), 400

        except MementoConnectionError as e:
            requests_cache.get_cache().delete_url(urim)
            application_logger.exception("There was a problem connecting to the "
                "submitted URI: {}".format(e.user_facing_error))
            return json.dumps({
                "content": e.user_facing_error,
                "error details": repr(traceback.format_exc())
            }, indent=4), 502

        except (TextProcessingError, MementoContentError) as e:
            requests_cache.get_cache().delete_url(urim)
            application_logger.exception("There was a problem processing the content of the submitted URI")
            return json.dumps({
                "content": e.user_facing_error,
                "error details": repr(traceback.format_exc())
            }, indent=4), 500

        except RedisError as e:
            requests_cache.get_cache().delete_url(urim)
            application_logger.exception("A Redis problem has occured")
            return json.dumps({
                "content": "MementoEmbed could not connect to its database cache, please contact the system owner.",
                "error details": repr(traceback.format_exc())
            }, indent=4), 500

        except Exception:
            requests_cache.get_cache().delete_url(urim)
            application_logger.exception("An unforeseen error has occurred")
            return json.dumps({
                "content": "An unforeseen error has occurred with MementoEmbed, please contact the system owner.",
                "error details": repr(traceback.format_exc())
            }, indent=4), 500


        return response

    return app

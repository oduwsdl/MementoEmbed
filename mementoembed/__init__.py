import sys
import os
import json
import logging

import redis
import requests
import requests_cache

from time import strftime

from redis import RedisError
from flask import Flask, request, render_template, make_response

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

    app.config['REQUEST_TIMEOUT_FLOAT'] = get_requests_timeout(app.config)

    application_logger.info("Requests timeout is set to {}".format(app.config['REQUEST_TIMEOUT_FLOAT']))
    application_logger.info("All Configuration successfully loaded for MementoEmbed")
    application_logger.info("MementoEmbed is now initialized and ready to receive requests")

    from mementoembed.services import oembed, memento, socialcard
    app.register_blueprint(oembed.bp)
    app.register_blueprint(memento.bp)
    app.register_blueprint(socialcard.bp)

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
        return render_template('index.html', pagetitle = "MementoEmbed")

    @app.route('/about/', methods=['GET', 'HEAD'])
    def about_page():
        return render_template('about.html', pagetitle = "MementoEmbed")

    @app.route('/generate/socialcard/', methods=['GET', 'HEAD'])
    def generate_social_card():
        return render_template('generate_social_card.html', 
            pagetitle="MementoEmbed - Generate a Social Card",
            surrogate_type="Social Card",
            baseuri="/generate/socialcard/",
            oembed_endpoint="/services/oembed?&format=json&url="
        )

    @app.route('/generate/socialcardnoimage/', methods=['GET', 'HEAD'])
    def generate_social_card_wo_image():
        return render_template('generate_social_card.html', 
            pagetitle="MementoEmbed - Generate a Social Card without an Image",
            surrogate_type="Social Card without Image",
            baseuri="/generate/socialcardnoimage/",
            oembed_endpoint="/services/oembed?&image=no&format=json&url="
        )

    #pylint: disable=unused-variable


    return app

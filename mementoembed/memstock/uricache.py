import sqlite3
import json
import logging
import datetime

from sqlite3 import OperationalError, ProgrammingError

import requests

from requests.structures import CaseInsensitiveDict

module_logger = logging.getLogger('mementoembed.memstock.uricache')

# TODO: create minimal response object

# timeout
# retries
# referrer
# accept-encoding

class URICacheError(Exception):
    pass

class URINotInCacheError(URICacheError):
    pass

def create_uricache_table(dbconn):

    query = '''CREATE TABLE URICACHE (
            uri TEXT,
            request_headers TEXT,
            response_status INTEGER,
            response_headers TEXT,
            response_content BLOB, 
            observation_datetime TIMESTAMP)'''

    dbconn.execute(query)
    dbconn.commit()

def uri_exists_already(uri, dbconn):

    exists = False

    try:
        get_uri_timestamp(uri, dbconn)
        exists = True
    except URINotInCacheError:
        pass

    return exists

def purgeuri(uri, dbconn):

    try:
        query = "DELETE FROM URICACHE WHERE URI == ?"
        queryargs = (uri, )
        c = dbconn.cursor()
        c.execute(query, queryargs)
        dbconn.commit()

    except (OperationalError, ProgrammingError) as e:
        module_logger.exception("Database error for uri: {}".format(uri))
        raise e

def purgeuri_if_expired(uri, dbconn, expiration_delta):

    if (datetime.datetime.now() - get_uri_timestamp(uri, dbconn)) > expiration_delta:
        purgeuri(uri, dbconn)

def saveuri(uri, dbconn, session=None, headers={}, expiration_delta=None):

    if session is None:
        session = requests.Session()

    if expiration_delta is not None:
        purgeuri_if_expired(uri, dbconn, expiration_delta)

    try:
        r = session.get(uri)

        query = "INSERT INTO URICACHE " \
            "(uri, request_headers, response_status, response_headers, " \
            "response_content, observation_datetime) " \
            "VALUES(?, ?, ?, ?, ?, ?)"
        queryargs = (
            uri, 
            json.dumps(dict(r.request.headers)), 
            r.status_code, 
            json.dumps(dict(r.headers)),
            r.content, 
            datetime.datetime.now()
            )

        c = dbconn.cursor()
        c.execute(query, queryargs)
        dbconn.commit()

    except (OperationalError, ProgrammingError) as e:
        module_logger.exception("Database error for uri: {}".format(uri))
        raise e
    
def get_uri_response_body(uri, dbconn):

    query = "SELECT response_content FROM URICACHE WHERE URI == ?"
    queryargs = (uri, )
    c = dbconn.cursor()
    c.execute(query, queryargs)

    records = c.fetchall()

    if len(records) == 1:
        return records[0][0]
    else:
        raise URINotInCacheError("This URI is not in the cache: {}".format(uri))

def get_uri_response_headers(uri, dbconn):

    query = "SELECT response_headers FROM URICACHE WHERE URI == ?"
    queryargs = (uri, )
    c = dbconn.cursor()
    c.execute(query, queryargs)

    records = c.fetchall()

    if len(records) == 1:
        return CaseInsensitiveDict(json.loads(records[0][0]))
    else:
        raise URINotInCacheError("This URI is not in the cache: {}".format(uri))

def get_uri_timestamp(uri, dbconn):

    query = "SELECT observation_datetime FROM URICACHE WHERE URI == ?"
    queryargs = (uri, )
    c = dbconn.cursor()
    c.execute(query, queryargs)

    records = c.fetchall()

    if len(records) == 1:

        timestamp = records[0][0]
        
        if type(timestamp) == str:
            return datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
        else:
            return timestamp
    else:
        raise URINotInCacheError("This URI is not in the cache: {}".format(uri))

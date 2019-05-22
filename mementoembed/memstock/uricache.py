import sqlite3
import json
import logging
import datetime

from sqlite3 import OperationalError, ProgrammingError

import requests
from requests.models import Response
from requests.structures import CaseInsensitiveDict

module_logger = logging.getLogger('mementoembed.memstock.uricache')

# this whole implementation exists because requests_cache
# would occasionally return incorrect content for a URI
# and I could not determine why

# timeout
# retries

class URICacheError(Exception):
    pass

class URINotInCacheError(URICacheError):
    pass

def dbtable_exists_already(dbconn):

    query = '''SELECT name from sqlite_master where type="table"'''

    c = dbconn.cursor()
    c.execute(query, ())

    records = c.fetchall()

    if len(records) == 1:
        return records[0][0] == "URICACHE"
    else:
        return False

def create_uricache_table(dbconn):

    query = '''CREATE TABLE URICACHE (
            uri TEXT,
            request_headers TEXT,
            request_method TEXT,
            response_status INTEGER,
            response_reason TEXT,
            response_elapsed INTEGER,
            response_headers TEXT,
            response_encoding TEXT,
            response_history TEXT,
            response_content BLOB, 
            observation_datetime TIMESTAMP)'''

    dbconn.execute(query)
    dbconn.commit()

def uri_exists_already(uri, dbconn):

    exists = False

    try:
        get_uri_datafield(uri, dbconn, 'observation_datetime')
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

    if (datetime.datetime.now() - get_uri_datafield(uri, dbconn, 'observation_datetime')) > expiration_delta:
        purgeuri(uri, dbconn)

def saveuri(uri, dbconn, session, expiration_delta=None):

    if expiration_delta is not None:
        purgeuri_if_expired(uri, dbconn, expiration_delta)

    try:
        r = session.get(uri)

        query = '''INSERT INTO URICACHE (
                uri, 
                request_headers,
                request_method,
                response_status,
                response_reason,
                response_elapsed,
                response_headers,
                response_encoding,
                response_history,
                response_content,
                observation_datetime
            ) VALUES(
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?)'''
        queryargs = (
            uri,
            json.dumps(dict(r.request.headers)),
            r.request.method,
            r.status_code,
            r.reason,
            r.elapsed.microseconds,
            json.dumps(dict(r.headers)),
            r.encoding,
            json.dumps(r.history),
            r.content, 
            datetime.datetime.utcnow()
            )

        c = dbconn.cursor()
        c.execute(query, queryargs)
        dbconn.commit()

    except (OperationalError, ProgrammingError) as e:
        module_logger.exception("Database error for uri: {}".format(uri))
        raise e

def get_uri_datafield(uri, dbconn, field):

    query = "SELECT {} from URICACHE WHERE URI == ?".format(field)
    queryargs = (uri,)
    c = dbconn.cursor()
    c.execute(query, queryargs)

    records = c.fetchall()

    if len(records) == 1:
        return records[0][0]
    else:
        raise URINotInCacheError("This URI is not in the cache: {}".format(uri))

class URICache:

    def __init__(self, dbname, session, expiration_delta):

        self.dbconn = sqlite3.connect(dbname)
        self.session = session
        self.expiration_delta = expiration_delta

        if dbtable_exists_already(self.dbconn) == False:
            create_uricache_table(self.dbconn)

    def get(self, uri, headers={}, timeout=None):

        if not uri_exists_already(uri, self.dbconn):
            saveuri(uri, self.dbconn, session=self.session)

        req_headers = CaseInsensitiveDict(json.loads(get_uri_datafield(uri, self.dbconn, 'request_headers')))
        req_method = get_uri_datafield(uri, self.dbconn, 'request_method')
        request = requests.Request(req_method, uri, headers=req_headers)
        request.prepare()

        response = Response()
        response.request = request
        response.status_code = get_uri_datafield(uri, self.dbconn, 'response_status')
        response.reason = get_uri_datafield(uri, self.dbconn, 'response_reason')
        response.elapsed = datetime.timedelta(microseconds=get_uri_datafield(uri, self.dbconn, 'response_elapsed'))
        response.encoding = get_uri_datafield(uri, self.dbconn, 'response_encoding')
        response.history = json.loads(get_uri_datafield(uri, self.dbconn, 'response_history'))
        response.headers = CaseInsensitiveDict(json.loads(get_uri_datafield(uri, self.dbconn, 'response_headers')))
        response._content = get_uri_datafield(uri, self.dbconn, 'response_content')
        response.url = uri

        return response

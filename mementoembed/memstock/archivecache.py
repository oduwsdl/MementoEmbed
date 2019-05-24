import sqlite3
import logging
import datetime

from sqlite3 import OperationalError, ProgrammingError

module_logger = logging.getLogger('mementoembed.memstock.uricache')

class ArchiveCacheError(Exception):
    pass

class ArchiveNotInCacheError(ArchiveCacheError):
    pass

def dbtable_exists_already(dbconn):

    query = '''SELECT name from sqlite_master where type="table"'''

    c = dbconn.cursor()
    c.execute(query, ())

    records = c.fetchall()

    if len(records) == 1:
        return records[0][0] == "ARCHIVECACHE"
    else:
        return False

def create_archivecache_table(dbconn):

    query = '''CREATE TABLE ARCHIVECACHE (
            archivename TEXT,
            archivefavicon TEXT,
            observation_datetime TIMESTAMP)'''

    dbconn.execute(query)
    dbconn.commit()

def get_record_datafield(key, keyfield, queryfield, dbconn, tablename):

    query = "SELECT {} from {} WHERE URI == ?".format(tablename, queryfield)
    queryargs = (key,)
    c = dbconn.cursor()
    c.execute(query, queryargs)

    records = c.fetchall()

    if len(records) == 1:
        return records[0][0]
    else:
        raise ArchiveNotInCacheError("This URI is not in the cache: {}".format(key)) 

def archive_exists_already(archivename, dbconn):

    exists = False

    try:
        get_record_datafield(archivename, "archivename", 'observation_datetime', dbconn, "ARCHVIECACHE")
        exists = True
    except ArchiveNotInCacheError:
        pass

    return exists

def purgerecord(key, keyfield, dbconn, tablename):

    try:
        query = "DELETE FROM {} WHERE {} == ?".format(tablename, keyfield)
        queryargs = (key, )
        c = dbconn.cursor()
        c.execute(query, queryargs)
        dbconn.commit()

    except (OperationalError, ProgrammingError) as e:
        module_logger.exception("Database error for {}: {}".format(keyfield, key))
        raise e

def purgerecord_if_expired(key, keyfield, dbconn, tablename, expiration_delta):

    if (datetime.datetime.now() - get_record_datafield(
        key, keyfield, 'observation_datetime', dbconn, tablename)) > expiration_delta:
        purgerecord(key, keyfield, dbconn, tablename)

def savearchive(archivename, dbconn, expiration_delta=None):

    if expiration_delta is not None:
        purgerecord_if_expired(archivename, 'archivename', dbconn, 'ARCHIVECACHE', expiration_delta)

    try:
        query = '''INSERT INTO ARCHIVECACHE (
            archivename,
            archivefavicon
        )
    except (OperationalError, ProgrammingError) as e:
        module_logger.exception("Database error for uri: {}".format(uri))
        raise e

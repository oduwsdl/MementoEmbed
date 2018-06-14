import os
import shutil
import json
import unittest
import logging
import glob
import subprocess
import calendar
import time

import requests
import chardet

from datetime import datetime, timedelta
from email.utils import formatdate

from cachecontrol import CacheControl
from cachecontrol.heuristics import BaseHeuristic
from cachecontrol.caches.file_cache import FileCache

from mementoembed import MementoSurrogate

working_dir = "/tmp/mementoembed/{}".format(
    os.path.basename(os.path.realpath(__file__))
)

thisdir = os.path.dirname(os.path.realpath(__file__))

class AlwaysUseCacheWhenPossibleHeuristic(BaseHeuristic):

    def update_headers(self, response):

        # expires = datetime.now() + timedelta(weeks=1)

        return {
            # 'expires': formatdate(calendar.timegm(expires.timetuple())),
            'expires': formatdate(calendar.timegm(
                time.struct_time(tm_year=3000, tm_mon=1, tm_mday=1, tm_hour=0, tm_min=0, tm_sec=0)
                )
                ),
            'cache-control' : 'public'
        }

    def warning(self, response):

        msg = 'Automatically cached! Response is Stale.'
        return '110 - "%s"' % msg

class TestMementoSurrogate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        if not os.path.exists(working_dir):
            os.makedirs(working_dir)
            # shutil.copy()


    @classmethod
    def tearDownClass(cls):

        # subprocess.call( [ "{}/savecache.sh".format(thisdir) ] )
        pass

    def test_surrogate(self):

        logger = logging.getLogger(__name__)

        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            level=logging.INFO,
            filename='fetch_surrogate.log'
        )

        # 1. load the data for known responses for testing

        testingdir = "{}".format(
            os.path.dirname(os.path.realpath(__file__))
        )

        testfiles = glob.glob("{}/expected_results/mementosurrogate_results_*.json".format(
            testingdir
        ))

        # because some mementos are different character sets, we can't all treat them the same
        for testdatafile in testfiles:

            print("testing data in data file {}".format(testdatafile))

            with open(testdatafile, 'rb') as f:
                data = f.read()

            cd = chardet.detect(data)

            print("decoding data as type {}".format(cd['encoding']))

            testdata = json.loads(data.decode(cd['encoding']))

            # 2. ensure that you use the local test cache file for HTTP responses

            # TODO: copy an existing zipped cache file to this destination and unzip it for use
            cachingdir = "{}/testcache".format(working_dir)

            print("caching dir is now {}".format(cachingdir))

            forever_cache = FileCache(cachingdir, forever=True)
            sess = CacheControl(requests.Session(), forever_cache) #, heuristic=AlwaysUseCacheWhenPossibleHeuristic)

            # 3. run the code, test the results against expected results

            urim = testdata["urim"]
        
            expected_results = testdata["expected results"]
            print("just loaded expected results")

            #pylint: disable=unused-variable
            ms = MementoSurrogate(urim, session=sess, 
                working_directory=working_dir, logger=logger)

            for method in expected_results:
                
                func = "ms.{}".format(method)

                if method == "memento_datetime":
                    result = eval(func).strftime("%Y-%m-%dT%H:%M:%SZ")
                else:
                    result = eval(func)

                # 4. profit!
                self.assertEqual(result, expected_results[method], "method {} failed".format(method))

            sess.close()
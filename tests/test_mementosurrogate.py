import os
import json
import unittest
import logging
import glob

import requests
import chardet

from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache

from mementoembed import MementoSurrogate

class TestMementoSurrogate(unittest.TestCase):

    def test_surrogate(self):

        logger = logging.getLogger(__name__)

        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            level=logging.INFO,
            filename='fetch_surrogate.log'
        )

        # 1. load the data for known responses for testing

        working_dir = "/tmp/mementoembed/{}".format(
            os.path.basename(__file__)
        )

        if not os.path.exists(working_dir):
            os.makedirs(working_dir)

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
            sess = CacheControl(requests.Session(), forever_cache)

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
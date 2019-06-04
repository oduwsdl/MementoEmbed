import unittest
import os
import csv

import requests

class TestSimpleMementoEmbedEndpoints(unittest.TestCase):

    def test_battery_happy_path(self):

        batteryfilename = "{}/battery_data.csv".format(
            os.path.dirname(os.path.realpath(__file__)
            ))

        def test_service(endpoint, datarow):

            urim = datarow['urim']

            r = requests.get("{}{}".format(endpoint, urim))

            self.assertEqual(r.status_code, 200)

            data = r.json()

            self.assertEqual(data['urim'], urim)
            self.assertIn("generation-time", data)

            for field in r.json():

                if field not in ['urim', 'generation-time', 'snippet']:

                    if datarow[field] == '':
                        self.assertEqual(data[field], None)
                    else:
                        self.assertEqual(data[field], datarow[field])


        with open(batteryfilename) as f:
            reader = csv.DictReader(f)

            for row in reader:

                print("testing with URI-M {}".format(row['urim']))

                test_service("http://localhost:5000/services/memento/contentdata/", row)
                test_service("http://localhost:5000/services/memento/bestimage/", row)
                test_service("http://localhost:5000/services/memento/archivedata/", row)
                test_service("http://localhost:5000/services/memento/originalresourcedata/", row)

        

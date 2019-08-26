import unittest
import os
import csv

import requests

class TestSimpleMementoEmbedEndpoints(unittest.TestCase):

    def test_battery_happy_path(self):

        batteryfilename = "{}/battery_data.csv".format(
            os.path.dirname(os.path.realpath(__file__)
            ))

        serviceport = "5550"

        configured_serviceport = os.getenv('TESTPORT')

        if configured_serviceport is not None:
            serviceport = configured_serviceport

        assertionerrors = []

        def test_service(endpoint, datarow):

            urim = datarow['urim']

            service_uri = "{}{}".format(endpoint, urim)

            r = requests.get(service_uri)

            print("testing service URI {}".format(service_uri))

            data = r.json()

            try:
                self.assertEqual(r.status_code, 200, "status code was not 200 for URI-M {} at endpoint {}".format(urim, endpoint))
                self.assertEqual(data['urim'], urim, msg="failed to match given URI-M of {} at endpoint {}".format(urim, endpoint))
                self.assertIn("generation-time", data, msg="generation-time field is not present for URI-M {} at endpoint {}".format(urim, endpoint))

                for field in r.json():

                    if field not in ['urim', 'generation-time', 'snippet', 'metadata']:

                        try:

                            if datarow[field] == '':
                                self.assertEqual(data[field], None, msg="failed for field {}".format(field))
                            else:
                                self.assertEqual(data[field], datarow[field], msg="failed for field {}".format(field))

                        except AssertionError as e:
                            print("Failed with URI-M {} for field {} at endpoint {}".format(urim, field, endpoint))
                            print("exception: {}".format(e))
                            assertionerrors.append(e)

                        except KeyError as e:
                            assertionerrors.append(e)

            except AssertionError as e:
                assertionerrors.append(e)


        with open(batteryfilename) as f:
            reader = csv.DictReader(f)

            for row in reader:

                print("testing with URI-M {}".format(row['urim']))

                test_service("http://localhost:{}/services/memento/contentdata/".format(serviceport), row)
                test_service("http://localhost:{}/services/memento/bestimage/".format(serviceport), row)
                test_service("http://localhost:{}/services/memento/archivedata/".format(serviceport), row)
                test_service("http://localhost:{}/services/memento/originalresourcedata/".format(serviceport), row)
                test_service("http://localhost:{}/services/memento/seeddata/".format(serviceport), row)

            if len(assertionerrors) > 0:
                self.fail("one or more inputs failed a test")
        

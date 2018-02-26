#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import json
import unittest

sys.path.insert(0, '..')

from enigma2_http_api.controller import ServiceLookupController
from enigma2_http_api.utils import NS_DVB_C, NS_DVB_S, NS_DVB_T

TD = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../contrib/testdata'))


class ServiceLookupControllerTestCase(unittest.TestCase):
    def setUp(self):
        filename = os.path.join(TD, "getallservices.json")
        with open(filename, "rb") as src:
            data = json.load(src)
        self.slc = ServiceLookupController(data)

    def testDictLikeLookup(self):
        with self.assertRaises(Exception) as context:
            self.slc["Sky Atlantic HD"]

        self.assertTrue('Sky Atlantic HD' in context.exception)

    def testDictLikeLookupTuples(self):
        result = self.slc.lookup_service('Sky Atlantic HD', NS_DVB_C)
        self.assertEqual('1:0:19:6e:d:85:ffff0000:0:0:0:', result)

        result2 = self.slc.lookup_service('Sky Atlantic HD', NS_DVB_S)
        self.assertEqual('1:0:19:6e:d:85:00c00000:0:0:0:', result2)

        with self.assertRaises(Exception) as context:
            self.slc.lookup_service("Sky Atlantic HD", NS_DVB_T)

        self.assertTrue(("Sky Atlantic HD", NS_DVB_T) in context.exception)


if __name__ == '__main__':
    unittest.main()

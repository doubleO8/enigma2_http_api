#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import json
import unittest
import glob
import datetime

sys.path.insert(0, '..')

from enigma2_http_api.utils import pseudo_unique_id, SERVICE_TYPE_RADIO
from enigma2_http_api.utils import pseudo_unique_id_any
from enigma2_http_api.utils import parse_servicereference
from enigma2_http_api.model import EEvent

TD = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../contrib/testdata'))


class PseudoIDTestCase(unittest.TestCase):
    maxDiff = None

    def _load_raw(self, filename):
        with open(filename, "r") as src:
            data = json.load(src)
        return data

    def setUp(self):
        self.raw = {}
        self.globme = TD + '/*.json'
        for filename in glob.glob(self.globme):
            (trunk, _) = os.path.splitext(os.path.basename(filename))
            self.raw[trunk] = self._load_raw(filename)

    def testSprechstundeDatasets(self):
        events = [EEvent(x) for x in self.raw['sprechstunde']]
        self.assertEqual(4, len(events))
        self.assertNotEqual(None, events[0].pseudo_id)

        for item in events:
            psr = parse_servicereference(item.service_reference)
            self.assertTrue((psr['service_type'] == SERVICE_TYPE_RADIO))

        self.assertEqual('38d97fdaad3c1d2c495ff0135869eb1aabdab336',
                         events[0].pseudo_id)
        self.assertEqual('dedd36e94f4a8521a810e8438327de2d8357e720',
                         events[1].pseudo_id)
        self.assertEqual('fbc5da506f991ac6c96fea98a8e923dfb10b83d1',
                         events[2].pseudo_id)
        self.assertEqual('47a1be2837d5cce375c544824322f2c07bdd8c2c',
                         events[3].pseudo_id)

    def testMusikstundeDatasets(self):
        events = [EEvent(x) for x in self.raw['musikstunde']]
        self.assertEqual(24, len(events))
        self.assertNotEqual(None, events[0].pseudo_id)

        for item in events:
            psr = parse_servicereference(item.service_reference)
            self.assertTrue((psr['service_type'] == SERVICE_TYPE_RADIO))

        self.assertEqual(pseudo_unique_id_any(events[0]), events[0].pseudo_id)

    def testOrangeDatasets(self):
        events = [EEvent(x) for x in self.raw['orange']]
        self.assertEqual(8, len(events))
        self.assertNotEqual(None, events[4].pseudo_id)

        for item in events:
            psr = parse_servicereference(item.service_reference)
            self.assertFalse((psr['service_type'] == SERVICE_TYPE_RADIO))

    def testGOTDatasets(self):
        events = [EEvent(x) for x in self.raw['got']]
        self.assertEqual(4, len(events))
        self.assertNotEqual(None, events[0].pseudo_id)
        for item in events:
            self.assertEqual(pseudo_unique_id(item), item.pseudo_id)
            psr = parse_servicereference(item.service_reference)
            self.assertFalse((psr['service_type'] == SERVICE_TYPE_RADIO))

    def testMovielistDatasets(self):
        events = [EEvent(x) for x in self.raw['movielist']['movies']]
        self.assertEqual(3, len(events))

        self.assertEqual("2017-09-21_20:55",
                         events[0].start_time.strftime("%Y-%m-%d_%H:%M"))
        self.assertEqual(datetime.timedelta(0, 7778), events[0].duration)
        self.assertEqual(2962768356996390958, events[0].item_id)
        self.assertEqual(None, events[0].pseudo_id)

        self.assertEqual("2017-09-17_23:55",
                         events[1].start_time.strftime("%Y-%m-%d_%H:%M"))
        self.assertEqual(datetime.timedelta(0, 7787), events[1].duration)
        self.assertEqual(6059448549813246681, events[1].item_id)
        self.assertEqual('SPUTNIK Black Beatz - Wiederholung', events[1].title)
        self.assertTrue(events[1].longinfo.startswith(
            "Feinster R'n'B, tighter"))

        self.assertEqual("2017-08-30_16:50",
                         events[2].start_time.strftime("%Y-%m-%d_%H:%M"))
        self.assertEqual(datetime.timedelta(), events[2].duration)
        self.assertEqual(events[2].start_time, events[2].stop_time)
        self.assertEqual(-5676678663366908110, events[2].item_id)

        for item in events[1:]:
            self.assertEqual(pseudo_unique_id(item), item.pseudo_id)


if __name__ == '__main__':
    unittest.main()

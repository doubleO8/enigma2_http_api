#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
import pprint
import logging
import datetime
import tempfile

REMOTE_ADDR = os.environ.get('ENIGMA2_HTTP_API_HOST')

import pytz

from enigma2_http_api.controller import Enigma2APIController
from enigma2_http_api.utils import filter_simple_events

logging.basicConfig(level=logging.DEBUG)

LOG = logging.getLogger("eha-examples")

LOCALTIMEZONE = pytz.timezone("Europe/Berlin")


def demo_search(what='Jahrhundert'):
    pprint.pprint(EAC.get_search(what))


def demo_about():
    pprint.pprint(EAC.get_about())


def demo_subservices():
    pprint.pprint(EAC.get_subservices())


def demo_services():
    pprint.pprint(EAC.get_services())


def demo_allservices():
    pprint.pprint(EAC.get_getallservices())

def demo_list_timers():
    timerlist = EAC.get_timerlist()

    dump_keys = ['begin', 'end', 'startprepare', 'realbegin', 'realend']
    for item in timerlist:
        for key in dump_keys:
            print("{:s}: {!s}".format(key, item[key]))
            try:
                dt_obj = datetime.datetime.fromtimestamp(item[key])
                if dt_obj.tzinfo is None:
                    dt_obj = LOCALTIMEZONE.localize(dt_obj)
                print(' ({!s})'.format(dt_obj.strftime('%Y-%m-%d %H:%M %z %Z')))
            except TypeError:
                pass
        pprint.pprint(item)


def demo_movielist():
    for item in EAC.get_movielist()['movies']:
        pprint.pprint(item)


def demo_zap_and_list_epg():
    services = EAC.get_services()
    # LOG.info(pprint.pformat(services))
    bouquet_reference = services[1][1]

    LOG.info(pprint.pformat(EAC.get_epgbouquet(bouquet_ref=bouquet_reference,
                                               filter_func=filter_simple_events)))

    fox_hd_s = '1:0:19:7C:6:85:FFFF0000:0:0:0:'
    LOG.info(pprint.pformat(EAC.get_zap(fox_hd_s)))
    LOG.info(pprint.pformat(
        EAC.get_epgservice(fox_hd_s, filter_func=filter_simple_events)))


if __name__ == '__main__':
    if not REMOTE_ADDR:
        sys.exit(-1)
    DUMP_REQUESTS = tempfile.mkdtemp()
    print("REMOTE_ADDR={!s}, DUMP_REQUESTS={!s}".format(REMOTE_ADDR, DUMP_REQUESTS))
    EAC = Enigma2APIController(remote_addr=REMOTE_ADDR, dump_requests=DUMP_REQUESTS)

    demo_search()
    demo_about()
    demo_subservices()
    demo_services()
    demo_allservices()
    demo_list_timers()
    demo_movielist()
    # demo_zap_and_list_epg()
    print("REMOTE_ADDR={!s}, DUMP_REQUESTS={!s}".format(REMOTE_ADDR, DUMP_REQUESTS))

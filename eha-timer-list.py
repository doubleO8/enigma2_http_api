#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from past.utils import old_div
import logging
import sys
import os
import argparse
import datetime
import pprint
import urllib.request, urllib.parse, urllib.error
import pytz

from enigma2_http_api.defaults import REMOTE_ADDR
from enigma2_http_api.controller import Enigma2APIController
from enigma2_http_api.model import EVENT_HEADER_FMT, EVENT_TITLE_FMT
from enigma2_http_api.model import EVENT_BODY_FMT, EVENT_PSEUDO_ID_FMT
from enigma2_http_api.utils import set_output_encoding

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

LOG = logging.getLogger("timer_list")


class TimerLister(Enigma2APIController):
    def __init__(self, *args, **kwargs):
        Enigma2APIController.__init__(self, *args, **kwargs)
        self.args = kwargs.get("cli_args")

    def list(self):
        set_output_encoding()

        for item in self.get_timerlist():
            print(EVENT_HEADER_FMT.format(
                item_id=item.item_id, service_name=item.service_name,
                start_time=item.start_time.strftime('%d.%m.%Y %H:%M'),
                stop_time=item.stop_time.strftime('%H:%M')))
            print(EVENT_TITLE_FMT.format(
                title=item.title,
                shortinfo=(
                item.shortinfo and u' - {:s}'.format(item.shortinfo) or "")))
            if self.args.verbose > 0:
                print(EVENT_BODY_FMT.format(
                    duration='{:d} mins.'.format(old_div(item.duration.seconds, 60)),
                    longinfo=item.longinfo))
            print(" ")

            if self.args.verbose > 1:
                print(EVENT_PSEUDO_ID_FMT.format(pseudo_id=item.pseudo_id))
                query_params = {
                    "sRef": item.get("serviceref"),
                    "begin": item.get("begin"),
                    "end": item.get("end"),
                }
                del_url = 'http://{remote_addr}/api/timerdelete?{query}'.format(
                    remote_addr=self.args.remote_addr,
                    query=urllib.parse.urlencode(query_params))
                print("Delete URL: {:s}".format(del_url))

            if self.args.verbose > 2:
                pprint.pprint(item)

            print(" ")


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--dry-run', '-n', action='store_true',
                           dest="dry_run",
                           help="dry run mode", default=False)
    argparser.add_argument('--remote-addr', '-a', dest="remote_addr",
                           default=REMOTE_ADDR,
                           help="enigma2 host address, default %(default)s")
    argparser.add_argument('--timezone', dest="local_timezone",
                           default='Europe/Berlin',
                           help="local timezone, default %(default)s")
    argparser.add_argument('-v', '--verbose',
                           action='count', default=0, dest='verbose')
    args = argparser.parse_args()

    tli = TimerLister(remote_addr=args.remote_addr,
                      dry_run=args.dry_run, cli_args=args)
    tli.list()

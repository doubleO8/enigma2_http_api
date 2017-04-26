#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import sys
import os
import argparse
import datetime
import pprint

import pytz

from enigma2_http_api.controller import Enigma2APIController
from enigma2_http_api.utils import pseudo_unique_id

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

LOG = logging.getLogger("timer_list")


class TimerLister(Enigma2APIController):
    def __init__(self, *args, **kwargs):
        Enigma2APIController.__init__(self, *args, **kwargs)
        self.args = kwargs.get("cli_args")

    def list(self):
        timerlist = self.get_timerlist()
        LOCALTIMEZONE = pytz.timezone(self.args.local_timezone)

        dt_keys = ['begin', 'end', 'startprepare', 'realbegin', 'realend']
        for item in timerlist:
            for key in dt_keys:
                try:
                    dt_obj = datetime.datetime.fromtimestamp(item[key])
                    if dt_obj.tzinfo is None:
                        dt_obj = LOCALTIMEZONE.localize(dt_obj)
                    item[key] = dt_obj
                except TypeError:
                    pass

            print '{servicename:50s} {begin} -- {end}'.format(
                servicename=item['servicename'],
                begin=item['begin'].strftime('%d.%m.%Y %H:%M'),
                end=item['end'].strftime('%H:%M')
            )
            print u'{name}'.format(name=item['name'])
            print u'{description:50s} ({duration}s) {pseudo_id}'.format(
                description=item['description'],
                duration=item['duration'],
                pseudo_id=pseudo_unique_id(item)
            )
            print " "
            print u'{descriptionextended}'.format(**item)
            # pprint.pprint(item)
            print " "


if __name__ == '__main__':
    default_remote_addr = '127.0.0.1'
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--dry-run', '-n', action='store_true',
                           dest="dry_run",
                           help="dry run mode", default=False)
    argparser.add_argument('--remote-addr', '-a', dest="remote_addr",
                           default=default_remote_addr,
                           help="enigma2 host address, default %(default)s")
    argparser.add_argument('--timezone', dest="local_timezone",
                           default='Europe/Berlin',
                           help="local timezone, default %(default)s")

    args = argparser.parse_args()

    tli = TimerLister(remote_addr=args.remote_addr,
                      dry_run=args.dry_run, cli_args=args)
    tli.list()

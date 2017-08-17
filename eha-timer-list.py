#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import sys
import os
import argparse
import datetime
import pprint
import urllib
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
                tkey = '{:s}_dt'.format(key)
                try:
                    dt_obj = datetime.datetime.fromtimestamp(item[key])
                    if dt_obj.tzinfo is None:
                        dt_obj = LOCALTIMEZONE.localize(dt_obj)
                    item[tkey] = dt_obj
                except TypeError:
                    pass

            try:
                eit = int(item.get("eit", -1))
            except Exception:
                eit = 0

            print '#{eit:06d} {servicename:50s} {begin_dt} -- {end_dt}'.format(
                servicename=item['servicename'],
                begin_dt=item['begin_dt'].strftime('%d.%m.%Y %H:%M'),
                end_dt=item['end_dt'].strftime('%H:%M'),
                eit=eit
            )
            print u'{name}'.format(name=item['name'])
            print u'{description:50s} ({duration}s) PSEUDO_ID={pseudo_id}'.format(
                description=item['description'],
                duration=item['duration'],
                pseudo_id=pseudo_unique_id(item)
            )
            print " "

            if self.args.verbose > 0:
                print u'{descriptionextended}'.format(**item)

            if self.args.verbose > 1:
                query_params = {
                    "sRef": item.get("serviceref"),
                    "begin": item.get("begin"),
                    "end": item.get("end"),
                }
                del_url = 'http://{remote_addr}/api/timerdelete?{query}'.format(
                    remote_addr=self.args.remote_addr,
                    query=urllib.urlencode(query_params))
                print("delete URL: {:s}".format(del_url))

            if self.args.verbose > 2:
                pprint.pprint(item)

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
    argparser.add_argument('-v', '--verbose',
                            action='count', default=0, dest='verbose')
    args = argparser.parse_args()

    tli = TimerLister(remote_addr=args.remote_addr,
                      dry_run=args.dry_run, cli_args=args)
    tli.list()

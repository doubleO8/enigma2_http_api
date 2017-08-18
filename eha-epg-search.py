#!/usr/bin/python
# -*- coding: utf-8 -*-
import pprint
import logging
import time
import sys
import os
import argparse
import json
import datetime
import re

import pytz

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from enigma2_http_api.controller import Enigma2APIController
from enigma2_http_api.utils import parse_servicereference
from enigma2_http_api.utils import normalise_servicereference
from enigma2_http_api.utils import pseudo_unique_id
from enigma2_http_api.utils import SERVICE_TYPE_TV, SERVICE_TYPE_HDTV

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

LOG = logging.getLogger("eha_epg_search")


class EPGSearch(Enigma2APIController):
    def __init__(self, *args, **kwargs):
        Enigma2APIController.__init__(self, *args, **kwargs)
        self.args = kwargs.get("cli_args")
        self.lookup_map = dict()
        self.timezone = pytz.timezone(self.args.local_timezone)

    def main(self):
        for item in self.search(self.args.search_query):
            try:
                pseudo_id = pseudo_unique_id(item)
            except Exception:
                pseudo_id = None
            print('#{eit:06d} {servicename:50s} {begin_dt} -- {end_dt}'.format(
                   eit=item['id'], servicename=item['sname'],
                   begin_dt=item['begin_timestamp_dt'].strftime('%d.%m.%Y %H:%M'),
                   end_dt=(item['begin_timestamp_dt'] + datetime.timedelta(seconds=item['duration_sec'])).strftime('%H:%M'),
                  )
            )
            print u'{name}'.format(name=item['title'])
            print u'{description:50s} ({duration}s) PSEUDO_ID={pseudo_id}'.format(
                description=item['shortdesc'],
                duration=item['duration'],
                pseudo_id=pseudo_id
            )
            print " "

            if self.args.verbose > 0:
                print u'{descriptionextended}'.format(descriptionextended=item['longdesc'])

            if self.args.verbose > 2:
                pprint.pprint(item)

            print " "

    def _update_lookup_map(self):
        st = (SERVICE_TYPE_TV, SERVICE_TYPE_HDTV)

        for servicename, servicereference in self.get_services():
            self.log.debug("Evaluating bouquet {!r}".format(servicename))
            for res in self.get_getservices(servicereference):
                sref = res['servicereference']
                val = res['servicename']
                psref = parse_servicereference(sref)

                self.log.debug(
                    "{:s}? {!r}".format(normalise_servicereference(sref),
                                        val))

                self.lookup_map[sref] = val

        for key in sorted(self.lookup_map.keys(),
                          key=lambda x: normalise_servicereference(x)):
            self.log.debug("{:s}> {!r}".format(normalise_servicereference(key),
                                               self.lookup_map[key]))

    def filter_search_results(self, data):
        for item in data:
            psref = parse_servicereference(item['sref'])
            if self.args.verbose > 2:
                pprint.pprint(item)

            del item['picon']
            LOCALTIMEZONE = pytz.timezone(self.args.local_timezone)

            dt_keys = ['begin_timestamp']
            for key in dt_keys:
                tkey = '{:s}_dt'.format(key)
                try:
                    dt_obj = datetime.datetime.fromtimestamp(item[key])
                    if dt_obj.tzinfo is None:
                        dt_obj = LOCALTIMEZONE.localize(dt_obj)
                    item[tkey] = dt_obj
                except TypeError:
                    pass

            if self.args.verbose > 1:
                pprint.pprint(item)
            yield item

    def search(self, what):
        return self.get_search(what, filter_func=self.filter_search_results)

    def zap(self, what):
        zap_to = None

        if not self.lookup_map:
            self._update_lookup_map()

        for sref in self.lookup_map:
            if what == self.lookup_map[sref]:
                zap_to = sref
                break

        if zap_to is None:
            zap_to = what

        self.log.info("Zapping to {!r} ({!r})".format(what, zap_to))

        try:
            parse_servicereference(zap_to)
        except Exception, pexc:
            self.log.error("Invalid service reference! {!r}".format(pexc))
            return False

        res = self.get_zap(zap_to)
        self.log.info(res)


if __name__ == '__main__':
    default_remote_addr = '127.0.0.1'
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--dry-run', '-n', action='store_true',
                           dest="dry_run",
                           help="dry run mode", default=False)
    argparser.add_argument('--verbose', '-v', action='count',
                           default=0, dest="verbose",
                           help="verbosity (more v: more verbosity)")
    argparser.add_argument('--remote-addr', '-a', dest="remote_addr",
                           default=default_remote_addr,
                           help="enigma2 host address, default %(default)s")
    argparser.add_argument(dest="search_query",
                           help="Search query")
    argparser.add_argument('--timezone', dest="local_timezone",
                           default='Europe/Berlin',
                           help="local timezone, default %(default)s")

    args = argparser.parse_args()

    es = EPGSearch(remote_addr=args.remote_addr,
                   dry_run=args.dry_run, cli_args=args)
    es.main()

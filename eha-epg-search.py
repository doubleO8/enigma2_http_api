#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from past.utils import old_div
import pprint
import logging
import argparse

import pytz

from enigma2_http_api.defaults import REMOTE_ADDR
from enigma2_http_api.controller import Enigma2APIController
from enigma2_http_api.utils import parse_servicereference
from enigma2_http_api.utils import normalise_servicereference
from enigma2_http_api.utils import set_output_encoding
from enigma2_http_api.utils import SERVICE_TYPE_TV, SERVICE_TYPE_HDTV
from enigma2_http_api.model import EVENT_HEADER_FMT, EVENT_TITLE_FMT
from enigma2_http_api.model import EVENT_BODY_FMT
from enigma2_http_api.model import EVENT_HEADER_TECH_FMT

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
        set_output_encoding()

        for item in self.search(self.args.search_query):
            fmt = EVENT_HEADER_FMT
            args = dict(
                item_id=item.item_id, service_name=item.service_name,
                start_time=item.start_time.strftime('%d.%m.%Y %H:%M'),
                stop_time=item.stop_time.strftime('%H:%M'),
            )
            if self.args.tech_mode:
                fmt = EVENT_HEADER_TECH_FMT
                # psr = parse_servicereference(item.service_reference)
                args['service_reference'] = item.service_reference

            print(fmt.format(**args))
            print(EVENT_TITLE_FMT.format(
                title=item.title,
                shortinfo=(
                    item.shortinfo and u' - {:s}'.format(
                        item.shortinfo) or "")))
            if self.args.verbose > 0:
                print(EVENT_BODY_FMT.format(
                    duration='{:d} mins.'.format(old_div(item.duration.seconds, 60)),
                    longinfo=item.longinfo))
            print(" ")
            if self.args.verbose > 2:
                pprint.pprint(item)
            print(" ")

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

        for key in sorted(list(self.lookup_map.keys()),
                          key=lambda x: normalise_servicereference(x)):
            self.log.debug("{:s}> {!r}".format(normalise_servicereference(key),
                                               self.lookup_map[key]))

    def filter_search_results(self, data):
        if (self.args.verbose or self.args.tech_mode) and data:
            self.log.info("Filtering {:d} result(s)".format(len(data)))

        for item in data:
            if self.args.verbose > 1:
                pprint.pprint(item)

            del item['picon']

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
        except Exception as pexc:
            self.log.error("Invalid service reference! {!r}".format(pexc))
            return False

        res = self.get_zap(zap_to)
        self.log.info(res)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--dry-run', '-n', action='store_true',
                           dest="dry_run",
                           help="dry run mode", default=False)
    argparser.add_argument('--technical', '-t', action='store_true',
                           dest="tech_mode",
                           help="dump more technical details", default=False)
    argparser.add_argument('--verbose', '-v', action='count',
                           default=0, dest="verbose",
                           help="verbosity (more v: more verbosity)")
    argparser.add_argument('--remote-addr', '-a', dest="remote_addr",
                           default=REMOTE_ADDR,
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

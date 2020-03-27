#!/usr/bin/python
# -*- coding: utf-8 -*-
import pprint
import logging
import argparse
import datetime

import pytz

from enigma2_http_api.defaults import REMOTE_ADDR
from enigma2_http_api.controller import Enigma2APIController
from enigma2_http_api.controller import POWERSTATE_MAP
from enigma2_http_api.utils import parse_servicereference
from enigma2_http_api.utils import normalise_servicereference
from enigma2_http_api.utils import set_output_encoding
from enigma2_http_api.utils import SERVICE_TYPE_TV, SERVICE_TYPE_HDTV
from enigma2_http_api.model import EVENT_HEADER_FMT, EVENT_TITLE_FMT
from enigma2_http_api.model import EVENT_BODY_FMT

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

LOG = logging.getLogger("eha_epg_search")

API_CALL_PREFIX = 'api_call-'


class UtilityBelt(Enigma2APIController):
    def __init__(self, *args, **kwargs):
        Enigma2APIController.__init__(self, *args, **kwargs)
        self.args = kwargs.get("cli_args")
        self.lookup_map = dict()
        self.timezone = pytz.timezone(self.args.local_timezone)

    def main(self):
        set_output_encoding()

        if self.args.power_state != -1:
            pprint.pprint(self.get_powerstate(self.args.power_state))
        elif self.args.mode.startswith(API_CALL_PREFIX):
            api_call = self.args.mode.replace(API_CALL_PREFIX, '')
            self.dump_api_result(api_call)
        elif self.args.zap_to_service:
            self.zap(self.args.zap_to_service)
        else:
            try:
                getattr(self, self.args.mode)()
            except AttributeError as aexception:
                self.log.error("Ha! Unsupported: {!r}".format(aexception))

    def about(self):
        pprint.pprint(self.get_about())

    def dump_api_result(self, api_call):
        pprint.pprint(self._apicall(api_call))

    def dump_has_rest_result(self):
        pprint.pprint(self.has_rest_support())

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
    argparser.add_argument('--verbose', '-v', action='count',
                           default=0, dest="verbose",
                           help="verbosity (more v: more verbosity)")
    argparser.add_argument('--remote-addr', '-a', dest="remote_addr",
                           default=REMOTE_ADDR,
                           help="enigma2 host address, default %(default)s")
    argparser.add_argument('--timezone', dest="local_timezone",
                           default='Europe/Berlin',
                           help="local timezone, default %(default)s")

    group_op = argparser.add_argument_group('Tools')
    group_op.add_argument('--about',
                          help='Dump "about" dataset',
                          action='store_const', const='about',
                          default='about', dest="mode")
    group_op.add_argument('--has-rest',
                          help='Dump result of REST supported check',
                          action='store_const', const='dump_has_rest_result',
                          default='about', dest="mode")
    group_op.add_argument('--zap', dest="zap_to_service",
                           default=None,
                           help="ZAP to Service")

    group_ac = argparser.add_argument_group('Miscellaneous API calls')
    api_calls = [
        'currenttime',
        # 'external',
        'getaudiotracks',
        'getcurrlocation',
        'getlocations',
        'getpid',
        'gettags',
        'mediaplayercurrent',
        'movietags',
        'parentcontrollist',
        'pluginlistread',
        'powerstate',
        'restarttwisted',
        # 'session',
        'settings',
        'vol',
    ]

    for ac in api_calls:
        group_ac.add_argument(
            '--{:s}'.format(ac),
            help='Dump data of API call {:s}'.format(ac),
            action='store_const', const='{:s}{:s}'.format(
                API_CALL_PREFIX, ac),
            default='about', dest="mode")

    group_power = argparser.add_argument_group('Power State Altering')
    for pw in POWERSTATE_MAP:
        group_power.add_argument(
            '--{:s}'.format(pw),
            help='Alter Powerstate: {:s}'.format(pw),
            action='store_const', const=POWERSTATE_MAP[pw],
            default=-1, dest="power_state")

    args = argparser.parse_args()

    ub = UtilityBelt(remote_addr=args.remote_addr,
                     dry_run=args.dry_run, cli_args=args)
    ub.main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import logging
import sys
import os
import argparse
import json
import datetime

from enigma2_http_api.defaults import REMOTE_ADDR
from enigma2_http_api.controller import Enigma2APIController
from enigma2_http_api.utils import parse_servicereference
from enigma2_http_api.utils import create_servicereference
from enigma2_http_api.utils import normalise_servicereference
from enigma2_http_api.utils import SERVICE_TYPE_TV, SERVICE_TYPE_HDTV
from enigma2_http_api.utils import NS_DVB_C
from enigma2_http_api.utils import NS, SERVICE_TYPE
from enigma2_http_api.utils import NS_LOOKUP, SERVICE_TYPE_LOOKUP

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

LOG = logging.getLogger("service_list")


class ServiceLister(Enigma2APIController):
    def __init__(self, *args, **kwargs):
        Enigma2APIController.__init__(self, *args, **kwargs)
        self.args = kwargs.get("cli_args")
        self.lookup_map = dict()
        self.timerlist_map = dict()
        self._update_lookup_map()

    def _update_lookup_map(self):
        if not self.args.filter_service_type:
            st = (SERVICE_TYPE_TV, SERVICE_TYPE_HDTV)
        else:
            st = self.args.filter_service_type

        if not self.args.filter_namespace:
            namespace = (NS_DVB_C,)
        else:
            namespace = self.args.filter_namespace

        filter_oid = None
        if self.args.filter_oid:
            filter_oid = []
            for item in self.args.filter_oid:
                if item.startswith('0x'):
                    item_i = int(item, 16)
                else:
                    item_i = int(item)
                filter_oid.append(item_i)

        self.log.debug(
            "st={!r} namespace={!r} filter_oid={!r}".format(st, namespace,
                                                            filter_oid))

        for servicename, servicereference in self.get_services():
            self.log.info("Evaluating bouquet {!r}".format(servicename))
            for res in self.get_getservices(servicereference):
                sref = res['servicereference']
                val = res['servicename']
                psref = parse_servicereference(sref)

                if psref.get('service_type') not in st:
                    self.log.debug(
                        'ignored(TYPE={!s}): {!r:40} / {!r}'.format(
                            psref.get('service_type'), val, sref))
                    continue

                self.log.debug(
                    "{:s}? {!r}".format(normalise_servicereference(sref),
                                        val))

                if psref.get('ns') not in namespace:
                    self.log.debug(
                        'ignored(NS): {!r:40} / {!r}'.format(val, sref))
                    continue

                if filter_oid:
                    if psref.get('oid') not in filter_oid:
                        self.log.debug(
                            'ignored(oid): {!r:40} / {!r}'.format(val, sref))
                        continue

                self.lookup_map[sref] = res

        for key in sorted(list(self.lookup_map.keys()),
                          key=lambda x: normalise_servicereference(x)):
            self.log.debug("{:s}> {!r}".format(normalise_servicereference(key),
                                               self.lookup_map[key]))

    def _sorted(self):
        if self.args.sorting == 'servicename':
            meta = list()

            for key in self.lookup_map:
                meta.append((self.lookup_map[key]['servicename'], key))

            return [x[1] for x in sorted(meta)]
        else:
            return sorted(list(self.lookup_map.keys()),
                          key=lambda x: normalise_servicereference(x))

    def list(self):
        for key in self._sorted():
            item = self.lookup_map[key]
            sref = parse_servicereference(item['servicereference'])
            self.log.debug("{:s}> {!r}".format(normalise_servicereference(key),
                                               self.lookup_map[key]))
            print('0x{oid:04X} {service_type:5s} {namespace:5s} {servicename:50s} {sref}'.format(
                oid=sref['oid'],
                service_type=SERVICE_TYPE_LOOKUP[sref['service_type']],
                namespace=NS_LOOKUP[sref['ns']],
                servicename=item['servicename'].encode('utf-8'),
                sref=item['servicereference']
            ))

    def dump(self):
        data = {
            "created": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "services": dict()
        }

        for key in self._sorted():
            item = self.lookup_map[key]
            sref = parse_servicereference(item['servicereference'])
            item_key = create_servicereference(sref)
            data['services'][item_key] = item

        with open(self.args.dump_file, "wb") as tgt:
            json.dump(data, tgt, indent=2)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--dry-run', '-n', action='store_true',
                           dest="dry_run",
                           help="dry run mode", default=False)
    argparser.add_argument('--remote-addr', '-a', dest="remote_addr",
                           default=REMOTE_ADDR,
                           help="enigma2 host address, default %(default)s")
    argparser.add_argument('--dump', dest="dump_file", metavar="FILE",
                           default=None,
                           help="File to dump service information to")

    group1 = argparser.add_argument_group('Sorting', 'Output Sorting')
    sortgroup = group1.add_mutually_exclusive_group()
    sortgroup.add_argument('--sort-name', dest="sorting",
                           default='servicename', const='servicename',
                           action='store_const',
                           help="sort by service name")
    sortgroup.add_argument('--sort-sref', dest="sorting",
                           default='servicename', const='serviceref',
                           action='store_const',
                           help="sort by service reference")

    fgroup = argparser.add_argument_group('Filtering', 'filter service list')
    fgroup.add_argument('--oid', dest="filter_oid",
                        default=[],
                        action='append',
                        help="filter by OID")

    for key in NS:
        fgroup.add_argument('--ns-' + key, dest="filter_namespace",
                            default=[],
                            const=NS[key], action='append_const',
                            help="filter namespace " + key)

    for key in SERVICE_TYPE:
        fgroup.add_argument('--st-' + key, dest="filter_service_type",
                            default=[],
                            const=SERVICE_TYPE[key], action='append_const',
                            help="filter namespace " + key)

    args = argparser.parse_args()

    sli = ServiceLister(remote_addr=args.remote_addr,
                        dry_run=args.dry_run, cli_args=args)
    sli.list()
    if args.dump_file:
        sli.dump()

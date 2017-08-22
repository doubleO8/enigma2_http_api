#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import sys
import os
import argparse
import pprint

from enigma2_http_api.defaults import REMOTE_ADDR
from enigma2_http_api.controller import Enigma2APIController

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

LOG = logging.getLogger("movie_list")


class MovieLister(Enigma2APIController):
    def __init__(self, *args, **kwargs):
        Enigma2APIController.__init__(self, *args, **kwargs)
        self.args = kwargs.get("cli_args")

    def list(self):
        for item in self.get_movielist()['movies']:
            self.log.debug(pprint.pformat(item))
            self.log.info(os.path.basename(item['filename']))


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--dry-run', '-n', action='store_true',
                           dest="dry_run",
                           help="dry run mode", default=False)
    argparser.add_argument('--remote-addr', '-a', dest="remote_addr",
                           default=REMOTE_ADDR,
                           help="enigma2 host address, default %(default)s")

    args = argparser.parse_args()

    moli = MovieLister(remote_addr=args.remote_addr,
                       dry_run=args.dry_run, cli_args=args)
    moli.list()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
from builtins import object
import os
import logging
import pprint
import json
import codecs

import requests

from .model import EEvent
from .utils import parse_servicereference, NORMALISED_SERVICEREFERENCE_FMT
from .utils import create_servicereference

#: enigma2 web interface URL format string
ENIGMA2_URL_FMT = '{scheme}://{remote_addr}/{path}'

# http://www.opena.tv/howtos/15123-enigma2-shell-befehle.html
POWERSTATE_TOGGLE_STANDBY = 0
POWERSTATE_DEEPSTANDBY = 1
POWERSTATE_REBOOT = 2
POWERSTATE_RESTART = 3
POWERSTATE_WAKEUP = 4
POWERSTATE_STANDBY = 5

POWERSTATE_MAP = {
    'toggle-standby': POWERSTATE_TOGGLE_STANDBY,
    'deep-standby': POWERSTATE_DEEPSTANDBY,
    'reboot': POWERSTATE_REBOOT,
    'restart': POWERSTATE_RESTART,
    'wakeup': POWERSTATE_WAKEUP,
    'standby': POWERSTATE_STANDBY,
}

MESSAGETYPE_YES_NO = 0
MESSAGETYPE_INFO = 1
MESSAGETYPE_MESSAGE = 2
MESSAGETYPE_ATTENTION = 3

MESSAGETYPES = [
    MESSAGETYPE_YES_NO,
    MESSAGETYPE_INFO,
    MESSAGETYPE_MESSAGE,
    MESSAGETYPE_ATTENTION
]


class BlacklistController(object):
    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger(__name__)
        self.blacklist = dict()
        self._blacklist_path = None
        self._pseudo_id_none_warnings = kwargs.get("pseudo_id_none_warnings",
                                                   True)

        if kwargs.get("blacklist_path"):
            self._blacklist_path = kwargs.get("blacklist_path")
            self.update_blacklist()

    def update_blacklist(self, filename=None):
        if not filename:
            filename = self._blacklist_path

        if filename is None:
            raise AssertionError('[update] blacklist filename may not be None')

        self.log.debug('%s', "Trying to load blacklist: {!r}".format(filename))

        try:
            with codecs.open(filename, "rb", "utf-8") as source:
                data = json.load(source)
                self.log.debug(
                    "the blacklist {!r} contains {:d} entrie(s)".format(
                        filename, len(data)))

            self.blacklist.update(data)
        except IOError as ierr:
            self.log.warning('%s',
                             "Failed to load blacklist data {!r}: {!s}".format(
                                 filename, ierr))

        self.log.debug("the blacklist contains {:d} entrie(s)".format(
            len(self.blacklist)))

    def persist_blacklist(self, items, filename=None):
        data = dict()

        if not filename:
            filename = self._blacklist_path

        if filename is None:
            raise AssertionError(
                "[persist] blacklist filename may not be None!")

        for item in items:
            e_item = EEvent(item)
            if e_item.pseudo_id is None:
                if self._pseudo_id_none_warnings:
                    self.log.warning(
                        '%s', "Pseudo ID is None: {!r}".format(item))
                continue
            data[e_item.pseudo_id] = item

        if not data:
            self.log.warning("No data to persist ..")
            return

        data.update(self.blacklist)

        self.log.debug("Persisting blacklist: {!r} ({:d} entries)".format(
            filename, len(data)))

        with codecs.open(filename, "wb", "utf-8") as target:
            json.dump(data, target, indent=2)


class Enigma2APIController(BlacklistController):
    """
    Enigma2 Web API Consuming Controller Class
    """

    def __init__(self, *args, **kwargs):
        BlacklistController.__init__(self, *args, **kwargs)
        self.log = logging.getLogger(__name__)
        self.remote_addr = kwargs.get("remote_addr", "enigma2.local")
        self.movielist_map = dict()
        self.movielist = list()
        self.dry_run = kwargs.get("dry_run", False)
        self.dump_requests = kwargs.get("dump_requests")
        self._request_no = 0
        self.timezone = kwargs.get("timezone")

        if self.dump_requests:
            self.log.info('%s',
                          "{!r} will contain request dump files".format(
                              self.dump_requests))

    def _get(self, url, **kwargs):
        """
        Generic HTTP GET request.

        :param url: URL
        :param kwargs: URL parameters
        :return: decoded JSON data
        :rtype: dict
        """
        self._request_no += 1
        try:
            return requests.get(url, **kwargs)
        except Exception as exc:
            self.log.error(
                "Error GETting {!s}: No JSON result? {!s}".format(url, exc))
            raise

    def _api(self, path):
        """
        Generate an API URL.

        :param path: path
        :return: API URL
        :rtype: str
        """
        return ENIGMA2_URL_FMT.format(remote_addr=self.remote_addr,
                                      path='api/{:s}'.format(path),
                                      scheme='http')

    def _dump_request(self, req, filter_key=None):
        dump_filename = 'eha_raw_{:04d}.json'.format(self._request_no)
        target_filename = os.path.join(self.dump_requests, dump_filename)
        data = {
            'url': req.url,
            '_filter_key': filter_key,
            'response': req.json(),
        }

        if filter_key:
            data['response'] = data['response'][filter_key]

        with open(target_filename, "wb") as target:
            json.dump(data, target, indent=2)

    def _apicall(self, path, **kwargs):
        """
        Execute generic API call.

        :param path: path
        :param kwargs: URL parameters
        :return: decoded JSON data
        :rtype: dict
        """
        filter_key = kwargs.get("filter_key")
        if filter_key:
            del kwargs['filter_key']

        req = self._get(self._api(path), **kwargs)

        if self.dump_requests:
            try:
                self._dump_request(req, filter_key)
            except Exception as exc:
                self.log.warning('%s',
                                 "Request dumping failed: {!r}".format(exc))

        rv = req.json()
        if filter_key:
            rv = rv[filter_key]

        return rv

    def has_rest_support(self):
        result = False
        target_url = ENIGMA2_URL_FMT.format(scheme='http',
                                            remote_addr=self.remote_addr,
                                            path='file')
        req = requests.options(target_url)

        if req.status_code == 200:
            expected_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Credentials',
                'Access-Control-Max-Age',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers',
            ]
            expected_headers_set = set([x.lower() for x in expected_headers])
            headers_set = set([x.lower() for x in list(req.headers.keys())])
            result = (
                len(expected_headers) == len(expected_headers_set & headers_set)
            )

        return result

    def update_movielist_map(self):
        """
        Update internal movie list map *self.movielist_map*
        by retrieving the current list of movie items on
        Enigma2 box.
        """
        res = self.get_movielist()
        self.movielist = res['movies']

        for item in self.movielist:
            e_item = EEvent(item)
            if e_item.pseudo_id is None:
                if self._pseudo_id_none_warnings:
                    self.log.warning(
                        '%s', "Pseudo ID is None: {!r}".format(item))
                continue
            self.movielist_map[e_item.pseudo_id] = item

    def get_services(self):
        """
        Get services (bouquets).

        :return: list containing service name and reference
        :rtype: list
        """
        res = self._apicall('getservices', filter_key='services')
        services = list()
        for row in res:
            services.append((row['servicename'], row['servicereference']))
        return services

    def get_getservices(self, service_ref):
        params = {
            'sRef': service_ref,
        }
        return self._apicall('getservices', params=params,
                             filter_key='services')

    def get_about(self):
        """
        Retrieve information about enigma2 device.

        :return: Enigma2 device information
        :rtype: dict
        """
        return self._apicall('about')

    def get_epgbouquet(self, bouquet_ref, filter_func=None):
        """
        Get EPG datasets for *bouquet_ref*.
        (**currently** running subservices' EPG datasets)

        :param bouquet_ref: bouquet reference
        :param filter_func: filter function
        :return: EPG datasets of current subservice
        :rtype: list
        """
        res = self._apicall('epgbouquet', params={'bRef': bouquet_ref},
                            filter_key='events')
        if filter_func is not None:
            return list(filter_func(res))
        return res

    def get_epgservice(self, service_ref, filter_func=None):
        """
        Get EPG datasets for *service_ref*.

        :param service_ref: service reference
        :param filter_func: filter function
        :return: EPG datasets of given service
        :rtype: list
        """
        res = self._apicall('epgservice', params={'sRef': service_ref},
                            filter_key='events')
        if filter_func is not None:
            return list(filter_func(res))
        return res

    def get_subservices(self):
        """
        Get subservices for current service

        :return: subservices of current service
        :rtype: list
        """
        return self._apicall('subservices', filter_key='services')

    def get_getallservices(self):
        """
        Get all services.

        :return:
        """
        return self._apicall('getallservices', filter_key='services')

    def get_movielist(self):
        """
        Get list of movie items available on *self.remote_addr*.

        :return:
        """
        return self._apicall('movielist')

    def get_moviedelete(self, service_ref):
        """
        Delete a movie item.

        :param service_ref: service reference
        :return:
        """
        params = {
            'sRef': service_ref
        }
        return self._apicall('moviedelete', params=params)

    def get_timerlist(self):
        """
        Get list of timers.

        :return:
        """
        return [EEvent(x, timezone=self.timezone) for x in
                self._apicall('timerlist', filter_key='timers')]

    def get_timeradd(self, service_ref, params):
        """
        Add a new timer

        /web/timeradd?sRef=&repeated=&begin=&end=&name=&description=&dirname=&tags=&eit=&disabled=&justplay=&afterevent=

        :param service_ref: service reference
        :param params: timer parameters
        :return:
        """
        params['sRef'] = service_ref
        return self._apicall('timeradd', params=params, filter_key='message')

    def get_timeraddbyeventid(self, service_ref, event_id):
        """
        Add a new timer by ID.

        :param service_ref: service reference
        :param event_id: ID of the event to be recorded
        :return:
        """
        params = {
            'sRef': service_ref,
            'eventid': event_id
        }
        return self._apicall('timeraddbyeventid', params=params)

    def get_timerdelete(self, service_ref, begin, end):
        """
        Delete an existing timer.

        :param service_ref: service reference
        :param begin: start time
        :param end: end time
        :return:
        """
        params = {
            'sRef': service_ref,
            'begin': begin,
            'end': end
        }
        return self._apicall('timerdelete', params=params, filter_key='message')

    def get_search(self, what, filter_func=None):
        """
        Search EPG for *what*.
        Will filter results if *filter_func* is given.

        :param what: Search string
        :param filter_func: result filtering function
        :return:
        """
        params = {
            'search': what,
        }
        res = self._apicall('epgsearch', params=params, filter_key='events')
        if filter_func is not None:
            return [EEvent(x, timezone=self.timezone) for x in filter_func(res)]
        return [EEvent(x, timezone=self.timezone) for x in res]

    def get_zap(self, service_ref):
        """
        Try to zap to given service.

        :param service_ref: service reference
        :return:
        """
        params = {
            'sRef': service_ref,
        }

        if self.dry_run:
            self.log.info('%s', "WOULD zap to {!r}".format(service_ref))
            return service_ref

        return self._apicall('zap', params=params, filter_key='message')

    def get_powerstate(self, new_state):
        """
        Change Power State

        :param new_state: Desired Power State
        :return:
        """
        params = {
            'newstate': new_state,
        }

        if self.dry_run:
            self.log.info('%s',
                          "WOULD set powerstate to {!r}".format(new_state))
            return ''

        return self._apicall('powerstate', params=params)

    def get_message(self, messagetext, timeout=10,
                    messagetype=MESSAGETYPE_INFO):
        """
        Display a message on enigma2's attached screen.

        :param messagetext: message
        :param timeout: timeout
        :param messagetype: message type
        :return:
        """
        params = {
            'text': messagetext,
            'type': messagetype,
        }

        if timeout:
            params['timeout'] = timeout

        if self.dry_run:
            self.log.info(
                '%s',
                "WOULD send message {!r} type={!r} timeout={!r}".format(
                    messagetext, messagetype, timeout))
            return ''

        return self._apicall('message', params=params)

    def get_messageanswer(self, messagetext, timeout=10):
        """
        Display a message and wait for user selection.
        (SEEMS TO BE NON-WORKING)

        :param messagetext: message
        :param timeout: timeout
        :return:
        """
        params = {
            'text': messagetext,
            'type': MESSAGETYPE_YES_NO,
            'getanswer': 'now'
        }

        if timeout:
            params['timeout'] = timeout

        if self.dry_run:
            self.log.info(
                '%s',
                "WOULD send messageanswer {!r} timeout={!r}".format(
                    messagetext, timeout))
            return ''

        return self._apicall('messageanswer', params=params)


class ServiceLookupController(object):
    def __init__(self, *args, **kwargs):
        self._lookup = dict()
        self._servicename_lookup = dict()

        if len(args) == 1:
            self.update_raw(args[0])

    def __getitem__(self, key):
        return self._servicename_lookup[key]

    def update_raw(self, getallservices_result):
        for item in getallservices_result:
            for sub in item.get("subservices", []):
                psref = parse_servicereference(sub['servicereference'])
                if psref['oid'] == psref['tsid'] == psref['sid'] == psref[
                    'ns'] == 0:
                    continue
                nrm_servicereference = NORMALISED_SERVICEREFERENCE_FMT.format(
                    **psref)
                service_tuple = (sub['servicename'], psref['ns'])
                self._lookup[nrm_servicereference] = service_tuple

                self._servicename_lookup[service_tuple] = psref

    def lookup_service(self, servicename, ns):
        return create_servicereference(self[(servicename, ns)])


if __name__ == '__main__':
    import sys
    import tempfile

    REMOTE_ADDR = os.environ.get('ENIGMA2_HTTP_API_HOST')
    if not REMOTE_ADDR:
        sys.exit(-1)
    DUMP_REQUESTS = tempfile.mkdtemp()
    print("REMOTE_ADDR={!s}, DUMP_REQUESTS={!s}".format(REMOTE_ADDR,
                                                        DUMP_REQUESTS))
    EAC = Enigma2APIController(remote_addr=REMOTE_ADDR,
                               dump_requests=DUMP_REQUESTS)
    EAC.get_services()
    EAC.get_about()
    EAC.get_subservices()
    EAC.get_getallservices()
    EAC.get_movielist()
    EAC.get_timerlist()

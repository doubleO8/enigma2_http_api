#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Model classes and constants.
"""
import pprint
import datetime

import pytz

from utils import parse_servicereference, create_servicereference

DEFAULT_LOCALTIMEZONE = "Europe/Berlin"

# '25.08.2017 00:10'
DT_FORMAT__REAL__KEYS = '%d.%m.%Y %H:%M'

ID = 1
START_TIMESTAMP = 2
STOP_TIMESTAMP = 3
DURATION = 4
SERVICE_NAME = 5
SERVICE_REFERENCE = 6
SHORTINFO = 7
LONGINFO = 8
TITLE = 9

# ETSI EN 300 707 V1.2.1 (2002-12)
# ETSI ETR 288 TECHNICAL October 1996
_METAMAP_ATTRIBUTES = {
    'item_id': ID,
    'service_name': SERVICE_NAME,
    'service_reference': SERVICE_REFERENCE,
    'title': TITLE,
    'shortinfo': SHORTINFO,
    'longinfo': LONGINFO,
}

_METAMAP_ATTR_REV = {
    START_TIMESTAMP: 'start_time',
    STOP_TIMESTAMP: 'stop_time',
}

for k, v in _METAMAP_ATTRIBUTES.items():
    if v is not None:
        _METAMAP_ATTR_REV[v] = k

ITEM_TYPE_TIMER = 'timer'
ITEM_TYPE_EPG = 'epg'

_META_MAP = {
    ITEM_TYPE_TIMER: {
        ID: 'eit',
        TITLE: 'name',
        START_TIMESTAMP: 'begin',
        STOP_TIMESTAMP: 'end',
        DURATION: None,
        SERVICE_NAME: 'servicename',
        SERVICE_REFERENCE: 'serviceref',
        SHORTINFO: 'description',
        LONGINFO: 'descriptionextended',
    },
    ITEM_TYPE_EPG: {
        ID: 'id',
        TITLE: 'title',
        START_TIMESTAMP: 'begin_timestamp',
        STOP_TIMESTAMP: None,
        DURATION: 'duration_sec',
        SERVICE_NAME: 'sname',
        SERVICE_REFERENCE: 'sref',
        SHORTINFO: 'shortdesc',
        LONGINFO: 'longdesc',
    }
}


class EEvent(dict):
    def __init__(self, *args, **kwargs):
        """
        Container class for timer or EPG items providing unified access to the
        data.
        Original data is exposed by `__getitem__()` access,
        mangled data is available through attributes.

        :param args:
        :param kwargs:
        :return:

        >>> from example_data import example_epg, example_timer, expected
        >>> epg_d = EEvent(example_epg)
        >>> timer_d = EEvent(example_timer)
        >>> epg_d.title == expected['title']
        True
        >>> timer_d.title == expected['title']
        True
        >>> epg_d.shortinfo == expected['shortinfo']
        True
        >>> timer_d.shortinfo == expected['shortinfo']
        True
        >>> epg_d.item_id == expected['item_id']
        True
        >>> timer_d.item_id == expected['item_id']
        True
        >>> epg_d.service_reference == expected['service_reference']
        True
        >>> timer_d.service_reference == expected['service_reference']
        True
        """
        dict.__init__(self, *args, **kwargs)
        if kwargs.get("timezone") is None:
            self.timezone = pytz.timezone(DEFAULT_LOCALTIMEZONE)
        else:
            self.timezone = kwargs.get("timezone")
        self._init_attributes()

    def _localized_dt(self, value):
        try:
            dt_obj = datetime.datetime.fromtimestamp(value)
        except TypeError:
            dt_obj = datetime.datetime.strptime(value, DT_FORMAT__REAL__KEYS)

        return self.timezone.localize(dt_obj)

    def _init_attributes(self):
        try:
            self['duration_sec']
            self._type = ITEM_TYPE_EPG
        except KeyError:
            self._type = ITEM_TYPE_TIMER

        attr_map = _META_MAP[self._type]

        for name in _METAMAP_ATTRIBUTES:
            key = _METAMAP_ATTRIBUTES.get(name)
            value = self.get(attr_map[key])
            setattr(self, name, value)

        dt_keys = [START_TIMESTAMP]
        if self._type == ITEM_TYPE_TIMER:
            dt_keys.append(STOP_TIMESTAMP)

        for dt_key in dt_keys:
            data_key = attr_map[dt_key]
            setattr(self, _METAMAP_ATTR_REV[dt_key],
                    self._localized_dt(self[data_key]))

        if self._type == ITEM_TYPE_EPG:
            self.duration = datetime.timedelta(
                seconds=self[attr_map[DURATION]])
            self.stop_time = self.start_time + self.duration
        elif self._type == ITEM_TYPE_TIMER:
            self.duration = self.stop_time - self.start_time
        else:
            raise ValueError("Unsupported type {!r}".format(self._type))

        self.service_reference = create_servicereference(
            parse_servicereference(self.service_reference))

    def __str__(self):
        return '[{:s}#{:d}] {:s} {:s}{:s}'.format(
            self.service_name, self.item_id,
            self.start_time.strftime('%y-%m-%d %H:%M'),
            self.title,
            (self.shortinfo and ' - {:s}'.format(self.shortinfo) or '')
        )

    def __repr__(self):
        return '<{:s} {!r} {:s}#{:06d}> {:s} {!r} {!r}'.format(
            self.__class__.__name__, self._type,
            self.service_name,
            self.item_id, self.start_time.strftime('%Y-%m-%d %H:%M %z %Z'),
            self.title, self.shortinfo)


if __name__ == '__main__':
    import doctest

    (FAILED, SUCCEEDED) = doctest.testmod()
    print("[doctest] SUCCEEDED/FAILED: {:d}/{:d}".format(SUCCEEDED, FAILED))

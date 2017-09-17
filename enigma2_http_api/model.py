#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Model classes and constants.
----------------------------

"""
import datetime

import pytz

from utils import parse_servicereference, create_servicereference
from utils import pseudo_unique_id, pseudo_unique_id_radio
from utils import SERVICE_TYPE_RADIO

#: default/fallback value for local timezone
#: as the enigma2 API returns localised timestamps (not UTC!) one need to set
#: the correct timezone or the results will not match the values shown on
#: the enigma2 device.
DEFAULT_LOCALTIMEZONE = "Europe/Berlin"

#: datetime format as used for *realbegin*/*realend* key/value pairs of timer
#: items returned by enigma2 API
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

#: type identifier for timer items
ITEM_TYPE_TIMER = 'timer'

#: type identifier for EPG items
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

EVENT_HEADER_FMT = u'{start_time} -- {stop_time} #{item_id:06d} {service_name}'
EVENT_TITLE_FMT = u'{title}{shortinfo}'
EVENT_BODY_FMT = u'{duration} {longinfo}'
EVENT_PSEUDO_ID_FMT = u'PSEUDO ID: {pseudo_id}'


class EEvent(dict):
    """
    This is a thin wrapper class to allow unified access to event items' data.

    As the data keys for EPG and timer events (returned by the enigma2 API)
    are different for the same data values the data is exposed as attributes
    common to all item types.

    Attribute names are inspired by names used in the ETSI EPG specification
    documents.

        #. ETSI EN 300 707 V1.2.1 (2002-12)
        #. ETSI ETR 288 TECHNICAL October 1996

    .. seealso::

        * http://www.etsi.org/deliver/etsi_en/300700_300799/300707/01.02.01_40/en_300707v010201o.pdf
        * http://www.etsi.org/deliver/etsi_etr/200_299/288/01_60/etr_288e01p.pdf

    """

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
        >>> timer_d.pseudo_id
        'c2e47cb10e10e6c7aaefadae26fdba2d35a9411a'
        >>> epg_d.pseudo_id is None
        True
        >>> timer_d.global_id == epg_d.global_id
        True
        >>> from example_data import example_timer_radio, expected_radio
        >>> timer_r = EEvent(example_timer_radio)
        >>> timer_r.title == expected_radio['title']
        True
        >>> timer_r.shortinfo == expected_radio['shortinfo']
        True
        >>> timer_r.service_name == expected_radio['service_name']
        True
        >>> timer_r.global_id
        '1:0:2:6f37:431:a401:ffff0000:0:0:0:6784'
        >>> timer_r.pseudo_id
        '9c357fbab2a36d905a9c2658eac6c11df1d23a85'
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

        psr = parse_servicereference(self.service_reference)
        self.service_reference = create_servicereference(psr)

        self.longinfo = self.longinfo.replace(u"\u008a", "\n")

        self.pseudo_id = None

        try:
            self.pseudo_id = pseudo_unique_id(self)
        except Exception:
            try:
                if psr['service_type'] == SERVICE_TYPE_RADIO:
                    self.pseudo_id = pseudo_unique_id_radio(self)
            except Exception:
                pass

    def get_global_id(self):
        return '{:s}{:d}'.format(self.service_reference, self.item_id)
    global_id = property(get_global_id)

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

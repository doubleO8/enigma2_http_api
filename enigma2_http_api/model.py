#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pprint
import datetime

import pytz

DEFAULT_LOCALTIMEZONE = "Europe/Berlin"

# '25.08.2017 00:10'
DT_FORMAT__REAL__KEYS = '%d.%m.%Y %H:%M'

ID = 'ID'
BEGIN_TIMESTAMP = 'BEGIN_TIMESTAMP'
END_TIMESTAMP = 'END_TIMESTAMP'
DURATION = 'DURATION'
SERVICE_NAME = 'SERVICE_NAME'
SERVICE_REFERENCE = 'SERVICE_REFERENCE'
DESCRIPTION = 'DESCRIPTION'
DESCRIPTION_EXTENDED = 'DESCRIPTION_EXTENDED'
TITLE = 'LABEL'

# ETSI EN 300 707 V1.2.1 (2002-12)
# ETSI ETR 288 TECHNICAL October 1996
_METAMAP_ATTRIBUTES = {
    'item_id': ID,
    'service_name': SERVICE_NAME,
    'service_reference': SERVICE_REFERENCE,
    'title': TITLE,
    'shortinfo': DESCRIPTION,
    'longinfo': DESCRIPTION_EXTENDED,
    # 'start_time': None,
    # 'stop_time': None,
}

_METAMAP_ATTR_REV = {
    BEGIN_TIMESTAMP: 'start_time',
    END_TIMESTAMP: 'stop_time',
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
        BEGIN_TIMESTAMP: 'begin',
        END_TIMESTAMP: 'end',
        DURATION: None,
        SERVICE_NAME: 'servicename',
        SERVICE_REFERENCE: 'serviceref',
        DESCRIPTION: 'description',
        DESCRIPTION_EXTENDED: 'descriptionextended',
    },
    ITEM_TYPE_EPG: {
        ID: 'id',
        TITLE: 'title',
        BEGIN_TIMESTAMP: 'begin_timestamp',
        END_TIMESTAMP: None,
        DURATION: 'duration_sec',
        SERVICE_NAME: 'sname',
        SERVICE_REFERENCE: 'sref',
        DESCRIPTION: 'shortdesc',
        DESCRIPTION_EXTENDED: 'longdesc',
    }
}


class EEvent(dict):
    def __init__(self, *args, **kwargs):
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

        dt_keys = [BEGIN_TIMESTAMP]
        if self._type == ITEM_TYPE_TIMER:
            dt_keys.append(END_TIMESTAMP)

        for dt_key in dt_keys:
            data_key = attr_map[dt_key]
            setattr(self, _METAMAP_ATTR_REV[dt_key],
                    self._localized_dt(self[data_key]))

        if self._type == ITEM_TYPE_EPG:
            self.duration = datetime.timedelta(seconds=self[attr_map[DURATION]])
            self.stop_time = self.start_time + self.duration
        elif self._type == ITEM_TYPE_TIMER:
            self.duration = self.stop_time - self.start_time
        else:
            raise ValueError("Unsupported type {!r}".format(self._type))

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
    from example_data import example_epg, example_timer

    epg_d = EEvent(example_epg)
    timer_d = EEvent(example_timer)

    victims = [epg_d, timer_d]
    for victim in victims:
        print victim
        print repr(victim)
        print victim.title
        print victim.shortinfo
        print victim.start_time
        print victim.stop_time
        print victim.duration
        print victim.service_name, victim.service_reference
        # pprint.pprint(victim)

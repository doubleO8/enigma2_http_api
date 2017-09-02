#!/usr/bin/env python
# -*- coding: utf-8 -*-

example_epg = {
    'begin_timestamp': 1503612900,
    'duration_sec': 3300,
    'id': 22997,
    'longdesc': u'',
    'shortdesc': u'Muss ich wirklich dazwischen?',

    'sname': 'zdf_neo',
    'sref': '1:0:1:6D6E:437:66:FFFF0000:0:0:0:',

    'title': u'Orange is the New Black'
}

example_timer = {
    'begin': 1503612600,

    'description': 'Muss ich wirklich dazwischen?',
    'descriptionextended': u"USA 2015\x8aIn Litchfield hat sich die Machtverteilung ver\xe4ndert. Piper genie\xdft ihren Aufstieg, w\xe4hrend die Konflikte zwischen den Gangs zunehmen.\x8aPiper distanziert sich von Alex und wei\xdf nicht, was sie will. Sophia wird attackiert und kommt in Einzelhaft. W\xe4hrenddessen liegt Daya in den Wehen.\x8aDarsteller:\x8aPiper Chapman - Taylor Schilling\x8aLarry Bloom - Jason Biggs\x8aAlex Vause - Laura Prepon\x8aTasha \xa0'Taystee'\xa0 Jefferson - Danielle Brooks\x8aGalina 'Red' Reznikov - Kate Mulgrew\x8aSam Healy - Michael Harney\x8aRegie: Andrew McCarthy u.a.\x8aBuch/Autor: Jenji Kohan u.a.\x8aHD-Produktion\x8aAltersfreigabe: 16",

    'eit': 22997,
    'end': 1503616500,
    'name': 'Orange is the New Black',

    'realbegin': '25.08.2017 00:10',
    'realend': '25.08.2017 01:15',

    'servicename': 'zdf_neo',
    'serviceref': '1:0:1:6D6E:437:66:FFFF0000:0:0:0:'
}

expected = {
    'title': 'Orange is the New Black',
    'shortinfo': 'Muss ich wirklich dazwischen?',
    'item_id': 22997,
    'service_name': 'zdf_neo',
    'service_reference': '1:0:1:6d6e:437:66:ffff0000:0:0:0:'
}

example_timer_radio = {
    "begin": 1504810500,
    "description": "",
    "tags": "",
    "firsttryprepare": True,
    "always_zap": -1,
    "toggledisabled": 1,
    "dontsave": 0,
    "backoff": 0,
    "disabled": 0,
    "asrefs": "",
    "repeated": 0,
    "servicename": "DASDING",
    "duration": 7800,
    "dirname": "None",
    "realend": "07.09.2017 23:05",
    "descriptionextended": "N/A",
    "name": "DASDING Sprechstunde",
    "startprepare": 1504810480,
    "realbegin": "07.09.2017 20:55",
    "end": 1504818300,
    "eit": 6784,
    "vpsplugin_overwrite": False,
    "afterevent": 3,
    "justplay": 0,
    "serviceref": "1:0:2:6F37:431:A401:FFFF0000:0:0:0:",
    "filename": None,
    "toggledisabledimg": "off",
    "state": 0,
    "logentries": [
        [1504339013, 15,
         "record time changed, start prepare is now: Thu Sep 7 20:54:40 2017"]
    ],
    "nextactivation": None,
    "vpsplugin_time": -1,
    "cancelled": False,
    "vpsplugin_enabled": False
}

expected_radio = {
    'title': 'DASDING Sprechstunde',
    'shortinfo': '',
    'item_id': 6784,
    'service_name': 'DASDING',
    'service_reference': '1:0:1:6d6e:437:66:ffff0000:0:0:0:'
}

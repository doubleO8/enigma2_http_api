#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import datetime
import hashlib
import re
import codecs
import sys

# https://wiki.neutrino-hd.de/wiki/Enigma:Services:Formatbeschreibung
# Dezimalwert: 1=TV, 2=Radio, 4=NVod, andere=Daten

SERVICE_TYPE_TV = 1
SERVICE_TYPE_RADIO = 2
SERVICE_TYPE_HDTV = 25

SERVICE_TYPE = {
    'TV': SERVICE_TYPE_TV,
    'HDTV': SERVICE_TYPE_HDTV,
    'RADIO': SERVICE_TYPE_RADIO
}

SERVICE_TYPE_LOOKUP = {v: k for k, v in SERVICE_TYPE.iteritems()}

#: Namespace - DVB-C services
NS_DVB_C = 0xffff0000

#: Namespace - DVB-S services
NS_DVB_S = 0x00c00000

#: Label:Namespace map
NS = {
    'DVB-C': NS_DVB_C,
    'DVB-S': NS_DVB_S
}

#: Namespace:Label lookup map
NS_LOOKUP = {v: k for k, v in NS.iteritems()}

#: list of tuples which may contain title and description of an event
LISTING_ITEM_KEY_PAIRS = [
    ('eventname', 'descriptionExtended'),
    ('title', 'longdesc'),
    ('name', 'descriptionextended'),
    ('eventname', 'description'),
]

# sondern Magnums Leben in Gefahr... 47 Min.
PATTERN_RUNLENGTH = r'\s\d+\sMin\.'
RE_RUNLENGTH = re.compile(PATTERN_RUNLENGTH)


def normalise_servicereference(serviceref):
    """
    Create a normalised representation of *serviceref* to be used e.g. as
    sorting hint

    :param serviceref: service reference
    :return:

    >>> sref = '1:0:1:300:7:85:00c00000:0:0:0:'
    >>> normalise_servicereference(sref)
    '0001:0300:0007:0085:00C00000'
    >>> sref2 = '1:64:A:0:0:0:0:0:0:0::SKY Sport'
    >>> normalise_servicereference(sref2)
    '000A:0000:0000:0000:00000000'
    """
    psref = parse_servicereference(serviceref)
    return '{service_type:04X}:{sid:04X}:{tsid:04X}:{oid:04X}:{ns:08X}'.format(
        **psref)


def parse_servicereference(serviceref):
    """
    Parse a Enigma2 style service reference string representation.

    :param serviceref: Enigma2 style service reference
    :type serviceref: string

    >>> sref = '1:0:1:300:7:85:00c00000:0:0:0:'
    >>> result = parse_servicereference(sref)
    >>> result
    {'service_type': 1, 'oid': 133, 'tsid': 7, 'ns': 12582912, 'sid': 768}
    >>> sref_g = create_servicereference(**result)
    >>> sref_g
    '1:0:1:300:7:85:00c00000:0:0:0:'
    >>> sref_g2 = create_servicereference(result)
    >>> sref_g2
    '1:0:1:300:7:85:00c00000:0:0:0:'
    >>> sref == sref_g
    True
    >>> sref2 = '1:64:A:0:0:0:0:0:0:0::SKY Sport'
    >>> result2 = parse_servicereference(sref2)
    >>> result2
    {'service_type': 10, 'oid': 0, 'tsid': 0, 'ns': 0, 'sid': 0}
    """
    parts = serviceref.split(":")
    sref_data = {
        'service_type': int(parts[2], 16),
        'sid': int(parts[3], 16),
        'tsid': int(parts[4], 16),
        'oid': int(parts[5], 16),
        'ns': int(parts[6], 16)
    }
    return sref_data


def create_servicereference(*args, **kwargs):
    """
    Generate a (Enigma2 style) service reference string representation.

    :param args[0]: Service Reference Parameter as dict
    :type args[0]: :class:`dict`

    :param service_type: Service Type
    :type service_type: int

    :param sid: SID
    :type sid: int

    :param tsid: TSID
    :type tsid: int

    :param oid: OID
    :type oid: int

    :param ns: Enigma2 Namespace
    :type ns: int
    """
    if len(args) == 1 and isinstance(args[0], dict):
        kwargs = args[0]
    service_type = kwargs.get('service_type', 0)
    sid = kwargs.get('sid', 0)
    tsid = kwargs.get('tsid', 0)
    oid = kwargs.get('oid', 0)
    ns = kwargs.get('ns', 0)

    return '{:x}:0:{:x}:{:x}:{:x}:{:x}:{:08x}:0:0:0:'.format(
        1,
        service_type,
        sid,
        tsid,
        oid,
        ns)


def create_picon(*args, **kwargs):
    """
    Generate a (Enigma2 style) program icon string representation.

    :param args[0]: Service Reference Parameter as dict
    :type args[0]: :class:`dict`

    :param service_type: Service Type
    :type service_type: int

    :param sid: SID
    :type sid: int

    :param tsid: TSID
    :type tsid: int

    :param oid: OID
    :type oid: int

    :param ns: Enigma2 Namespace
    :type ns: int
    """
    if len(args) == 1 and isinstance(args[0], dict):
        kwargs = args[0]
    service_type = kwargs.get('service_type', 0)
    sid = kwargs.get('sid', 0)
    tsid = kwargs.get('tsid', 0)
    oid = kwargs.get('oid', 0)
    ns = kwargs.get('ns', 0)
    return '{:x}_0_{:d}_{:x}_{:x}_{:x}_{:x}_0_0_0'.format(
        1,
        service_type,
        sid,
        tsid,
        oid,
        ns).upper() + kwargs.get('extension',
                                 '.png')


def filter_simple_events(data):
    """
    .. code::

        [
            u'begin',
            u'sname',
            u'end',
            u'title',
            u'id',
            u'now_timestamp',
            u'picon',
            u'longdesc',
            u'duration',
            u'duration_sec',
            u'sref',
            u'date',
            u'shortdesc',
            u'progress',
            u'tleft',
            u'begin_timestamp'],


    :param data:
    :return:
    """
    for row in data:
        psref = parse_servicereference(row['sref'])
        yield row['sname'], row['title'], row['longdesc'], '{:04X}'.format(
            psref['ns']), datetime.datetime.fromtimestamp(
            int(row['begin_timestamp']))


def pseudo_unique_id(item):
    """
    Generate a pseudo unique ID for an event item, movie item or timer item.
    The ID is based on the item's title and description attribute.
    Neither title nor description may be empty.

    :param item: event, movie or timer
    :return: generated pseudo ID
    :rtype: str

    >>> pseudo_unique_id({'event': 1})
    Traceback (most recent call last):
        ...
    AssertionError: name or desc may not be None
    >>> pseudo_unique_id({'eventname': 1, 'descriptionExtended': 'bla'})
    Traceback (most recent call last):
        ...
    AttributeError: 'int' object has no attribute 'strip'
    >>> pseudo_unique_id({'eventname': "x", 'descriptionExtended': 'bla'})
    '7a6615ef8ca6b06ac6a837741293759d3083a49c'
    >>> pseudo_unique_id({'eventname': "x", 'description': 'bla'})
    '7a6615ef8ca6b06ac6a837741293759d3083a49c'
    >>> pseudo_unique_id({'eventname': " ", 'descriptionExtended': '  '})
    Traceback (most recent call last):
        ...
    AssertionError: name or desc may not be empty
    >>> pseudo_unique_id({'title': "x", 'longdesc': 'bla'})
    '7a6615ef8ca6b06ac6a837741293759d3083a49c'
    >>> pseudo_unique_id({'name': "x", 'descriptionextended': 'bla'})
    '7a6615ef8ca6b06ac6a837741293759d3083a49c'
    >>> pseudo_unique_id({'name': "x", 'descriptionextended': ' 17 Min.'})
    Traceback (most recent call last):
        ...
    AssertionError: desc_mangled may not be empty
    >>> pseudo_unique_id({'name': "x", 'descriptionextended': 'Bla Bla 17 Min.'})
    '4db3822ad252366e57d9515b1e37d3449a45a0cb'
    >>> pseudo_unique_id({'name': "x", 'descriptionextended': 'Bla Bla 18 Min.'})
    '4db3822ad252366e57d9515b1e37d3449a45a0cb'
    """

    (name, desc) = None, None
    for name_key, desc_key in LISTING_ITEM_KEY_PAIRS:
        try:
            (name, desc) = item[name_key], item[desc_key]
            if desc is not None and desc.strip():
                break
        except KeyError:
            pass

    if None in (name, desc):
        raise AssertionError("name or desc may not be None")
    if '' in (name.strip(), desc.strip()):
        raise AssertionError("name or desc may not be empty")

    desc_mangled = re.sub(RE_RUNLENGTH, '', desc)

    if not desc_mangled.strip():
        raise AssertionError("desc_mangled may not be empty")

    m = hashlib.sha1()
    m.update(name.encode("utf-8"))
    m.update(desc_mangled.encode("utf-8"))
    return m.hexdigest()


def pseudo_unique_id_radio(item):
    return pseudo_unique_id(
        {
            "title": item.get("title"),
            "longdesc": "{:s},{:s}".format(
                item.get("sref"), item.get("date"))
        }
    )


def enigma_trunkname(path):
    """
    Determine the trunk of enigma2 specific files.

    :param path: filename
    :return: trunk

    >>> enigma_trunkname(None)
    Traceback (most recent call last):
        ...
    ValueError: None
    >>> enigma_trunkname('')
    Traceback (most recent call last):
        ...
    ValueError: ''
    >>> enigma_trunkname(2)
    Traceback (most recent call last):
        ...
    ValueError: 2
    >>> enigma_trunkname('somefile')
    Traceback (most recent call last):
        ...
    ValueError: 'somefile' has no extension
    >>> enigma_trunkname('somefile.bla')
    Traceback (most recent call last):
        ...
    ValueError: 'somefile.bla' has bad extension 'bla'
    >>> enigma_trunkname('somefile.bla.bla')
    Traceback (most recent call last):
        ...
    ValueError: 'somefile.bla.bla' has bad extension 'bla'
    >>> enigma_trunkname('somefile.ts')
    'somefile'
    >>> enigma_trunkname('/tmp/somefile.ts')
    'somefile'
    >>> enigma_trunkname('somefile.ts.sc')
    'somefile'
    """
    e_ext_level1 = ('ts', 'eit',)
    e_ext_level2 = ('ap', 'cuts', 'meta', 'sc',)

    try:
        w_path = os.path.basename(path)
    except AttributeError:
        raise ValueError(repr(path))

    if not w_path:
        raise ValueError(repr(path))

    parts = w_path.split('.')

    if len(parts) == 1:
        raise ValueError('{!r} has no extension'.format(path))
    elif len(parts) == 2:
        if not parts[1] in e_ext_level1:
            raise ValueError(
                '{!r} has bad extension {!r}'.format(path, parts[1]))
        return parts[0]
    elif len(parts) == 3:
        if not parts[1] in e_ext_level1:
            raise ValueError(
                '{!r} has bad extension {!r}'.format(path, parts[1]))
        if not parts[2] in e_ext_level2:
            raise ValueError(
                '{!r} has bad extension {!r}'.format(path, parts[2]))
        return parts[0]

    raise ValueError(repr(path))


def set_output_encoding(encoding='utf-8'):
    """
    Stolen from https://stackoverflow.com/
        questions/19696652/piping-output-causes-python-program-to-fail

    When piping to the terminal, python knows the encoding needed, and
    sets it automatically. But when piping to another program (for example,
    | less), python can not check the output encoding. In that case, it
    is None. What I am doing here is to catch this situation for both
    stdout and stderr and force the encoding
    """
    current = sys.stdout.encoding
    if current is None:
        sys.stdout = codecs.getwriter(encoding)(sys.stdout)
    current = sys.stderr.encoding
    if current is None:
        sys.stderr = codecs.getwriter(encoding)(sys.stderr)


if __name__ == '__main__':
    import doctest

    (FAILED, SUCCEEDED) = doctest.testmod()
    print("[doctest] SUCCEEDED/FAILED: {:d}/{:d}".format(SUCCEEDED, FAILED))

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

sys.path.insert(0, '../../')

from enigma2_http_api.model import _METAMAP_ATTRIBUTES
from enigma2_http_api.model import _META_MAP, ITEM_TYPE_EPG, ITEM_TYPE_TIMER
from enigma2_http_api.model import START_TIMESTAMP, STOP_TIMESTAMP, DURATION

rows = []
max_len = 0

attributes = _METAMAP_ATTRIBUTES
more_attributes = {
    'start_time [#f1]_': START_TIMESTAMP,
    'stop_time [#f1]_': STOP_TIMESTAMP,
    'duration [#f2]_': DURATION
}
attributes.update(more_attributes)

for attribute_name in sorted(attributes.keys()):
    key = _METAMAP_ATTRIBUTES[attribute_name]
    portions = [attribute_name]
    for item_type in (ITEM_TYPE_EPG, ITEM_TYPE_TIMER):
        original_name = _META_MAP[item_type].get(key)
        if original_name is None:
            original_name = '-- n/a --'
        portions.append(original_name)
    rows.append(portions)

    for x in portions:
        max_len = max(max_len, len(x))

header_items = ('EEvent attribute', ITEM_TYPE_EPG, ITEM_TYPE_TIMER)
for x in header_items:
    max_len = max(max_len, len(x))

fmt = '{:' + str(max_len) + 's}'
items_per_row = len(header_items)
lines = []
lines.append(' '.join(["=" * max_len for x in range(items_per_row)]))
lines.append(' '.join([fmt.format(x) for x in header_items]))
lines.append(' '.join(["=" * max_len for x in range(items_per_row)]))
for row in rows:
    lines.append(' '.join([fmt.format(x) for x in row]))
lines.append(' '.join(["=" * max_len for x in range(items_per_row)]))
lines.append('')
lines.append('.. rubric:: Footnotes')
lines.append('.. [#f1] :py:class:`datetime.datetime` instances.')
lines.append('.. [#f2] :py:class:`datetime.timedelta` instances.')

print("\n".join(lines))

with open('event_attributes_table.rst', "wb") as target:
    target.write("\n".join(lines))

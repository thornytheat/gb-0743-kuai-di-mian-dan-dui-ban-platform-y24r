from collections import defaultdict
from itertools import combinations

from app.clock import instant, stamp
from app.errors import DomainError
from app.modules.coordinates.box import Box, rectangle, scalar
from app.modules.intake.contract import FIELDS, valid_code
from app.modules.intake.reader import lines

COLS = {'format', 'revision', 'start', 'end', 'paper', 'quiet_mm', 'zones', 'note'}


def normalize(row):
    data = row['data']
    if (set(data) != COLS or not valid_code(data['format']) or type(data['revision']) is not int
            or data['revision'] < 1 or not isinstance(data['zones'], dict) or set(data['zones']) != FIELDS
            or not isinstance(data['note'], str)):
        raise DomainError('BAD_TEMPLATE')
    start, end = instant(data['start']), instant(data['end'])
    if start >= end:
        raise DomainError('BAD_TEMPLATE')
    if not isinstance(data['paper'], list) or len(data['paper']) != 2:
        raise DomainError('BAD_TEMPLATE')
    width, height = map(scalar, data['paper'])
    quiet = scalar(data['quiet_mm'])
    paper = Box(0, 0, width, height)
    if min(width, height, quiet) <= 0 or quiet * 2 >= width:
        raise DomainError('BAD_TEMPLATE')
    if any(not paper.contains(rectangle(zone)) for zone in data['zones'].values()):
        raise DomainError('BAD_TEMPLATE')
    return dict(data, start=stamp(start), end=stamp(end), line=row['line'], raw=row['raw'])


def read_versions(raw):
    rows, encoding = lines(raw)
    groups, excluded = defaultdict(list), []
    accepted = []
    for row in rows:
        if row['code']:
            excluded.append(row)
            continue
        try:
            version = normalize(row)
            groups[version['format'], version['revision']].append(version)
        except DomainError:
            excluded.append(dict(row, code='BAD_TEMPLATE'))
    for group in groups.values():
        conflicts = set()
        for left, right in combinations(group, 2):
            if instant(left['end']) > instant(right['start']) and instant(right['end']) > instant(left['start']):
                conflicts.update((left['line'], right['line']))
        for row in group:
            if row['line'] in conflicts:
                excluded.append(dict(line=row['line'], raw=row['raw'], code='TEMPLATE_CONFLICT'))
            else:
                accepted.append(row)
    return {'input_rows': len(rows), 'encoding': encoding, 'versions': sorted(accepted, key=lambda row: row['line']),
            'excluded': sorted(excluded, key=lambda row: row['line'])}

from collections import Counter, defaultdict

from app.canonical import canonical
from app.clock import instant
from app.errors import DomainError
from .contract import normalize
from .reader import lines


def receive(raw):
    rows, encoding = lines(raw)
    groups = defaultdict(list)
    accepted, rejected = [], []
    for row in rows:
        if row['code']:
            rejected.append(row)
            continue
        try:
            row['data'] = normalize(row['data'])
            groups[row['data']['label']].append(row)
        except DomainError as error:
            rejected.append(dict(row, code=error.code))
    for group in groups.values():
        if len({canonical(row['data']) for row in group}) > 1:
            rejected.extend(dict(row, code='PRINT_CONFLICT') for row in group)
        else:
            accepted.append(group[0])
            rejected.extend(dict(row, code='DUPLICATE_PRINT') for row in group[1:])
    accepted.sort(key=lambda row: (instant(row['data']['at']), row['data']['label']))
    return {'input_rows': len(rows), 'encoding': encoding, 'accepted': accepted,
            'excluded': sorted(rejected, key=lambda row: row['line']),
            'reasons': dict(Counter(row['code'] for row in rejected))}

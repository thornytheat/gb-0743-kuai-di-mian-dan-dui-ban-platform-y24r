from collections import Counter

from app.clock import instant, stamp
from app.errors import DomainError
from app.modules.intake.contract import valid_code
from app.modules.intake.reader import lines

VOID_REASONS = {'JAM': '卡纸', 'SMEAR': '墨迹模糊', 'LOST': '面单遗失'}


def normalize_void(data):
    if (set(data) != {'id', 'label', 'at', 'reason'} or not valid_code(data['id']) or not valid_code(data['label'])
            or not isinstance(data['reason'], str) or data['reason'] not in VOID_REASONS):
        raise DomainError('BAD_VOID')
    return dict(data, at=stamp(instant(data['at'])))


def read_voids(raw):
    entries, _ = lines(raw, allow_empty=True)
    accepted, excluded = [], []
    for entry in entries:
        if entry['code']:
            excluded.append(entry)
            continue
        try:
            accepted.append(dict(entry, data=normalize_void(entry['data'])))
        except DomainError as error:
            excluded.append(dict(entry, code=error.code))
    counts = Counter(entry['data']['id'] for entry in accepted)
    excluded.extend(dict(entry, code='DUPLICATE_VOID') for entry in accepted if counts[entry['data']['id']] > 1)
    return [entry for entry in accepted if counts[entry['data']['id']] == 1], excluded

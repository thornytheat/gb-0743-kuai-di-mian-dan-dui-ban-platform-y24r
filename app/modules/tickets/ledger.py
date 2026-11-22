from app.clock import instant
from .voids import read_voids


def reprint_failure(target, item, previous):
    if previous is None:
        return 'REPRINT_UNKNOWN'
    if previous['parcel'] != item['parcel']:
        return 'REPRINT_PARCEL'
    if previous['state'] != 'revoked':
        return 'REPRINT_NOT_VOID'
    if instant(item['at']) < instant(previous['void']['at']):
        return 'REPRINT_TIME'
    if previous['replaced_by'] or target != previous['label']:
        return 'REPRINT_REUSED'
    return None


def lifecycle(prints, defects, raw_voids):
    voids, excluded_voids = read_voids(raw_voids)
    merged = [(instant(entry['data']['at']), 0, entry['data']['id'], entry) for entry in voids]
    merged += [(instant(entry['data']['at']), 1, entry['data']['label'], entry) for entry in prints]
    labels, latest = {}, {}
    applied = []
    for _, order, key, entry in sorted(merged, key=lambda item: item[:3]):
        row = entry['data']
        if order == 0:
            current = labels.get(row['label'])
            if not current or current['state'] != 'valid':
                excluded_voids.append(dict(entry, code='VOID_NOT_LIVE'))
            else:
                current['state'] = 'revoked'
                current['void'] = dict(row, line=entry['line'], raw=entry['raw'])
                applied.append(current['void'])
            continue
        parcel, replaces = row['parcel'], row['replaces']
        issues = list(defects.get(key, []))
        relation = None
        if replaces:
            relation = reprint_failure(latest.get(parcel), row, labels.get(replaces))
        elif parcel in latest:
            relation = 'DUPLICATE_PARCEL'
        if relation:
            issues.append(relation)
        state = 'isolated' if issues else 'valid'
        labels[key] = {'label': key, 'parcel': parcel, 'at': row['at'], 'line': entry['line'],
                       'state': state, 'codes': issues, 'replaces': replaces, 'replaced_by': None, 'void': None}
        if state == 'valid':
            if replaces:
                labels[replaces]['replaced_by'] = key
            latest[parcel] = key
    return {'labels': list(labels.values()), 'applied': applied,
            'excluded_voids': sorted(excluded_voids, key=lambda row: row['line'])}

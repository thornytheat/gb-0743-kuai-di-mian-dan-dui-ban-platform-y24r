from app.canonical import digest
from app.clock import instant, stamp
from app.config import SAMPLES
from app.errors import DomainError
from app.modules.intake.contract import valid_code
from app.modules.intake.reader import append_row
from .ledger import reprint_failure
from .pipeline import run
from .voids import normalize_void


def sample_sources():
    return {key: (SAMPLES / file).read_bytes() for key, file in
            [('prints', 'prints.jsonl'), ('templates', 'templates.jsonl'), ('parcels', 'parcels.json'), ('voids', 'voids.jsonl')]}


def seed(store):
    if store.active() is None:
        sources = sample_sources()
        store.save(run(sources), sources, None)


def rerun(store, expected):
    if store.active() != expected:
        raise DomainError('STALE_RUN', 409, current=store.active())
    sources = store.sources(expected)
    return store.save(run(sources), sources, expected)


def restore(store, target, expected):
    return store.save(store.find(target), store.sources(target), expected)


def upload(store, expected, raw):
    store.find(expected)
    sources = store.sources(expected)
    sources['prints'] = raw
    return store.save(run(sources), sources, expected)


def record_void(store, expected, label, at, reason):
    snapshot = store.find(expected)
    items = {row['label']: row for row in snapshot['tickets']['labels']}
    if not valid_code(label):
        raise DomainError('BAD_VOID')
    row = normalize_void({'id': 'V-' + digest(label.encode())[:32], 'label': label, 'at': at, 'reason': reason})
    target = items.get(label)
    if target is None or target['state'] != 'valid' or instant(row['at']) <= instant(target['at']):
        raise DomainError('VOID_NOT_LIVE', label=label)
    sources = store.sources(expected)
    sources['voids'] = append_row(sources['voids'], row)
    candidate = run(sources)
    if not any(item['id'] == row['id'] for item in candidate['tickets']['applied']):
        raise DomainError('DUPLICATE_VOID', label=label)
    return store.save(candidate, sources, expected)


def reprint(store, expected, target, label, at):
    snapshot = store.find(expected)
    if not valid_code(label) or not valid_code(target):
        raise DomainError('BAD_PRINT')
    tickets = {row['label']: row for row in snapshot['tickets']['labels']}
    old = tickets.get(target)
    if not old:
        raise DomainError('REPRINT_UNKNOWN', label=target)
    if label in tickets or any((row['data'] or {}).get('label') == label for row in snapshot['intake']['excluded']):
        raise DomainError('LABEL_EXISTS', label=label)
    original = next(entry['data'] for entry in snapshot['intake']['accepted'] if entry['data']['label'] == target)
    row = dict(original, label=label, at=stamp(instant(at)), replaces=target)
    latest = next((item['label'] for item in reversed(snapshot['tickets']['labels'])
                   if item['parcel'] == old['parcel'] and item['state'] != 'isolated'), None)
    if code := reprint_failure(latest, row, old):
        raise DomainError(code, label=target)
    sources = store.sources(expected)
    sources['prints'] = append_row(sources['prints'], row)
    candidate = run(sources)
    new = next(item for item in candidate['tickets']['labels'] if item['label'] == label)
    if new['state'] != 'valid':
        raise DomainError(new['codes'][0], label=label, reasons=new['codes'])
    return store.save(candidate, sources, expected)

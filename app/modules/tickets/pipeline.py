from collections import defaultdict
from time import perf_counter

from app.canonical import manifest
from app.errors import DomainError
from app.modules.barcode.service import compare
from app.modules.coordinates.service import calibrate
from app.modules.intake.service import receive
from app.modules.occlusion.service import check
from app.modules.reconcile.service import reconcile
from app.modules.templates.service import resolve
from .ledger import lifecycle


def run(sources):
    begin = perf_counter()
    intake = receive(sources['prints'])
    prints = intake['accepted']
    templates, bound = resolve(sources['templates'], prints)
    coordinates, physical = calibrate(prints, bound)
    barcode, parcels = compare(prints, sources['parcels'])
    occlusion = check(physical, bound)
    defects = defaultdict(list)
    for row in coordinates:
        if 'code' in row:
            defects[row['label']].append(row['code'])
    for row in barcode:
        defects[row['label']].extend(item['code'] for item in row['checks'] if item['code'])
    for row in occlusion:
        defects[row['label']].extend(sorted({item['code'] for item in row['issues']}))
    tickets = lifecycle(prints, defects, sources['voids'])
    balance = reconcile(intake, tickets, parcels)
    if not balance['ok']:
        raise DomainError('ACCOUNT_MISMATCH', 409)
    return {'manifest': manifest(sources, round((perf_counter() - begin) * 1000, 3)), 'intake': intake,
            'templates': templates, 'coordinates': coordinates, 'barcode': barcode,
            'occlusion': occlusion, 'reconcile': balance, 'tickets': tickets}

from collections import Counter, defaultdict


def reconcile(received, ledger, parcels):
    totals = Counter(row['state'] for row in ledger['labels'])
    totals['isolated'] += len(received['excluded'])
    shipments = defaultdict(list)
    grouped = defaultdict(Counter)
    for row in ledger['labels']:
        grouped[row['parcel']][row['state']] += 1
        if row['state'] == 'valid':
            shipments[row['parcel']].append(row['label'])
    by_parcel = [dict(parcel=parcel, valid=grouped[parcel]['valid'], revoked=grouped[parcel]['revoked'],
                      isolated=grouped[parcel]['isolated'], live_labels=shipments[parcel])
                 for parcel in sorted(set(parcels) | set(grouped))]
    gap = received['input_rows'] - sum(totals.values())
    multiples = [row for row in by_parcel if row['valid'] > 1]
    unissued = sum(not shipments[key] for key in parcels)
    return {'input_rows': received['input_rows'], 'valid': totals['valid'], 'revoked': totals['revoked'],
            'isolated': totals['isolated'], 'gap': gap, 'multiple_live': multiples, 'parcels': by_parcel,
            'parcels_total': len(parcels), 'shippable': len(parcels) - unissued, 'unissued': unissued,
            'ok': gap == 0 and not multiples}

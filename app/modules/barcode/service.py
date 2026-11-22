import json

RULES = {'barcode': ('tracking', 'TRACKING_MISMATCH'), 'route': ('route', 'ROUTE_MISMATCH'),
         'recipient': ('recipient', 'RECIPIENT_MISMATCH')}


def compare(prints, raw_parcels):
    parcels = json.loads(raw_parcels)
    output = []
    for row in prints:
        data = row['data']
        expected = parcels.get(data['parcel'])
        checks = []
        if expected is None:
            checks.append({'code': 'UNKNOWN_PARCEL'})
        else:
            for field, (key, code) in RULES.items():
                seen = data['fields'][field]['value']
                correct = seen.strip() == expected[key]
                checks.append({'field': field, 'seen': seen, 'expected': expected[key], 'code': None if correct else code})
        output.append({'label': data['label'], 'parcel': data['parcel'], 'line': row['line'],
                       'checks': checks, 'ok': all(item['code'] is None for item in checks)})
    return output, parcels

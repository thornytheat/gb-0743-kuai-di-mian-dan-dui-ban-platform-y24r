

def lookup(batch, label):
    return next(row for row in batch['barcode'] if row['label'] == label)


def test_three_authoritative_fields_match(batch):
    row = lookup(batch, 'L-001')
    assert row['ok'] is True
    assert [(item['field'], item['expected']) for item in row['checks']] == [('barcode','00078263100001'), ('route','E-01'), ('recipient','R-001')]


def test_stripping_leading_zero_does_not_match(batch):
    row = lookup(batch, 'L-009')
    first = row['checks'][0]
    assert row['ok'] is False and (first['seen'],first['expected'],first['code']) == ('78263100009','00078263100009','TRACKING_MISMATCH')


def test_outer_whitespace_allowed_but_retained_as_evidence(batch):
    row = lookup(batch, 'L-027')
    assert row['ok'] and row['checks'][0]['seen'] == '  00078263100027  '


def test_route_mismatch_is_independent_of_tracking(batch):
    row = lookup(batch, 'L-010')
    assert [item['code'] for item in row['checks']] == [None, 'ROUTE_MISMATCH', None]


def test_recipient_mismatch_is_not_reported_as_route_error(batch):
    row = lookup(batch, 'L-011')
    assert row['checks'][2] == {'field':'recipient','seen':'R-0111','expected':'R-011','code':'RECIPIENT_MISMATCH'}


def test_unknown_parcel_reports_reference_gap(batch):
    row = lookup(batch, 'L-099')
    assert not row['ok'] and row['parcel'] == '0099' and row['checks'] == [{'code':'UNKNOWN_PARCEL'}]

from copy import deepcopy

from app.modules.reconcile.service import reconcile


def test_physical_prints_balance_without_dropping_malformed_rows(batch):
    row = batch['reconcile']
    assert (row['input_rows'],row['valid'],row['revoked'],row['isolated'],row['gap']) == (39,15,2,22,0)


def test_each_package_can_ship_once(batch):
    result = batch['reconcile']
    assert (result['parcels_total'],result['shippable'],result['unissued']) == (28,15,13)
    assert all(row['valid'] <= 1 for row in result['parcels'])


def test_void_reprint_and_wrong_branch_have_independent_buckets(batch):
    package = next(row for row in batch['reconcile']['parcels'] if row['parcel'] == '0001')
    assert (package['valid'],package['revoked'],package['isolated'],package['live_labels']) == (1,1,1,['L-001-R'])


def test_voided_without_replacement_is_unissued(batch):
    package = next(row for row in batch['reconcile']['parcels'] if row['parcel'] == '0015')
    assert package['valid'] == 0 and package['revoked'] == 1 and package['live_labels'] == []


def test_second_active_label_caught_even_when_input_count_matches(batch):
    ledger = deepcopy(batch['tickets'])
    old = next(row for row in ledger['labels'] if row['label'] == 'L-001')
    old['state'] = 'valid'
    result = reconcile(batch['intake'], ledger, {'0001':{}})
    assert result['gap'] == 0 and not result['ok']
    assert result['multiple_live'][0]['live_labels'] == ['L-001','L-001-R']


def test_lost_print_is_detected_as_one_row_gap(batch):
    ledger = dict(batch['tickets'], labels=batch['tickets']['labels'][1:])
    result = reconcile(batch['intake'], ledger, {'0001':{}})
    assert result['gap'] == 1 and result['ok'] is False

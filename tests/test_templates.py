import json

from app.modules.templates.service import resolve


def by_label(batch, label):
    return next(row for row in batch['templates']['bindings'] if row['label'] == label)


# TRAP-25

def test_same_revision_overlap_is_quarantined_without_losing_older_versions(batch):
    result = batch['templates']
    assert [(row['line'], row['code']) for row in result['excluded']] == [(3, 'TEMPLATE_CONFLICT'), (4, 'TEMPLATE_CONFLICT'), (5, 'BAD_TEMPLATE')]
    assert by_label(batch, 'L-020')['revision'] == 2


# TRAP-23

def test_half_open_boundaries_choose_new_revision_then_fall_back(batch):
    assert [by_label(batch, name)['revision'] for name in ('L-018', 'L-019', 'L-021', 'L-022')] == [1, 2, 1, None]


def test_unknown_format_cannot_bind_other_template(batch):
    assert by_label(batch, 'L-013') == {'label':'L-013', 'line':None, 'revision':None}


def test_invalid_quiet_zone_value_is_isolated(batch):
    row = batch['templates']['excluded'][-1]
    assert row['line'] == 5 and json.loads(row['raw'])['quiet_mm'] == 0


def test_format_whose_only_version_is_invalid_stays_unbound(batch, sources):
    p = dict(batch['intake']['accepted'][0]['data'], format='CN101')
    result, lookup = resolve(sources['templates'], [{'data': p}])
    assert lookup['L-001'] is None and len(result['versions']) == 2


def test_shifts_within_same_revision_can_touch_without_conflict(batch):
    first = json.loads(batch['templates']['versions'][0]['raw'])
    second = dict(first, start=first['end'], end='2026-11-20T11:00:00+08:00')
    raw = ('\n'.join(json.dumps(row) for row in (first, second))).encode()
    print_row = dict(batch['intake']['accepted'][0]['data'], at=second['start'])
    result, lookup = resolve(raw, [{'data': print_row}])
    assert result['excluded'] == [] and lookup['L-001']['line'] == 2

import io
import json

from app.modules.intake.service import receive


# TRAP-02 TRAP-08

def test_bom_and_leading_zero_packaging(batch):
    intake = batch['intake']
    first = intake['accepted'][0]
    assert (intake['encoding'], first['data']['parcel'], first['line']) == ('UTF-8 BOM', '0001', 1)


# TRAP-13

def test_late_file_rows_are_sorted_by_actual_time(batch):
    rows = batch['intake']['accepted']
    index = next(i for i, row in enumerate(rows) if row['data']['label'] == 'L-001-R')
    assert rows[index]['line'] == 29 and rows[index + 1]['data']['label'] == 'L-001-B'
    assert rows[index - 1]['data']['label'] == 'L-012'


# TRAP-14

def test_conflicting_repeats_quarantine_both_and_identical_retries_keep_one(batch):
    result = batch['intake']
    groups = [(row['line'], row['data']['label'], row['code']) for row in result['excluded'] if row['data']]
    assert groups == [(24, 'L-024', 'PRINT_CONFLICT'), (35, 'L-025', 'DUPLICATE_PRINT'), (36, 'L-024', 'PRINT_CONFLICT')]
    assert [row['line'] for row in result['accepted'] if row['data']['label'] == 'L-025'] == [25]


# TRAP-16

def test_truncated_last_payload_is_isolated_with_exact_raw(batch):
    bad, = [row for row in batch['intake']['excluded'] if row['code'] == 'BAD_JSON_LINE']
    assert (bad['line'], bad['raw']) == (37, '{"label":"broken","fields":')
    assert len(batch['intake']['accepted']) == 33


# TRAP-19

def test_duplicate_json_key_does_not_silently_overwrite(batch):
    bad, = [row for row in batch['intake']['excluded'] if row['code'] == 'DUPLICATE_KEY']
    assert bad['line'] == 38 and 'L-SWAP' in bad['raw'] and bad['data'] is None


# TRAP-01 TRAP-03

def test_gb18030_crlf_and_lf_preserve_records(batch):
    row = batch['intake']['accepted'][0]['data']
    row = dict(row, fields={**row['fields'], 'recipient': {'value': '运转班', 'box': [12,70,68,9]}})
    line = json.dumps(row, ensure_ascii=False).encode('gb18030')
    out = receive(line + b'\r\n{}\n')
    assert out['encoding'] == 'GB18030' and out['accepted'][0]['data']['fields']['recipient']['value'] == '运转班'
    assert (out['excluded'][0]['line'], out['excluded'][0]['code']) == (2, 'BAD_PRINT')


def test_bad_upload_returns_422_without_changing_batch(client, batch_id):
    response = client.post('/api/intake', data={'expected': batch_id, 'prints': (io.BytesIO(b''), 'empty.jsonl')})
    assert (response.status_code, response.json['code']) == (422, 'EMPTY_INPUT')
    assert client.get('/health').json['run'] == batch_id


def test_unicode_line_separator_inside_json_is_not_a_record_break(batch):
    row = batch['intake']['accepted'][0]['data']
    row = dict(row, fields={**row['fields'], 'recipient': {'value': '收件\u2028A', 'box': [12,70,68,9]}})
    out = receive(json.dumps(row, ensure_ascii=False).encode())
    assert out['input_rows'] == 1
    assert out['accepted'][0]['data']['fields']['recipient']['value'] == '收件\u2028A'


def test_decimal_tokens_do_not_allow_numeric_identifiers_or_values(batch):
    raw = json.dumps(batch['intake']['accepted'][0]['data'])
    numeric_label = raw.replace('"L-001"', '1e2')
    numeric_tracking = raw.replace('"00078263100001"', '7.82631e11')
    result = receive((numeric_label + '\n' + numeric_tracking).encode())
    assert result['accepted'] == [] and result['reasons'] == {'BAD_PRINT': 2}

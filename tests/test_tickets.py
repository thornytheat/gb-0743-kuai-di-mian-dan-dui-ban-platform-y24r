from concurrent.futures import ThreadPoolExecutor

from app.canonical import canonical, digest
from app.modules.tickets.service import seed


def all_tickets(batch):
    return {row['label']:row for row in batch['tickets']['labels']}


def test_void_is_prior_to_same_instant_reprint(batch):
    old, new = (all_tickets(batch)[key] for key in ('L-001','L-001-R'))
    assert old['void']['at'] == new['at'] and old['void']['line'] == 1
    assert (old['state'],old['replaced_by'],new['state'],new['replaces']) == ('revoked','L-001-R','valid','L-001')


def test_still_live_foreign_and_used_targets_are_isolated(batch):
    labels = all_tickets(batch)
    for key, code in [('L-002-A','REPRINT_NOT_VOID'), ('L-014-Q','REPRINT_PARCEL'), ('L-001-B','REPRINT_REUSED'), ('L-016-D','DUPLICATE_PARCEL')]:
        assert labels[key]['codes'] == [code] and labels[key]['state'] == 'isolated'


def test_isolated_stock_is_not_voidable(batch):
    [row] = batch['tickets']['excluded_voids']
    assert (row['line'],row['code'],row['data']['label']) == (3,'VOID_NOT_LIVE','L-005')


def test_ticket_and_all_seven_entry_points(client, batch_id):
    html = client.get('/').get_data(as_text=True)
    assert '面单坐标棋盘' in html and '登记作废与重打' in html
    for key in ('intake','templates','coordinates','barcode','occlusion','reconcile','tickets'):
        response = client.get(f'/api/{key}?run={batch_id}')
        assert response.status_code == 200 and response.json['data'] and response.json['id'] == batch_id


def test_reprint_archives_chain_and_updates_ship_count(client, batch_id):
    body = {'expected':batch_id,'target':'L-015','label':'L-015-NEW','at':'2026-11-20T08:38:00+08:00'}
    response = client.post('/api/tickets/reprint', json=body)
    assert response.status_code == 200 and response.json['created']
    output = client.get('/api/tickets').json['data']['labels']
    assert next(row for row in output if row['label'] == 'L-015')['replaced_by'] == 'L-015-NEW'
    assert client.get('/api/reconcile').json['data']['shippable'] == 16
    duplicate_retry = client.post('/api/tickets/reprint', json=body)
    assert duplicate_retry.json['id'] == response.json['id'] and not duplicate_retry.json['created']


def test_reprint_before_void_or_without_void_fails(client, batch_id):
    early = {'expected':batch_id,'target':'L-015','label':'L-015-NEW','at':'2026-11-20T08:36:00+08:00'}
    assert client.post('/api/tickets/reprint',json=early).json['code'] == 'REPRINT_TIME'
    assert client.post('/api/tickets/reprint',json=dict(early,target='L-002')).json['code'] == 'REPRINT_NOT_VOID'
    assert client.get('/api/runs').json['history'][0]['id'] == batch_id


def test_reprint_outside_version_window_keeps_the_archived_old_batch(client, batch_id):
    response = client.post('/api/tickets/reprint', json={'expected':batch_id, 'target':'L-015',
                            'label':'L-015-NEW', 'at':'2026-11-20T10:30:00+08:00'})
    assert (response.status_code, response.json['code']) == (422, 'NO_TEMPLATE')
    assert client.get('/health').json['run'] == batch_id
    packages = client.get('/api/reconcile').json['data']
    assert packages['revoked'] == 2 and packages['shippable'] == 15


# TRAP-26

def test_void_new_version_rejects_stale_write_and_restores_original(client, batch_id):
    command = {'expected':batch_id,'label':'L-002','at':'2026-11-20T08:30:00+08:00','reason':'LOST'}
    new = client.post('/api/tickets/void',json=command).json['id']
    assert client.get('/api/reconcile').json['data']['valid'] == 14
    stale = client.post('/api/tickets/void',json=dict(command,label='L-003'))
    assert (stale.status_code,stale.json['code']) == (409,'STALE_RUN')
    restored = client.post('/api/runs/restore',json={'expected':new,'target':batch_id})
    assert restored.json['id'] == batch_id and restored.json['changed']
    assert len(client.get('/api/runs').json['history']) == 2


def test_seed_replay_and_evidence_are_stable(client, batch_id, app, sources):
    url = f'/api/runs/{batch_id}/evidence.json'
    before = client.get(url)
    seed(app.extensions['batch_store'])
    refreshed = client.post('/api/runs/rerun',json={'expected':batch_id})
    assert refreshed.json == {'id':batch_id,'created':False,'changed':False}
    assert client.get(url).data == before.data and 'attachment' in before.headers['Content-Disposition']
    bundle = before.json['evidence']
    assert before.json['sha256'] == digest(canonical(bundle).encode())
    assert bundle['manifest']['inputs']['prints']['sha256'] == digest(sources['prints'])
    assert bundle['reconcile']['gap'] == 0 and bundle['intake']['excluded']


def test_concurrent_repeat_creates_single_archive(app, batch_id):
    def submit(_):
        return app.test_client().post('/api/tickets/void',json={'expected':batch_id,'label':'L-002','at':'2026-11-20T08:29:00+08:00','reason':'JAM'}).json
    with ThreadPoolExecutor(2) as pool:
        one, two = pool.map(submit, range(2))
    assert one['id'] == two['id'] and sorted([one['created'],two['created']]) == [False,True]


def test_storage_failure_keeps_all_four_original_files_and_current_pointer(app, client, batch_id):
    db = app.extensions['batch_store']
    with db.transaction() as tx:
        tx.execute("CREATE TRIGGER reject_update BEFORE UPDATE ON current_batch BEGIN SELECT RAISE(ABORT,'test'); END")
    response = client.post('/api/tickets/void', json={'expected':batch_id,'label':'L-002','at':'2026-11-20T08:29:00+08:00','reason':'JAM'})
    assert (response.status_code,response.json['code']) == (503,'STORE_UNAVAILABLE')
    with db.transaction() as tx:
        assert tx.execute('SELECT count(*) FROM batch').fetchone() == (1,)
        assert tx.execute('SELECT count(*) FROM source').fetchone() == (4,)
    assert db.active() == batch_id

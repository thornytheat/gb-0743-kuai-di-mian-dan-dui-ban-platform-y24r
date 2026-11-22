import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .canonical import canonical
from .errors import DomainError

TABLES = '''
CREATE TABLE IF NOT EXISTS batch (id TEXT PRIMARY KEY, created TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS source (run_id TEXT NOT NULL REFERENCES batch(id), name TEXT NOT NULL,
                                   raw BLOB NOT NULL, PRIMARY KEY (run_id, name));
CREATE TABLE IF NOT EXISTS current_batch (slot INTEGER PRIMARY KEY CHECK (slot = 1),
                                          run_id TEXT NOT NULL REFERENCES batch(id));
'''


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.transaction() as db:
            db.executescript(TABLES)

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.execute('PRAGMA foreign_keys = ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _active(db):
        row = db.execute('SELECT run_id FROM current_batch WHERE slot=1').fetchone()
        return row[0] if row else None

    def active(self):
        with self.transaction() as db:
            return self._active(db)

    def find(self, run_id=None):
        with self.transaction() as db:
            if run_id is None:
                row = db.execute('SELECT payload FROM batch JOIN current_batch ON batch.id=current_batch.run_id').fetchone()
            else:
                row = db.execute('SELECT payload FROM batch WHERE id=?', (run_id,)).fetchone()
        if not row:
            raise DomainError('RUN_NOT_FOUND', 404)
        return json.loads(row[0])

    def sources(self, run_id):
        with self.transaction() as db:
            return dict(db.execute('SELECT name, raw FROM source WHERE run_id=?', (run_id,)))

    def history(self):
        sql = '''SELECT batch.id, created, batch.id=current_batch.run_id, json_extract(payload,'$.reconcile.input_rows')
                 FROM batch CROSS JOIN current_batch ORDER BY created DESC, batch.id'''
        with self.transaction() as db:
            return [{'id': key, 'created': created, 'active': bool(active), 'rows': rows}
                    for key, created, active, rows in db.execute(sql)]

    def save(self, snapshot, sources, expected):
        key = snapshot['manifest']['id']
        with self.transaction() as db:
            db.execute('BEGIN IMMEDIATE')
            active = self._active(db)
            old = db.execute('SELECT payload FROM batch WHERE id=?', (key,)).fetchone()
            if old:
                previous = json.loads(old[0])
                check = dict(snapshot, manifest=dict(snapshot['manifest']))
                for name in ('created', 'elapsed_ms'):
                    check['manifest'][name] = previous['manifest'][name]
                if check != previous:
                    raise DomainError('REPLAY_DRIFT', 409)
                if active == key:
                    return {'id': key, 'created': False, 'changed': False}
            if active != expected:
                raise DomainError('STALE_RUN', 409, current=active)
            if not old:
                db.execute('INSERT INTO batch VALUES (?, ?, ?)', (key, snapshot['manifest']['created'], canonical(snapshot)))
                db.executemany('INSERT INTO source VALUES (?, ?, ?)', [(key, name, raw) for name, raw in sources.items()])
            db.execute('INSERT INTO current_batch VALUES (1, ?) ON CONFLICT(slot) DO UPDATE SET run_id=excluded.run_id', (key,))
            return {'id': key, 'created': not old, 'changed': key != expected}

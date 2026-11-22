from flask import Blueprint, Response, jsonify

from app.canonical import canonical
from app.web import payload, snapshot, stage, store
from .evidence import package
from .service import record_void, reprint, rerun, restore

bp = Blueprint('tickets', __name__)


@bp.get('/api/tickets')
def trace():
    return stage('tickets')


@bp.post('/api/tickets/void')
def revoke():
    return jsonify(record_void(store(), **payload('expected', 'label', 'at', 'reason')))


@bp.post('/api/tickets/reprint')
def replace():
    return jsonify(reprint(store(), **payload('expected', 'target', 'label', 'at')))


@bp.get('/api/runs')
def history():
    run = snapshot()
    return jsonify(manifest=run['manifest'], balance=run['reconcile'], history=store().history())


@bp.post('/api/runs/rerun')
def replay():
    return jsonify(rerun(store(), **payload('expected')))


@bp.post('/api/runs/restore')
def rollback():
    return jsonify(restore(store(), **payload('target', 'expected')))


@bp.get('/api/runs/<run_id>/evidence.json')
def evidence(run_id):
    run = store().find(run_id)
    return Response(canonical(package(run)) + '\n', mimetype='application/json',
                    headers={'Content-Disposition': f'attachment; filename="label-register-{run_id[:12]}.json"'})

from flask import Blueprint, jsonify, request

from app.config import MAX_BYTES
from app.errors import DomainError
from app.modules.tickets.service import upload
from app.web import stage, store

bp = Blueprint('intake', __name__)


@bp.get('/api/intake')
def review():
    return stage('intake')


@bp.post('/api/intake')
def receive():
    provided = request.files.get('prints')
    if provided is None:
        raise DomainError('UPLOAD_REQUIRED')
    expected = request.form.get('expected')
    if not expected:
        raise DomainError('BAD_REQUEST')
    return jsonify(upload(store(), expected, provided.stream.read(MAX_BYTES + 1)))

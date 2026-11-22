from flask import Blueprint

from app.web import stage

bp = Blueprint('reconcile', __name__)


@bp.get('/api/reconcile')
def inspect():
    return stage('reconcile')

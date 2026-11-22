from flask import Blueprint

from app.web import stage

bp = Blueprint('barcode', __name__)


@bp.get('/api/barcode')
def inspect():
    return stage('barcode')

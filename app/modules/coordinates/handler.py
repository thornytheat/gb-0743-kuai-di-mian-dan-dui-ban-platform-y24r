from flask import Blueprint

from app.web import stage

bp = Blueprint('coordinates', __name__)


@bp.get('/api/coordinates')
def inspect():
    return stage('coordinates')

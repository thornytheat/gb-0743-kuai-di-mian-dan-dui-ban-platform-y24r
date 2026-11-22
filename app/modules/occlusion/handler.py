from flask import Blueprint

from app.web import stage

bp = Blueprint('occlusion', __name__)


@bp.get('/api/occlusion')
def inspect():
    return stage('occlusion')

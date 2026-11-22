from flask import Blueprint

from app.web import stage

bp = Blueprint('templates', __name__)


@bp.get('/api/templates')
def inspect():
    return stage('templates')

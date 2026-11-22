import os
import sqlite3

from flask import Flask, jsonify, render_template
from werkzeug.exceptions import RequestEntityTooLarge

from .config import MAX_BYTES
from .errors import DomainError
from .modules.barcode.handler import bp as barcode
from .modules.coordinates.handler import bp as coordinates
from .modules.intake.handler import bp as intake
from .modules.occlusion.handler import bp as occlusion
from .modules.reconcile.handler import bp as reconcile
from .modules.templates.handler import bp as templates
from .modules.tickets.handler import bp as tickets
from .modules.tickets.service import seed
from .modules.tickets.voids import VOID_REASONS
from .reasons import LABELS
from .store import Store


def create_app(path=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = MAX_BYTES + 32 * 1024
    db = Store(path or os.getenv('LABEL_DB', 'var/labels.sqlite3'))
    app.extensions['batch_store'] = db
    seed(db)
    for blueprint in (intake, templates, coordinates, barcode, occlusion, reconcile, tickets):
        app.register_blueprint(blueprint)

    @app.errorhandler(DomainError)
    def error_response(error):
        return jsonify(code=error.code, message=LABELS[error.code], details=error.details), error.status

    @app.errorhandler(RequestEntityTooLarge)
    def oversize(_):
        return error_response(DomainError('INPUT_TOO_LARGE', 413))

    @app.errorhandler(sqlite3.Error)
    def persistence(error):
        app.logger.error('批次存储失败', exc_info=error)
        return error_response(DomainError('STORE_UNAVAILABLE', 503))

    @app.get('/')
    def workbench():
        return render_template('workbench.html', labels=LABELS, void_reasons=VOID_REASONS)

    @app.get('/health')
    def health():
        return jsonify(status='ok', run=db.active())

    return app

from flask import current_app, jsonify, request

from .errors import DomainError


def store():
    return current_app.extensions['batch_store']


def snapshot():
    return store().find(request.args.get('run'))


def stage(name):
    run = snapshot()
    return jsonify(id=run['manifest']['id'], data=run[name])


def payload(*fields):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != set(fields) or any(not isinstance(value, str) or not value for value in data.values()):
        raise DomainError('BAD_REQUEST', fields=list(fields))
    return data

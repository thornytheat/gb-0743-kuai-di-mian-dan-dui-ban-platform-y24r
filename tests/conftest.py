import pytest

from app.main import create_app
from app.modules.tickets.pipeline import run
from app.modules.tickets.service import sample_sources


@pytest.fixture(scope='session')
def sources():
    return sample_sources()


@pytest.fixture(scope='session')
def batch(sources):
    return run(sources)


@pytest.fixture
def app(tmp_path):
    return create_app(tmp_path / 'proof.sqlite3')


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def batch_id(client):
    return client.get('/api/runs').json['manifest']['id']

from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {'greetings': 'NMDC users!'}

import io
import os
import zipfile
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from flask import Flask
from flask_login import LoginManager

import app.modules.cart.routes as cart_routes
from app.modules.cart import cart_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(cart_bp)
    lm = LoginManager()
    lm.init_app(app)

    @lm.user_loader
    def _load_user(user_id):
        u = MagicMock()
        u.is_authenticated = True
        try:
            u.id = int(user_id)
        except Exception:
            u.id = user_id
        return u

    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def login_client(client, user_id="1"):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)


def make_file_model(filename="file.dat", user_id=2, dataset_id=10, title="T", description="D", authors=None):
    if authors is None:
        authors = []
    fm_meta = SimpleNamespace(filename=filename, title=title, description=description, authors=authors)
    data_set = SimpleNamespace(user_id=user_id)
    fm = SimpleNamespace(id=123, fm_meta_data=fm_meta, data_set=data_set, data_set_id=dataset_id)
    return fm


def test_cart_count_returns_json(monkeypatch, app, client):
    mock_cart_service = MagicMock()
    mock_cart_service.view_cart.return_value = [{"cart_item_id": 1}, {"cart_item_id": 2}]
    monkeypatch.setattr(cart_routes, "cart_service", mock_cart_service)

    login_client(client)
    resp = client.get("/user/cart/count")
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {"count": 2}


def test_add_to_cart_missing_item_id(monkeypatch, app, client):
    mock_cart_service = MagicMock()
    monkeypatch.setattr(cart_routes, "cart_service", mock_cart_service)

    login_client(client)
    resp = client.post("/filemodel/cart/add", json={})
    assert resp.status_code == 400
    assert resp.is_json
    assert "No item_id provided" in resp.get_json()["message"]


def test_add_to_cart_delegates_to_service(monkeypatch, app, client):
    mock_cart_service = MagicMock()
    mock_cart_service.add_to_cart.return_value = ({"message": "ok"}, 200)
    monkeypatch.setattr(cart_routes, "cart_service", mock_cart_service)

    login_client(client)
    resp = client.post("/filemodel/cart/add", json={"item_id": 55})
    assert resp.status_code == 200
    mock_cart_service.add_to_cart.assert_called_once_with(1, 55)


def test_delete_from_cart_calls_service(monkeypatch, app, client, capsys):
    mock_cart_service = MagicMock()
    mock_cart_service.delete_from_cart.return_value = ({"message": "removed"}, 200)
    monkeypatch.setattr(cart_routes, "cart_service", mock_cart_service)

    login_client(client)
    resp = client.post("/user/cart/delete", json={"item_id": 99})
    assert resp.status_code == 200
    mock_cart_service.delete_from_cart.assert_called_once_with(1, 99)


def test_create_dataset_post_invalid_form(monkeypatch, app, client):
    mock_cart_service = MagicMock()

    class FakeForm:

        def validate_on_submit(self):
            return False

        @property
        def errors(self):
            return {"field": ["error"]}

    monkeypatch.setattr(cart_routes, "cart_service", mock_cart_service)
    monkeypatch.setattr(cart_routes, "CartCreateDatasetForm", lambda: FakeForm())

    login_client(client)
    resp = client.post("/user/cart/create", data={})
    assert resp.status_code == 400
    assert resp.is_json
    assert "field" in resp.get_json()["message"]


def test_create_dataset_post_delegates_to_service(monkeypatch, app, client):
    mock_cart_service = MagicMock()

    class FakeForm:
        def validate_on_submit(self):
            return True

    mock_cart_service.create_dataset.return_value = ({"message": "created"}, 201)

    monkeypatch.setattr(cart_routes, "cart_service", mock_cart_service)
    monkeypatch.setattr(cart_routes, "CartCreateDatasetForm", lambda: FakeForm())

    login_client(client)
    resp = client.post("/user/cart/create", data={})
    assert resp.status_code == 201
    mock_cart_service.create_dataset.assert_called_once()


def test_download_cart_empty(monkeypatch, app, client):
    mock_cart_service = MagicMock()
    mock_cart_service.view_cart.return_value = []
    monkeypatch.setattr(cart_routes, "cart_service", mock_cart_service)

    login_client(client)
    resp = client.get("/user/cart/download")
    assert resp.status_code == 400
    assert resp.is_json
    assert "Cart is empty" in resp.get_json()["message"]


def test_download_cart_creates_zip_and_returns_file(monkeypatch, tmp_path, app, client):
    tmpdir = str(tmp_path)
    monkeypatch.setenv("WORKING_DIR", tmpdir)

    user_id = 7
    dataset_id = 33
    filename = "myfile.txt"
    upload_folder = os.path.join(tmpdir, "uploads", f"user_{user_id}", f"dataset_{dataset_id}")
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    with open(file_path, "wb") as fh:
        fh.write(b"hello zip")

    mock_cart_service = MagicMock()
    mock_fm_service = MagicMock()

    mock_cart_service.view_cart.return_value = [{"cart_item_id": 1, "file_model_id": 123}]
    fm = make_file_model(filename=filename, user_id=user_id, dataset_id=dataset_id)
    mock_fm_service.get_by_id.return_value = fm

    monkeypatch.setattr(cart_routes, "cart_service", mock_cart_service)
    monkeypatch.setattr(cart_routes, "fm_service", mock_fm_service)

    login_client(client)
    resp = client.get("/user/cart/download")
    assert resp.status_code == 200
    assert resp.mimetype == "application/zip"
    zip_bytes = resp.get_data()
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    names = zf.namelist()
    assert filename in names
    with zf.open(filename) as f:
        assert f.read() == b"hello zip"

import os
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from app.modules.pixchecker import pixchecker_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(pixchecker_bp)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def make_hubfile_mock(path):
    m = MagicMock()
    m.get_path.return_value = path
    return m


@patch("app.modules.pixchecker.routes.HubfileService")
def test_check_pix_valid(MockHubfileService, client):
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    fixture = os.path.join(fixtures_dir, "correct.pix")

    mock_hub = make_hubfile_mock(fixture)
    MockHubfileService.return_value.get_or_404.return_value = mock_hub

    resp = client.get("/pixchecker/check_pix/10")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("message") == "Valid Model"


@patch("app.modules.pixchecker.routes.HubfileService")
def test_check_pix_invalid(MockHubfileService, client):
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    fixture = os.path.join(fixtures_dir, "incorrect.pix")

    mock_hub = make_hubfile_mock(fixture)
    MockHubfileService.return_value.get_or_404.return_value = mock_hub

    resp = client.get("/pixchecker/check_pix/5")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "errors" in data and len(data["errors"]) > 0

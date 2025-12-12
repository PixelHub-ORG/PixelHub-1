from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from flask import Flask

from app.modules.badge.routes import badge_bp, badge_svg, badge_svg_download, estimate_text_width, make_segment


@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(badge_bp)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_dataset():
    ds_mock = {
        "title": "Test Dataset",
        "downloads": 42,
        "doi": "10.1234/testdoi",
        "url": "http://example.com/dataset",
    }
    return ds_mock


@patch("app.modules.badge.routes.get_dataset")
def test_badge_svg_download_success(mock_get_dataset, client, mock_dataset):
    mock_get_dataset.return_value = mock_dataset
    response = client.get("/badge/1.svg")

    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"
    assert f"{mock_dataset['downloads']} DL" in response.get_data(as_text=True)
    assert response.headers["Content-Disposition"] == 'attachment; filename="badge_1.svg"'
    assert response.headers["Access-Control-Allow-Origin"] == "*"
    assert response.headers["Cache-Control"] == "no-cache"


@patch("app.modules.badge.routes.get_dataset")
def test_badge_svg_download_not_found(mock_get_dataset, client):
    mock_get_dataset.return_value = None
    response = client.get("/badge/999.svg")

    assert response.status_code == 404
    assert b"Dataset not found" in response.data


@patch("app.modules.badge.routes.get_dataset")
def test_badge_svg_success(mock_get_dataset, client, mock_dataset):
    mock_get_dataset.return_value = mock_dataset
    response = client.get("/badge/1/svg")

    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"
    assert f"{mock_dataset['downloads']} DL" in response.get_data(as_text=True)
    assert "Content-Disposition" not in response.headers
    assert response.headers["Access-Control-Allow-Origin"] == "*"


@patch("app.modules.badge.routes.get_dataset")
def test_badge_svg_not_found(mock_get_dataset, client):
    mock_get_dataset.return_value = None
    response = client.get("/badge/999/svg")

    assert response.status_code == 404
    assert b"Dataset not found" in response.data


@patch("app.modules.badge.routes.get_dataset")
@patch("app.modules.badge.routes.url_for")
def test_badge_embed_success(mock_url_for, mock_get_dataset, client, mock_dataset):
    mock_get_dataset.return_value = mock_dataset
    mock_url_for.return_value = "http://example.com/badge/1/svg"

    response = client.get("/badge/1/embed")

    assert response.status_code == 200
    data = response.get_json()
    assert "markdown" in data
    assert "html" in data
    assert mock_dataset["title"] in data["markdown"]
    assert str(mock_dataset["downloads"]) in data["markdown"]
    assert mock_dataset["doi"] in data["markdown"]
    assert "http://example.com/badge/1/svg" in data["html"]


@patch("app.modules.badge.routes.get_dataset")
def test_badge_embed_not_found(mock_get_dataset, client):
    mock_get_dataset.return_value = None
    response = client.get("/badge/999/embed")

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Dataset not found"


def test_make_segment_width_estimation():
    seg = make_segment("Test", "#123456", font_size=10, pad_x=5, min_w=40)
    assert seg["text"] == "Test"
    assert seg["bg"] == "#123456"
    assert seg["w"] >= 40


def test_estimate_text_width_basic():
    w = estimate_text_width("abc", font_size=10)
    assert w == int(0.6 * 10 * 3)


def test_estimate_text_width_zero_length():
    assert estimate_text_width("", font_size=12) == 0


def test_estimate_text_width_never_negative():
    assert estimate_text_width("", font_size=0) == 0
    assert estimate_text_width("", font_size=-10) == 0


def test_make_segment_respects_min_width():
    seg = make_segment("a", "#000", font_size=5, pad_x=2, min_w=100)
    assert seg["w"] == 100


def test_make_segment_calculates_expected_width():
    seg = make_segment("Hello", "#111", font_size=10, pad_x=5, min_w=10)
    expected = estimate_text_width("Hello", 10) + 10
    assert seg["w"] == expected


@patch("app.modules.badge.routes.get_dataset")
def test_badge_svg_download_no_url(mock_get_dataset, client):
    mock_get_dataset.return_value = {
        "title": "NoURL",
        "downloads": 0,
        "doi": "",
        "url": None,
    }

    response = client.get("/badge/2.svg")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "<a xlink:href" not in html
    assert "0 DL" in html


@patch("app.modules.badge.routes.get_dataset")
def test_badge_svg_download_long_title(mock_get_dataset, client):
    long_title = "A" * 200
    mock_get_dataset.return_value = {
        "title": long_title,
        "downloads": 10,
        "doi": "10.xxx/yyy",
        "url": "http://example.com",
    }

    response = client.get("/badge/3.svg")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert long_title in html


@patch("app.modules.badge.routes.get_dataset")
def test_badge_svg_empty_doi(mock_get_dataset, client):
    mock_get_dataset.return_value = {
        "title": "Test",
        "downloads": 5,
        "doi": "",
        "url": "http://example.com",
    }
    response = client.get("/badge/10/svg")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "5 DL" in html


@patch("app.modules.badge.routes.get_dataset")
def test_badge_svg_no_link(mock_get_dataset, client):
    mock_get_dataset.return_value = {
        "title": "Dataset",
        "downloads": 100,
        "doi": "10.x",
        "url": None,
    }
    response = client.get("/badge/11/svg")
    html = response.get_data(as_text=True)

    assert "<a xlink" not in html


@patch("app.modules.badge.routes.get_dataset")
@patch("app.modules.badge.routes.url_for")
def test_badge_embed_empty_doi(mock_url_for, mock_get_dataset, client):
    mock_get_dataset.return_value = {
        "title": "TestDS",
        "downloads": 12,
        "doi": "",
        "url": "http://example.com",
    }
    mock_url_for.return_value = "http://example.com/badge/1/svg"

    response = client.get("/badge/1/embed")
    assert response.status_code == 200
    data = response.get_json()
    assert "markdown" in data
    assert "html" in data
    assert "TestDS" in data["markdown"]


@patch("app.modules.badge.routes.get_dataset")
@patch("app.modules.badge.routes.url_for")
def test_badge_embed_no_dataset_url_uses_svg(mock_url_for, mock_get_dataset, client):
    mock_get_dataset.return_value = {
        "title": "Edge",
        "downloads": 0,
        "doi": "no",
        "url": None,
    }
    mock_url_for.return_value = "http://example.com/badge/2/svg"

    response = client.get("/badge/2/embed")
    data = response.get_json()

    assert data["markdown"].endswith("(http://example.com/badge/2/svg)")

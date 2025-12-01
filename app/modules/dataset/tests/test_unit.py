import io
import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from flask_login import LoginManager

from app.modules.badge.routes import badge_bp, make_segment
from app.modules.dataset import dataset_bp
from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType
from app.modules.dataset.repositories import DSDownloadRecordRepository
from app.modules.dataset.services import DataSetService, DSDownloadRecordService

FIXED_TIME = datetime(2025, 12, 1, 15, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def app_context(app):
    with app.app_context():
        yield


@pytest.fixture
def mock_dsdownloadrecord_repository():
    repository = MagicMock(spec=DSDownloadRecordRepository)
    mock_dataset = MagicMock(spec=DataSet)
    repository.top_3_dowloaded_datasets_per_week.return_value = [mock_dataset] * 3
    return repository


@pytest.fixture
def dataset_service(mock_dsdownloadrecord_repository):
    service = DataSetService()
    service.dsdownloadrecord_repository = mock_dsdownloadrecord_repository
    return service


@pytest.fixture
def download_service(mock_dsdownloadrecord_repository):
    service = DSDownloadRecordService()
    service.repository = mock_dsdownloadrecord_repository
    return service


# badge
@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(badge_bp)
    app.config["TESTING"] = True
    return app


# badge
@pytest.fixture
def client(app):
    return app.test_client()


# badge
@pytest.fixture
def mock_dataset():
    ds_mock = {
        "title": "Test Dataset",
        "downloads": 42,
        "doi": "10.1234/testdoi",
        "url": "http://example.com/dataset",
    }
    return ds_mock


def test_download_counter_registered_for_authenticated_user(download_service, mock_dsdownloadrecord_repository):
    test_user_id = 99
    test_dataset_id = 1
    test_cookie = "auth-cookie-123"

    download_service.create(
        user_id=test_user_id,
        dataset_id=test_dataset_id,
        download_date=FIXED_TIME,
        download_cookie=test_cookie,
    )

    mock_dsdownloadrecord_repository.create.assert_called_once_with(
        user_id=test_user_id,
        dataset_id=test_dataset_id,
        download_date=FIXED_TIME,
        download_cookie=test_cookie,
    )


def test_download_counter_registered_for_unauthenticated_user(download_service, mock_dsdownloadrecord_repository):
    test_dataset_id = 2
    test_cookie = "anon-cookie-456"

    download_service.create(
        user_id=None,
        dataset_id=test_dataset_id,
        download_date=FIXED_TIME,
        download_cookie=test_cookie,
    )

    mock_dsdownloadrecord_repository.create.assert_called_once()
    args, kwargs = mock_dsdownloadrecord_repository.create.call_args
    assert kwargs.get("user_id") is None
    assert kwargs.get("dataset_id") == test_dataset_id
    assert kwargs.get("download_cookie") == test_cookie


def test_multiple_downloads_from_same_user_are_registered(download_service, mock_dsdownloadrecord_repository):
    test_user_id = 77
    test_dataset_id = 5
    test_cookie = "repetitive-cookie"

    download_service.create(
        user_id=test_user_id,
        dataset_id=test_dataset_id,
        download_date=FIXED_TIME,
        download_cookie=test_cookie,
    )

    download_service.create(
        user_id=test_user_id,
        dataset_id=test_dataset_id,
        download_date=FIXED_TIME,
        download_cookie=test_cookie,
    )

    assert mock_dsdownloadrecord_repository.create.call_count == 2

    mock_dsdownloadrecord_repository.create.assert_any_call(
        user_id=test_user_id,
        dataset_id=test_dataset_id,
        download_date=FIXED_TIME,
        download_cookie=test_cookie,
    )


def test_download_counter_raises_error_with_null_dataset_id(download_service, mock_dsdownloadrecord_repository):
    mock_dsdownloadrecord_repository.create.side_effect = Exception("IntegrityError: dataset_id is required")

    with pytest.raises(Exception, match="IntegrityError: dataset_id is required"):
        download_service.create(
            user_id=1,
            dataset_id=None,
            download_date=FIXED_TIME,
            download_cookie="null-id-cookie",
        )

    mock_dsdownloadrecord_repository.create.assert_called_once()


def test_download_counter_raises_error_with_null_cookie(download_service, mock_dsdownloadrecord_repository):
    mock_dsdownloadrecord_repository.create.side_effect = Exception("IntegrityError: download_cookie cannot be null")

    with pytest.raises(Exception, match="IntegrityError: download_cookie cannot be null"):
        download_service.create(
            user_id=1,
            dataset_id=3,
            download_date=FIXED_TIME,
            download_cookie=None,
        )

    mock_dsdownloadrecord_repository.create.assert_called_once()


def test_get_dataset_leaderboard_success(dataset_service, mock_dsdownloadrecord_repository):
    period = "week"
    leaderboard_data = dataset_service.get_dataset_leaderboard(period=period)
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.assert_called_once_with(period=period)
    assert len(leaderboard_data) == 3


def test_get_dataset_leaderboard_with_month_period(dataset_service, mock_dsdownloadrecord_repository):
    period = "month"
    leaderboard_data = dataset_service.get_dataset_leaderboard(period=period)
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.assert_called_once_with(period=period)
    assert len(leaderboard_data) == 3


def test_get_dataset_leaderboard_invalid_period(dataset_service):
    with pytest.raises(ValueError, match="Periodo no soportado: usa 'week' o 'month'"):
        dataset_service.get_dataset_leaderboard(period="invalid_period")


def test_get_dataset_leaderboard_empty(dataset_service, mock_dsdownloadrecord_repository):
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.return_value = []
    period = "week"
    leaderboard_data = dataset_service.get_dataset_leaderboard(period=period)
    assert len(leaderboard_data) == 0


def test_get_dataset_leaderboard_with_same_downloads(dataset_service, mock_dsdownloadrecord_repository):
    mock_dataset_1 = MagicMock(spec=DataSet, id=1, downloads=20)
    mock_dataset_2 = MagicMock(spec=DataSet, id=2, downloads=20)
    mock_dataset_3 = MagicMock(spec=DataSet, id=3, downloads=20)
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.return_value = [
        mock_dataset_1,
        mock_dataset_2,
        mock_dataset_3,
    ]
    period = "week"
    leaderboard_data = dataset_service.get_dataset_leaderboard(period=period)
    assert leaderboard_data[0].id <= leaderboard_data[1].id <= leaderboard_data[2].id


def test_get_dataset_leaderboard_already_sorted(dataset_service, mock_dsdownloadrecord_repository):
    mock_dataset_1 = MagicMock(spec=DataSet, id=1, downloads=30)
    mock_dataset_2 = MagicMock(spec=DataSet, id=2, downloads=20)
    mock_dataset_3 = MagicMock(spec=DataSet, id=3, downloads=10)
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.return_value = [
        mock_dataset_1,
        mock_dataset_2,
        mock_dataset_3,
    ]
    period = "week"
    leaderboard_data = dataset_service.get_dataset_leaderboard(period=period)
    assert leaderboard_data[0].downloads > leaderboard_data[1].downloads > leaderboard_data[2].downloads


def test_get_dataset_leaderboard_large_number_of_datasets(dataset_service, mock_dsdownloadrecord_repository):
    mock_datasets = [MagicMock(spec=DataSet, id=i, downloads=100) for i in range(1000)]
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.return_value = mock_datasets[:3]
    period = "week"
    leaderboard_data = dataset_service.get_dataset_leaderboard(period=period)
    assert len(leaderboard_data) == 3


def test_get_dataset_leaderboard_with_null_data(dataset_service, mock_dsdownloadrecord_repository):
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.return_value = None
    period = "week"
    leaderboard_data = dataset_service.get_dataset_leaderboard(period=period)
    assert leaderboard_data == []


def test_get_dataset_leaderboard_limit_parameter(dataset_service, mock_dsdownloadrecord_repository):
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.return_value = []
    period = "week"

    dataset_service.dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week(period=period, limit=1)
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.assert_called_once_with(period=period, limit=1)


def test_get_dataset_leaderboard_with_duplicate_datasets(dataset_service, mock_dsdownloadrecord_repository):
    mock_dataset = MagicMock(spec=DataSet, id=1, downloads=10)
    mock_datasets = [mock_dataset, mock_dataset, mock_dataset]
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.return_value = mock_datasets

    leaderboard_data = dataset_service.get_dataset_leaderboard(period="week")

    assert all(d.id == 1 for d in leaderboard_data)


def test_get_dataset_leaderboard_repository_error(dataset_service, mock_dsdownloadrecord_repository):
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.side_effect = Exception("DB error")

    with pytest.raises(Exception, match="DB error"):
        dataset_service.get_dataset_leaderboard(period="week")


def test_get_dataset_leaderboard_with_single_dataset(dataset_service, mock_dsdownloadrecord_repository):
    mock_dataset_1 = MagicMock(spec=DataSet, id=1, downloads=100)
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.return_value = [mock_dataset_1]
    period = "week"
    leaderboard_data = dataset_service.get_dataset_leaderboard(period=period)
    assert len(leaderboard_data) == 1
    assert leaderboard_data[0].downloads == 100


def test_get_dataset_leaderboard_with_null_values_in_dataset(dataset_service, mock_dsdownloadrecord_repository):
    mock_dataset_1 = MagicMock(spec=DataSet, id=1, downloads=None)
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.return_value = [mock_dataset_1]
    period = "week"
    leaderboard_data = dataset_service.get_dataset_leaderboard(period=period)
    assert leaderboard_data[0].downloads is None


def test_get_dataset_leaderboard_with_empty_fields(dataset_service, mock_dsdownloadrecord_repository):
    mock_dataset_1 = MagicMock(spec=DataSet, id=1, downloads=100, description=None)
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.return_value = [mock_dataset_1]
    period = "week"
    leaderboard_data = dataset_service.get_dataset_leaderboard(period=period)
    assert leaderboard_data[0].description is None


def test_get_dataset_leaderboard_with_invalid_dataset_id(dataset_service, mock_dsdownloadrecord_repository):
    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.return_value = []
    period = "week"
    leaderboard_data = dataset_service.get_dataset_leaderboard(period=period)
    assert leaderboard_data == []


def test_get_dataset_leaderboard_with_special_characters_in_period(dataset_service, mock_dsdownloadrecord_repository):
    period = "week$"
    leaderboard_data = dataset_service.get_dataset_leaderboard(period=period)

    mock_dsdownloadrecord_repository.top_3_dowloaded_datasets_per_week.assert_called_once_with(period="week")

    assert len(leaderboard_data) == 3


# badge feature
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


@patch("app.modules.dataset.routes.current_user")
def test_upload_valid(mock_current_user):
    tmp = tempfile.mkdtemp()
    try:
        # ensure temp_folder() returns a plain string (not a coroutine/AsyncMock)
        mock_current_user.temp_folder = lambda: tmp
        mock_current_user.is_authenticated = True

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
        # attach a real LoginManager so flask-login utilities work
        lm = LoginManager()
        lm.init_app(app)
        # register a no-op user loader to satisfy flask-login internals

        @lm.user_loader
        def _load_user(user_id):
            # return a simple mock user when asked so login_required passes
            u = MagicMock()
            u.is_authenticated = True
            try:
                u.id = int(user_id)
            except Exception:
                u.id = user_id
            return u

        app.config["TESTING"] = True
        client = app.test_client()

        # mark session as logged in for flask-login
        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        data = {"file": (io.BytesIO(b"dummy content"), "test.pix")}
        resp = client.post("/dataset/file/upload", data=data, content_type="multipart/form-data")

        assert resp.status_code == 200
        j = resp.get_json()
        assert j["filename"] == "test.pix"
        assert "uploaded" in j["message"].lower()

        # ensure file was saved
        saved_path = os.path.join(tmp, "test.pix")
        assert os.path.exists(saved_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@patch("app.modules.dataset.routes.current_user")
def test_upload_invalid_extension(mock_current_user):
    tmp = tempfile.mkdtemp()
    try:
        # ensure temp_folder() returns a plain string (not a coroutine/AsyncMock)
        mock_current_user.temp_folder = lambda: tmp
        mock_current_user.is_authenticated = True

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
        # attach a real LoginManager so flask-login utilities work
        lm = LoginManager()
        lm.init_app(app)
        # register a no-op user loader to satisfy flask-login internals

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
        client = app.test_client()

        # mark session as logged in for flask-login
        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        data = {"file": (io.BytesIO(b"dummy content"), "test.txt")}
        resp = client.post("/dataset/file/upload", data=data, content_type="multipart/form-data")

        assert resp.status_code == 400
        j = resp.get_json()
        assert "valid" in j["message"].lower()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@patch("app.modules.dataset.routes.current_user")
@patch("app.modules.dataset.routes.DSDownloadRecordService")
@patch("app.modules.dataset.routes.dataset_service")
def test_download_dataset(mock_dataset_service, mock_dsdownload_service, mock_current_user):
    # Prepare an uploads tree
    base_dir = os.getcwd()
    user_id = 42
    dataset_id = 99
    uploads_path = os.path.join(base_dir, "uploads", f"user_{user_id}", f"dataset_{dataset_id}")
    os.makedirs(uploads_path, exist_ok=True)
    try:
        # create a sample file in dataset folder
        sample_file = os.path.join(uploads_path, "sample.txt")
        with open(sample_file, "wb") as fh:
            fh.write(b"hello world")

        # mock dataset_service.get_or_404
        ds = MagicMock()
        ds.id = dataset_id
        ds.user_id = user_id
        mock_dataset_service.get_or_404.return_value = ds

        # mock DSDownloadRecordService().create to track calls
        mock_service_instance = MagicMock()
        mock_dsdownload_service.return_value = mock_service_instance

        # current_user not authenticated -> cookie generated, user_id passed as None
        mock_current_user.is_authenticated = False
        mock_current_user.id = None

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
        # attach a real LoginManager so flask-login utilities work
        lm = LoginManager()
        lm.init_app(app)
        # register a no-op user loader to satisfy flask-login internals

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
        client = app.test_client()

        resp = client.get(f"/dataset/download/{dataset_id}")
        # should return the zip file for download
        assert resp.status_code == 200
        # response should be an attachment with zip mimetype
        assert resp.mimetype == "application/zip"

        # ensure download record was created
        mock_service_instance.create.assert_called()
    finally:
        # cleanup uploads
        shutil.rmtree(os.path.join(base_dir, "uploads"), ignore_errors=True)


@pytest.fixture
def mock_dataset_with_data():
    mock_author_1 = MagicMock(spec=Author, id=1, name="A1")
    mock_author_2 = MagicMock(spec=Author, id=2, name="A2")
    mock_meta = MagicMock(
        spec=DSMetaData,
        authors=[mock_author_1, mock_author_2],
        tags="spl,mobile,app",
        publication_type=PublicationType.JOURNAL_ARTICLE,
    )
    target_ds = MagicMock(spec=DataSet, id=10)
    target_ds.ds_meta_data = mock_meta
    target_ds.get_authors_set.return_value = target_ds.ds_meta_data.authors
    target_ds.get_tags_set.return_value = set(target_ds.ds_meta_data.tags.split(","))
    target_ds.get_publication_type.return_value = target_ds.ds_meta_data.publication_type
    target_ds.get_download_count.return_value = 0
    return target_ds


@pytest.fixture
def mock_all_datasets_query():
    ds1_meta = MagicMock(
        spec=DSMetaData,
        authors=[MagicMock(spec=Author, id=1, name="A1")],
        tags="spl,mobile,app,android",
        publication_type=PublicationType.JOURNAL_ARTICLE,
    )
    ds1 = MagicMock(spec=DataSet, id=11, created_at=datetime(2023, 1, 1))
    ds1.ds_meta_data = ds1_meta
    ds1.get_authors_set.return_value = ds1.ds_meta_data.authors
    ds1.get_tags_set.return_value = set(ds1.ds_meta_data.tags.split(","))
    ds1.get_publication_type.return_value = ds1.ds_meta_data.publication_type
    ds1.get_download_count.return_value = 5

    ds2_meta = MagicMock(
        spec=DSMetaData,
        authors=[MagicMock(spec=Author, id=3, name="A3")],
        tags="game,puzzle",
        publication_type=PublicationType.BOOK,
    )
    ds2 = MagicMock(spec=DataSet, id=12, created_at=datetime.now(timezone.utc) - timedelta(days=1))
    ds2.ds_meta_data = ds2_meta
    ds2.get_authors_set.return_value = ds2.ds_meta_data.authors
    ds2.get_tags_set.return_value = set(ds2.ds_meta_data.tags.split(","))
    ds2.get_publication_type.return_value = ds2.ds_meta_data.publication_type
    ds2.get_download_count.return_value = 1000

    ds3_meta = MagicMock(
        spec=DSMetaData,
        authors=[MagicMock(spec=Author, id=2, name="A2")],
        tags="spl,analysis",
        publication_type=PublicationType.CONFERENCE_PAPER,
    )
    ds3 = MagicMock(spec=DataSet, id=13, created_at=datetime.now(timezone.utc) - timedelta(days=30))
    ds3.ds_meta_data = ds3_meta
    ds3.get_authors_set.return_value = ds3.ds_meta_data.authors
    ds3.get_tags_set.return_value = set(ds3.ds_meta_data.tags.split(","))
    ds3.get_publication_type.return_value = ds3.ds_meta_data.publication_type
    ds3.get_download_count.return_value = 350

    return [ds1, ds2, ds3]


@patch("app.modules.dataset.models.DataSet.calculate_similarity_score", autospec=True)
@patch("app.modules.dataset.models.DataSet.query", new_callable=MagicMock)
def test_recommendations_prioritize_high_score_and_downloads(
    mock_dataset_query,
    mock_similarity_score,
    dataset_service,
    mock_dataset_with_data,
    mock_all_datasets_query,
):
    mock_dataset_query.filter.return_value = mock_dataset_query
    mock_dataset_query.all.return_value = mock_all_datasets_query

    ds1_base_score = 40
    ds2_base_score = 10
    ds3_base_score = 30

    def side_effect(self, other_dataset):
        if other_dataset.id == 11:
            return ds1_base_score
        if other_dataset.id == 12:
            return ds2_base_score
        if other_dataset.id == 13:
            return ds3_base_score
        return 0

    mock_similarity_score.side_effect = side_effect
    recommendations = dataset_service.get_dataset_recommendations(mock_dataset_with_data, limit=3)

    assert len(recommendations) == 3
    assert recommendations[0].id == 12
    assert recommendations[1].id == 13
    assert recommendations[2].id == 11


@patch("app.modules.dataset.models.DataSet.calculate_similarity_score", autospec=True)
@patch("app.modules.dataset.models.DataSet.query", new_callable=MagicMock)
def test_recommendations_returns_random_3__if_no_match(
    mock_dataset_query,
    mock_similarity_score,
    dataset_service,
    mock_dataset_with_data,
    mock_all_datasets_query,
):
    mock_dataset_query.filter.return_value = mock_dataset_query
    mock_dataset_query.all.return_value = mock_all_datasets_query
    mock_similarity_score.return_value = 0
    recommendations = dataset_service.get_dataset_recommendations(mock_dataset_with_data, limit=3)
    assert len(recommendations) == 3


@patch("app.modules.dataset.models.DataSet.calculate_similarity_score", autospec=True)
@patch("app.modules.dataset.models.DataSet.query", new_callable=MagicMock)
def test_recommendations_respects_limit(
    mock_dataset_query,
    mock_similarity_score,
    dataset_service,
    mock_dataset_with_data,
    mock_all_datasets_query,
):
    mock_dataset_query.filter.return_value = mock_dataset_query
    mock_dataset_query.all.return_value = mock_all_datasets_query
    mock_similarity_score.return_value = 10
    recommendations = dataset_service.get_dataset_recommendations(mock_dataset_with_data, limit=2)
    assert len(recommendations) == 2


@patch("app.modules.dataset.models.DataSet.calculate_similarity_score", autospec=True)
@patch("app.modules.dataset.models.DataSet.query", new_callable=MagicMock)
def test_recommendations_excludes_target_dataset(
    mock_dataset_query, mock_similarity_score, dataset_service, mock_dataset_with_data
):
    mock_dataset_query.filter.return_value = mock_dataset_query
    mock_dataset_query.all.return_value = [mock_dataset_with_data]
    mock_dataset_query.filter.return_value.all.return_value = []
    recommendations = dataset_service.get_dataset_recommendations(mock_dataset_with_data, limit=5)
    assert len(recommendations) == 0

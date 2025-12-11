import io
import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from zipfile import ZipFile

import pytest
from flask import Flask
from flask_login import LoginManager

from app.modules.badge.routes import badge_bp, make_segment
from app.modules.dataset import dataset_bp
from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType
from app.modules.dataset.repositories import DSDownloadRecordRepository
from app.modules.dataset.services import (
    DataSetComparisonService,
    DataSetService,
    DSDownloadRecordService,
    DSViewRecordService,
    SizeService,
)

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
        # Check backward compatibility
        assert j["filename"] == "test.pix"
        # Check new array format
        assert "filenames" in j
        assert len(j["filenames"]) == 1
        assert j["filenames"][0] == "test.pix"
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
        assert "only .pix or .zip files are allowed" in j["message"].lower()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@patch("app.modules.dataset.routes.current_user")
def test_upload_valid_zip_with_pix_files(mock_current_user):
    tmp = tempfile.mkdtemp()
    try:
        mock_current_user.temp_folder = lambda: tmp
        mock_current_user.is_authenticated = True

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
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
        client = app.test_client()

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        # Create a zip file with multiple .pix files
        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, "w") as zf:
            zf.writestr("file1.pix", b"pix content 1")
            zf.writestr("file2.pix", b"pix content 2")
            zf.writestr("nested/file3.pix", b"pix content 3")
        zip_buffer.seek(0)

        data = {"file": (zip_buffer, "test.zip")}
        resp = client.post("/dataset/file/upload", data=data, content_type="multipart/form-data")

        assert resp.status_code == 200
        j = resp.get_json()
        assert "uploaded" in j["message"].lower()
        # Check backward compatibility - filename should be first file
        assert j["filename"] == "file1.pix"
        # Check new array format
        assert "filenames" in j
        assert len(j["filenames"]) == 3
        assert "file1.pix" in j["filenames"]
        assert "file2.pix" in j["filenames"]
        assert "file3.pix" in j["filenames"]

        # Verify files were extracted
        for filename in j["filenames"]:
            assert os.path.exists(os.path.join(tmp, filename))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@patch("app.modules.dataset.routes.current_user")
def test_upload_zip_without_pix_files(mock_current_user):
    tmp = tempfile.mkdtemp()
    try:
        mock_current_user.temp_folder = lambda: tmp
        mock_current_user.is_authenticated = True

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
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
        client = app.test_client()

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        # Create a zip file without .pix files
        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, "w") as zf:
            zf.writestr("file1.txt", b"text content")
            zf.writestr("file2.doc", b"doc content")
        zip_buffer.seek(0)

        data = {"file": (zip_buffer, "test.zip")}
        resp = client.post("/dataset/file/upload", data=data, content_type="multipart/form-data")

        assert resp.status_code == 400
        j = resp.get_json()
        assert "does not contain any .pix files" in j["message"].lower()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@patch("app.modules.dataset.routes.current_user")
def test_upload_zip_with_filename_collision(mock_current_user):
    tmp = tempfile.mkdtemp()
    try:
        mock_current_user.temp_folder = lambda: tmp
        mock_current_user.is_authenticated = True

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
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
        client = app.test_client()

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        # Pre-create a file to cause collision
        existing_file = os.path.join(tmp, "duplicate.pix")
        with open(existing_file, "w") as f:
            f.write("existing content")

        # Create zip with duplicate filename
        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, "w") as zf:
            zf.writestr("duplicate.pix", b"new content")
        zip_buffer.seek(0)

        data = {"file": (zip_buffer, "test.zip")}
        resp = client.post("/dataset/file/upload", data=data, content_type="multipart/form-data")

        assert resp.status_code == 200
        j = resp.get_json()
        assert len(j["filenames"]) == 1
        # Should generate unique filename like "duplicate (1).pix"
        assert "duplicate" in j["filenames"][0]
        assert j["filenames"][0] != "duplicate.pix"
        assert os.path.exists(os.path.join(tmp, j["filenames"][0]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@patch("app.modules.dataset.routes.current_user")
def test_upload_zip_with_case_insensitive_extension(mock_current_user):
    tmp = tempfile.mkdtemp()
    try:
        mock_current_user.temp_folder = lambda: tmp
        mock_current_user.is_authenticated = True

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
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
        client = app.test_client()

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        # Create zip with mixed-case .PIX extension
        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, "w") as zf:
            zf.writestr("FILE1.PIX", b"pix content 1")
            zf.writestr("file2.Pix", b"pix content 2")
        zip_buffer.seek(0)

        data = {"file": (zip_buffer, "TEST.ZIP")}
        resp = client.post("/dataset/file/upload", data=data, content_type="multipart/form-data")

        assert resp.status_code == 200
        j = resp.get_json()
        assert len(j["filenames"]) == 2
        assert "FILE1.PIX" in j["filenames"]
        assert "file2.Pix" in j["filenames"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@patch("app.modules.dataset.routes.current_user")
@patch("app.modules.dataset.routes.DSDownloadRecordService")
@patch("app.modules.dataset.routes.dataset_service")
@patch("app.modules.dataset.routes.tempfile.mkdtemp")
@patch("app.modules.dataset.routes.ZipFile")
@patch("app.modules.dataset.routes.send_from_directory")
def test_download_dataset(
    mock_send, mock_zipfile, mock_mkdtemp, mock_dataset_service, mock_dsdownload_service, mock_current_user
):
    # Mock dataset service
    ds = MagicMock()
    ds.id = 99
    ds.user_id = 42
    mock_dataset_service.get_or_404.return_value = ds

    # Mock download service
    mock_service_instance = MagicMock()
    mock_dsdownload_service.return_value = mock_service_instance

    # Mock temp directory
    mock_mkdtemp.return_value = "/tmp/test"

    # Mock ZipFile to avoid actual file operations
    mock_zip_instance = MagicMock()
    mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

    # Mock send_from_directory to return a real Response
    from flask import Response

    mock_response = Response("zip content", mimetype="application/zip")
    mock_send.return_value = mock_response

    # current_user not authenticated
    mock_current_user.is_authenticated = False
    mock_current_user.id = None

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(dataset_bp)
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
    client = app.test_client()

    with patch("app.modules.dataset.routes.os.walk") as mock_walk:
        mock_walk.return_value = [("/fake/path", [], ["sample.txt"])]

        resp = client.get("/dataset/download/99")

        assert resp.status_code == 200
        assert resp.mimetype == "application/zip"
        mock_service_instance.create.assert_called()


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


# Test upload_github endpoint
@patch("app.modules.dataset.routes.current_user")
@patch("app.modules.dataset.routes.requests.Session")
def test_upload_github_success(mock_session_class, mock_current_user):
    tmp = tempfile.mkdtemp()
    try:
        mock_current_user.temp_folder = lambda: tmp
        mock_current_user.is_authenticated = True

        # Mock session.get for API calls
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock GitHub API response for contents
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"type": "file", "name": "test.pix", "download_url": "https://raw.example.com/test.pix"}
        ]
        mock_session.get.return_value = mock_response
        # Second call for file download
        mock_file_response = MagicMock()
        mock_file_response.status_code = 200
        mock_file_response.content = b"pix content"
        mock_session.get.side_effect = [mock_response, mock_file_response]

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
        lm = LoginManager()
        lm.init_app(app)

        @lm.user_loader
        def _load_user(user_id):
            u = MagicMock()
            u.is_authenticated = True
            u.id = int(user_id) if user_id else None
            return u

        app.config["TESTING"] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        data = {"repo_url": "https://github.com/owner/repo", "path": ""}
        resp = client.post("/dataset/file/upload_github", json=data)

        assert resp.status_code == 200
        j = resp.get_json()
        assert "uploaded" in j["message"].lower()
        assert j["filename"] == "test.pix"
        assert "test.pix" in j["filenames"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@patch("app.modules.dataset.routes.current_user")
def test_upload_github_no_repo_url(mock_current_user):
    tmp = tempfile.mkdtemp()
    try:
        mock_current_user.temp_folder = lambda: tmp
        mock_current_user.is_authenticated = True

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
        lm = LoginManager()
        lm.init_app(app)

        @lm.user_loader
        def _load_user(user_id):
            return MagicMock(is_authenticated=True, id=int(user_id) if user_id else None)

        app.config["TESTING"] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        data = {"path": "some/path"}
        resp = client.post("/dataset/file/upload_github", json=data)

        assert resp.status_code == 400
        j = resp.get_json()
        assert "repo_url is required" in j["message"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@patch("app.modules.dataset.routes.current_user")
def test_upload_github_invalid_url(mock_current_user):
    tmp = tempfile.mkdtemp()
    try:
        mock_current_user.temp_folder = lambda: tmp
        mock_current_user.is_authenticated = True

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
        lm = LoginManager()
        lm.init_app(app)

        @lm.user_loader
        def _load_user(user_id):
            return MagicMock(is_authenticated=True, id=int(user_id) if user_id else None)

        app.config["TESTING"] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        data = {"repo_url": "https://invalid-url.com/not-github"}
        resp = client.post("/dataset/file/upload_github", json=data)

        assert resp.status_code == 400
        j = resp.get_json()
        assert "Could not parse" in j["message"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@patch("app.modules.dataset.routes.current_user")
@patch("app.modules.dataset.routes.requests.Session")
def test_upload_github_no_pix_files(mock_session_class, mock_current_user):
    tmp = tempfile.mkdtemp()
    try:
        mock_current_user.temp_folder = lambda: tmp
        mock_current_user.is_authenticated = True

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"type": "file", "name": "test.txt", "download_url": "https://raw.example.com/test.txt"}
        ]
        mock_session.get.return_value = mock_response

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
        lm = LoginManager()
        lm.init_app(app)

        @lm.user_loader
        def _load_user(user_id):
            return MagicMock(is_authenticated=True, id=int(user_id) if user_id else None)

        app.config["TESTING"] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        data = {"repo_url": "https://github.com/owner/repo"}
        resp = client.post("/dataset/file/upload_github", json=data)

        assert resp.status_code == 400
        j = resp.get_json()
        assert "No .pix files found" in j["message"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# Test delete endpoint
@patch("app.modules.dataset.routes.current_user")
def test_delete_file_success(mock_current_user):
    tmp = tempfile.mkdtemp()
    try:
        mock_current_user.temp_folder = lambda: tmp
        mock_current_user.is_authenticated = True

        # Create a file to delete
        test_file = os.path.join(tmp, "test_delete.pix")
        with open(test_file, "w") as f:
            f.write("test content")

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
        lm = LoginManager()
        lm.init_app(app)

        @lm.user_loader
        def _load_user(user_id):
            return MagicMock(is_authenticated=True, id=int(user_id) if user_id else None)

        app.config["TESTING"] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        data = {"file": "test_delete.pix"}
        resp = client.post("/dataset/file/delete", json=data)

        assert resp.status_code == 200
        j = resp.get_json()
        assert "deleted" in j["message"].lower()
        assert not os.path.exists(test_file)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@patch("app.modules.dataset.routes.current_user")
def test_delete_file_not_found(mock_current_user):
    tmp = tempfile.mkdtemp()
    try:
        mock_current_user.temp_folder = lambda: tmp
        mock_current_user.is_authenticated = True

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
        lm = LoginManager()
        lm.init_app(app)

        @lm.user_loader
        def _load_user(user_id):
            return MagicMock(is_authenticated=True, id=int(user_id) if user_id else None)

        app.config["TESTING"] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        data = {"file": "nonexistent.pix"}
        resp = client.post("/dataset/file/delete", json=data)

        assert resp.status_code == 200
        j = resp.get_json()
        assert "error" in j
        assert "not found" in j["error"].lower()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# Test list_dataset endpoint
@patch("app.modules.dataset.routes.current_user")
@patch("app.modules.dataset.routes.dataset_service")
@patch("app.modules.dataset.routes.render_template")
def test_list_dataset(mock_render_template, mock_dataset_service, mock_current_user):
    mock_current_user.id = 1
    mock_current_user.is_authenticated = True

    mock_dataset_service.get_synchronized.return_value = [MagicMock(id=1)]
    mock_dataset_service.get_unsynchronized.return_value = [MagicMock(id=2)]
    mock_render_template.return_value = "<html>list</html>"

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(dataset_bp)
    lm = LoginManager()
    lm.init_app(app)

    @lm.user_loader
    def _load_user(user_id):
        return MagicMock(is_authenticated=True, id=int(user_id) if user_id else None)

    app.config["TESTING"] = True
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["_user_id"] = "1"

    resp = client.get("/dataset/list")

    assert resp.status_code == 200
    mock_dataset_service.get_synchronized.assert_called_once_with(1)
    mock_dataset_service.get_unsynchronized.assert_called_once_with(1)


# Test home_leaderboard endpoint
@patch("app.modules.dataset.routes.dataset_service")
@patch("app.modules.dataset.routes.render_template")
def test_home_leaderboard_default_period(mock_render_template, mock_dataset_service):
    mock_dataset_service.get_dataset_leaderboard.return_value = [MagicMock(id=1, downloads=100)]
    mock_render_template.return_value = "<html>leaderboard</html>"

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(dataset_bp)
    app.config["TESTING"] = True
    client = app.test_client()

    resp = client.get("/home/leaderboard")

    assert resp.status_code == 200
    mock_dataset_service.get_dataset_leaderboard.assert_called_once_with(period="week")


@patch("app.modules.dataset.routes.dataset_service")
@patch("app.modules.dataset.routes.render_template")
def test_home_leaderboard_custom_period(mock_render_template, mock_dataset_service):
    mock_dataset_service.get_dataset_leaderboard.return_value = [MagicMock(id=1, downloads=100)]
    mock_render_template.return_value = "<html>leaderboard</html>"

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(dataset_bp)
    app.config["TESTING"] = True
    client = app.test_client()

    resp = client.get("/home/leaderboard?period=month")

    assert resp.status_code == 200
    mock_dataset_service.get_dataset_leaderboard.assert_called_once_with(period="month")


# Test subdomain_index (DOI view)
@patch("app.modules.dataset.routes.doi_mapping_service")
@patch("app.modules.dataset.routes.dataset_service")
@patch("app.modules.dataset.routes.dsmetadata_service")
@patch("app.modules.dataset.routes.ds_view_record_service")
@patch("app.modules.dataset.routes.render_template")
def test_subdomain_index_success(
    mock_render_template, mock_view_service, mock_dsmetadata_service, mock_dataset_service, mock_doi_mapping_service
):
    mock_doi_mapping_service.get_new_doi.return_value = None
    mock_ds_meta = MagicMock()
    mock_dataset = MagicMock(id=1)
    mock_ds_meta.data_set = mock_dataset
    mock_dsmetadata_service.filter_by_doi.return_value = mock_ds_meta
    mock_view_service.create_cookie.return_value = "test-cookie"
    mock_dataset_service.get_dataset_recommendations.return_value = []
    mock_dataset_service.get_dataset_history.return_value = []
    mock_render_template.return_value = "<html>dataset view</html>"

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(dataset_bp)
    app.config["TESTING"] = True
    client = app.test_client()

    resp = client.get("/doi/10.1234/test/")

    assert resp.status_code == 200
    mock_dsmetadata_service.filter_by_doi.assert_called_once_with("10.1234/test")


@patch("app.modules.dataset.routes.doi_mapping_service")
@patch("app.modules.dataset.routes.dsmetadata_service")
def test_subdomain_index_not_found(mock_dsmetadata_service, mock_doi_mapping_service):
    mock_doi_mapping_service.get_new_doi.return_value = None
    mock_dsmetadata_service.filter_by_doi.return_value = None

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(dataset_bp)
    app.config["TESTING"] = True
    client = app.test_client()

    resp = client.get("/doi/10.1234/nonexistent/")

    assert resp.status_code == 404


# Test get_unsynchronized_dataset
@patch("app.modules.dataset.routes.current_user")
@patch("app.modules.dataset.routes.dataset_service")
@patch("app.modules.dataset.routes.render_template")
def test_get_unsynchronized_dataset_success(mock_render_template, mock_dataset_service, mock_current_user):
    mock_current_user.id = 1
    mock_current_user.is_authenticated = True

    mock_dataset = MagicMock(id=5)
    mock_dataset_service.get_unsynchronized_dataset.return_value = mock_dataset
    mock_dataset_service.get_dataset_history.return_value = []
    mock_render_template.return_value = "<html>dataset view</html>"

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(dataset_bp)
    lm = LoginManager()
    lm.init_app(app)

    @lm.user_loader
    def _load_user(user_id):
        return MagicMock(is_authenticated=True, id=int(user_id) if user_id else None)

    app.config["TESTING"] = True
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["_user_id"] = "1"

    resp = client.get("/dataset/unsynchronized/5/")

    assert resp.status_code == 200
    mock_dataset_service.get_unsynchronized_dataset.assert_called_once_with(1, 5)


@patch("app.modules.dataset.routes.current_user")
@patch("app.modules.dataset.routes.dataset_service")
def test_get_unsynchronized_dataset_not_found(mock_dataset_service, mock_current_user):
    mock_current_user.id = 1
    mock_current_user.is_authenticated = True

    mock_dataset_service.get_unsynchronized_dataset.return_value = None

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(dataset_bp)
    lm = LoginManager()
    lm.init_app(app)

    @lm.user_loader
    def _load_user(user_id):
        return MagicMock(is_authenticated=True, id=int(user_id) if user_id else None)

    app.config["TESTING"] = True
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["_user_id"] = "1"

    resp = client.get("/dataset/unsynchronized/999/")

    assert resp.status_code == 404


# Test compare_datasets
@patch("app.modules.dataset.routes.current_user")
@patch("app.modules.dataset.routes.dataset_service")
@patch("app.modules.dataset.routes.DataSetComparisonService")
@patch("app.modules.dataset.routes.render_template")
def test_compare_datasets(mock_render_template, mock_comparison_service_class, mock_dataset_service, mock_current_user):
    mock_current_user.is_authenticated = True

    mock_old_ds = MagicMock(id=1)
    mock_new_ds = MagicMock(id=2)
    mock_dataset_service.get_or_404.side_effect = [mock_old_ds, mock_new_ds]

    mock_comparison_service = MagicMock()
    mock_comparison_service.compare.return_value = {"metadata": {}, "files": {}}
    mock_comparison_service_class.return_value = mock_comparison_service
    mock_render_template.return_value = "<html>compare</html>"

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(dataset_bp)
    lm = LoginManager()
    lm.init_app(app)

    @lm.user_loader
    def _load_user(user_id):
        return MagicMock(is_authenticated=True, id=int(user_id) if user_id else None)

    app.config["TESTING"] = True
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["_user_id"] = "1"

    resp = client.get("/dataset/compare/1/2")

    assert resp.status_code == 200
    mock_comparison_service.compare.assert_called_once_with(mock_old_ds, mock_new_ds)


# Test file_diff
@patch("app.modules.dataset.routes.DataSetComparisonService")
def test_file_diff(mock_comparison_service_class):
    mock_comparison_service = MagicMock()
    mock_comparison_service.generate_diff_html.return_value = "<div>diff</div>"
    mock_comparison_service_class.return_value = mock_comparison_service

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(dataset_bp)
    app.config["TESTING"] = True
    client = app.test_client()

    resp = client.get("/file/diff/1/2")

    assert resp.status_code == 200
    j = resp.get_json()
    assert "diff_html" in j
    assert j["diff_html"] == "<div>diff</div>"
    mock_comparison_service.generate_diff_html.assert_called_once_with(1, 2)


# Test create_dataset endpoint
@patch("app.modules.dataset.routes.DataSetForm")
@patch("app.modules.dataset.routes.render_template")
@patch("app.modules.dataset.routes.current_user")
def test_create_dataset_get(mock_current_user, mock_render_template, mock_form_class):
    mock_current_user.is_authenticated = True
    mock_form = MagicMock()
    mock_form_class.return_value = mock_form
    mock_render_template.return_value = "<html>upload</html>"

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(dataset_bp)
    lm = LoginManager()
    lm.init_app(app)

    @lm.user_loader
    def _load_user(user_id):
        return MagicMock(is_authenticated=True, id=int(user_id) if user_id else None)

    app.config["TESTING"] = True
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["_user_id"] = "1"

    resp = client.get("/dataset/upload")

    assert resp.status_code == 200
    mock_render_template.assert_called_once()


@patch("app.modules.dataset.routes.DataSetForm")
@patch("app.modules.dataset.routes.current_user")
def test_create_dataset_post_invalid_form(mock_current_user, mock_form_class):
    mock_current_user.is_authenticated = True
    mock_form = MagicMock()
    mock_form.validate_on_submit.return_value = False
    mock_form.errors = {"field": ["error"]}
    mock_form_class.return_value = mock_form

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(dataset_bp)
    lm = LoginManager()
    lm.init_app(app)

    @lm.user_loader
    def _load_user(user_id):
        return MagicMock(is_authenticated=True, id=int(user_id) if user_id else None)

    app.config["TESTING"] = True
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["_user_id"] = "1"

    resp = client.post("/dataset/upload", data={})
    assert resp.status_code == 400
    j = resp.get_json()
    assert "field" in j["message"]
    assert j["message"]["field"] == ["error"]


@patch("app.modules.dataset.routes.current_user")
def test_upload_no_file(mock_current_user):
    mock_current_user.is_authenticated = True
    mock_current_user.temp_folder.return_value = "/tmp/test_folder"

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(dataset_bp)
    lm = LoginManager()
    lm.init_app(app)

    @lm.user_loader
    def _load_user(user_id):
        return MagicMock(is_authenticated=True, id=int(user_id) if user_id else None)

    app.config["TESTING"] = True
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["_user_id"] = "1"

    resp = client.post("/dataset/file/upload", data={})
    assert resp.status_code == 400
    j = resp.get_json()
    assert "No file provided" in j["message"]


@patch("app.modules.dataset.routes.current_user")
@patch("app.modules.dataset.routes.requests.Session")
def test_upload_github_exception(mock_session_cls, mock_current_user):
    tmp = tempfile.mkdtemp()
    try:
        mock_current_user.is_authenticated = True
        mock_current_user.temp_folder = lambda: tmp

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.get.side_effect = Exception("GitHub API Error")

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(dataset_bp)
        lm = LoginManager()
        lm.init_app(app)

        @lm.user_loader
        def _load_user(user_id):
            return MagicMock(is_authenticated=True, id=int(user_id) if user_id else None)

        app.config["TESTING"] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        data = {"repo_url": "https://github.com/user/repo"}
        resp = client.post("/dataset/file/upload_github", json=data)

        assert resp.status_code == 400
        j = resp.get_json()
        assert "GitHub API Error" in j["message"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_size_service():
    service = SizeService()
    assert service.get_human_readable_size(500) == "500 bytes"
    assert service.get_human_readable_size(1024) == "1.0 KB"
    assert service.get_human_readable_size(1024 * 1024) == "1.0 MB"
    assert service.get_human_readable_size(1024 * 1024 * 1024) == "1.0 GB"
    assert service.get_human_readable_size(1500) == "1.46 KB"


def test_get_dataset_history(dataset_service):
    # Create a chain of datasets: 1 -> 2 -> 3
    ds1 = MagicMock(id=1, version=1, previous_version_id=None, next_versions=[])
    ds2 = MagicMock(id=2, version=2, previous_version_id=1, next_versions=[])
    ds3 = MagicMock(id=3, version=3, previous_version_id=2, next_versions=[])

    ds1.next_versions = [ds2]
    ds2.next_versions = [ds3]

    # Mock repository get_by_id
    dataset_service.repository = MagicMock()

    def get_by_id_side_effect(id):
        if id == 1:
            return ds1
        if id == 2:
            return ds2
        if id == 3:
            return ds3
        return None

    dataset_service.repository.get_by_id.side_effect = get_by_id_side_effect

    # Test getting history from middle
    history = dataset_service.get_dataset_history(2)
    assert len(history) == 3
    assert history[0].id == 1
    assert history[1].id == 2
    assert history[2].id == 3


def test_get_pixelhub_doi(dataset_service):
    dataset = MagicMock()
    dataset.ds_meta_data.dataset_doi = "10.1234/test"

    with patch.dict(os.environ, {"FLASK_ENV": "production", "DOMAIN": "pixelhub.com"}):
        doi_url = dataset_service.get_pixelhub_doi(dataset)
        assert doi_url == "https://pixelhub.com/doi/10.1234/test"

    with patch.dict(os.environ, {"FLASK_ENV": "development", "DOMAIN": "localhost:5000"}):
        doi_url = dataset_service.get_pixelhub_doi(dataset)
        assert doi_url == "http://localhost:5000/doi/10.1234/test"


@patch("app.modules.dataset.services.AuthenticationService")
def test_move_file_models(mock_auth_service, dataset_service):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.temp_folder.return_value = "/tmp/source"
    mock_auth_service.return_value.get_authenticated_user.return_value = mock_user

    dataset = MagicMock(id=10)
    file_model = MagicMock()
    file_model.fm_meta_data.filename = "test.txt"
    dataset.file_models = [file_model]

    with (
        patch("app.modules.dataset.services.shutil.move") as mock_move,
        patch("app.modules.dataset.services.os.makedirs") as mock_makedirs,
        patch("app.modules.dataset.services.os.path.join") as mock_join,
    ):

        mock_join.side_effect = lambda *args: "/".join(args)

        dataset_service.move_file_models(dataset)

        mock_makedirs.assert_called()
        mock_move.assert_called()


def test_ds_view_record_service_create_cookie(app):
    service = DSViewRecordService()
    service.repository = MagicMock()
    service.repository.the_record_exists.return_value = False

    dataset = MagicMock()

    with app.test_request_context():
        # Case 1: No cookie in request
        cookie = service.create_cookie(dataset)
        assert cookie is not None
        service.repository.create_new_record.assert_called()

    with app.test_request_context(headers={"Cookie": "view_cookie=existing-cookie"}):
        # Case 2: Cookie exists
        service.repository.the_record_exists.return_value = True
        cookie = service.create_cookie(dataset)
        assert cookie == "existing-cookie"


def test_dataset_comparison_service_compare():
    service = DataSetComparisonService()

    # Mock Old Dataset
    old_ds = MagicMock()
    old_ds.ds_meta_data.title = "Old Title"
    old_ds.ds_meta_data.description = "Old Description"
    old_ds.ds_meta_data.publication_type.name = "Journal Article"
    old_ds.ds_meta_data.publication_doi = "10.1000/old"
    old_ds.ds_meta_data.tags = "tag1,tag2"

    author1 = MagicMock()
    author1.name = "Author 1"
    old_ds.ds_meta_data.authors = [author1]

    file1 = MagicMock()
    file1.name = "file1.txt"
    file1.checksum = "123"

    file2 = MagicMock()
    file2.name = "file2.txt"
    file2.checksum = "abc"

    old_ds.files.return_value = [file1, file2]

    # Mock New Dataset
    new_ds = MagicMock()
    new_ds.ds_meta_data.title = "New Title"
    new_ds.ds_meta_data.description = "Old Description"  # Unchanged
    new_ds.ds_meta_data.publication_type.name = "Conference Paper"
    new_ds.ds_meta_data.publication_doi = "10.1000/new"
    new_ds.ds_meta_data.tags = "tag1,tag3"

    author2 = MagicMock()
    author2.name = "Author 2"
    new_ds.ds_meta_data.authors = [author2]

    file1_mod = MagicMock()
    file1_mod.name = "file1.txt"
    file1_mod.checksum = "456"  # Modified

    file3 = MagicMock()
    file3.name = "file3.txt"
    file3.checksum = "xyz"  # Added

    # file2 is deleted

    new_ds.files.return_value = [file1_mod, file3]

    comparison = service.compare(old_ds, new_ds)

    # Check Metadata Changes
    metadata_changes = comparison["metadata"]
    assert any(c["field"] == "Title" and c["old"] == "Old Title" and c["new"] == "New Title" for c in metadata_changes)
    assert any(
        c["field"] == "Publication Type" and c["old"] == "Journal Article" and c["new"] == "Conference Paper"
        for c in metadata_changes
    )
    assert any(
        c["field"] == "Publication DOI" and c["old"] == "10.1000/old" and c["new"] == "10.1000/new"
        for c in metadata_changes
    )
    assert any(c["field"] == "Tags" and c["old"] == "tag1,tag2" and c["new"] == "tag1,tag3" for c in metadata_changes)
    assert any(c["field"] == "Authors" and "Author 1" in c["old"] and "Author 2" in c["new"] for c in metadata_changes)

    # Check File Changes
    file_changes = comparison["files"]
    assert len(file_changes["added"]) == 1
    assert file_changes["added"][0].name == "file3.txt"

    assert len(file_changes["deleted"]) == 1
    assert file_changes["deleted"][0].name == "file2.txt"

    assert len(file_changes["modified"]) == 1
    assert file_changes["modified"][0]["old"].checksum == "123"
    assert file_changes["modified"][0]["new"].checksum == "456"


def test_dataset_service_counts(dataset_service):
    dataset_service.repository = MagicMock()
    dataset_service.file_model_repository = MagicMock()
    dataset_service.author_repository = MagicMock()
    dataset_service.dsmetadata_repository = MagicMock()
    dataset_service.dsdownloadrecord_repository = MagicMock()
    dataset_service.dsviewrecord_repostory = MagicMock()

    dataset_service.repository.count_synchronized_datasets.return_value = 10
    dataset_service.file_model_repository.count_file_models.return_value = 20
    dataset_service.author_repository.count.return_value = 30
    dataset_service.dsmetadata_repository.count.return_value = 40
    dataset_service.dsdownloadrecord_repository.total_dataset_downloads.return_value = 50
    dataset_service.dsviewrecord_repostory.total_dataset_views.return_value = 60

    assert dataset_service.count_synchronized_datasets() == 10
    assert dataset_service.count_file_models() == 20
    assert dataset_service.count_authors() == 30
    assert dataset_service.count_dsmetadata() == 40
    assert dataset_service.total_dataset_downloads() == 50
    assert dataset_service.total_dataset_views() == 60

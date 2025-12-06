import random

from locust import HttpUser, TaskSet, between, task

from app import create_app, db
from app.modules.dataset.models import DSMetaData
from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token


class DatasetBehavior(TaskSet):
    def on_start(self):
        response = self.client.get("/dataset/upload")
        get_csrf_token(response)

    @task
    def dataset(self):
        response = self.client.get("/dataset/upload")
        get_csrf_token(response)


class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
    wait_time = between(1, 3)

    _cached_dois = []
    _cache_initialized = False

    def on_start(self):
        if not DatasetUser._cache_initialized:
            DatasetUser._cache_initialized = True
            self._initialize_doi_cache()

    def _initialize_doi_cache(self):
        try:
            app = create_app()
            with app.app_context():
                datasets_with_doi = (
                    db.session.query(DSMetaData.dataset_doi)
                    .filter(DSMetaData.dataset_doi.isnot(None))
                    .filter(DSMetaData.dataset_doi != "")
                    .limit(20)
                    .all()
                )
                DatasetUser._cached_dois = [doi[0] for doi in datasets_with_doi if doi[0]]
        except Exception:
            DatasetUser._cached_dois = []

    @task(2)
    def list_datasets(self):
        self.client.get("/dataset/list")

    @task(3)
    def view_dataset(self):
        dataset_id = random.randint(1, 4)
        self.client.get(f"/dataset/unsynchronized/{dataset_id}/")

    @task(2)
    def download_dataset(self):
        dataset_id = random.randint(1, 4)
        self.client.get(f"/dataset/download/{dataset_id}")

    @task(1)
    def compare_datasets(self):
        old_id = random.randint(1, 4)
        new_id = random.randint(1, 4)
        if old_id != new_id:
            self.client.get(f"/dataset/compare/{old_id}/{new_id}")

    @task(1)
    def view_by_doi(self):
        if DatasetUser._cached_dois:
            doi = random.choice(DatasetUser._cached_dois)
            self.client.get(f"/doi/{doi}/")

    @task(1)
    def upload_file(self):
        files = {"file": ("test.pix", b"contenido de prueba")}
        self.client.post("/dataset/file/upload", files=files)

    @task(1)
    def create_dataset(self):
        payload = {
            "title": "Dataset de prueba",
            "desc": "Descripción de prueba",
            "publication_type": "Article",
            "tags": ["test", "locust"],
            "authors": [{"name": "John Doe", "affiliation": "Test"}],
            "file_models": [{"filename": "test.pix"}],
        }
        self.client.post("/dataset/upload", data=payload)

    @task(1)
    def create_version_page(self):
        dataset_id = random.randint(1, 4)
        self.client.get(f"/dataset/{dataset_id}/create_version")

    @task(1)
    def create_version_post(self):
        dataset_id = random.randint(1, 4)
        payload = {
            "title": f"Version dataset {dataset_id}",
            "desc": "Descripción versión",
            "publication_type": "Article",
            "tags": ["version", "test"],
            "authors": [{"name": "John Doe", "affiliation": "Test"}],
            "file_models": [{"filename": "test.pix"}],
        }
        self.client.post(f"/dataset/{dataset_id}/create_version", data=payload)

    @task(1)
    def view_leaderboard(self):
        period = random.choice(["week", "month"])
        self.client.get(f"/home/leaderboard?period={period}")

    @task(1)
    def view_file_diff(self):
        old_file_id = random.randint(1, 4)
        new_file_id = random.randint(1, 4)
        if old_file_id != new_file_id:
            self.client.get(f"/file/diff/{old_file_id}/{new_file_id}")

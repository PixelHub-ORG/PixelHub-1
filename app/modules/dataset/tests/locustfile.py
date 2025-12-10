import logging
import random

from bs4 import BeautifulSoup
from locust import HttpUser, TaskSet, between, task

from app import create_app, db
from app.modules.dataset.models import DSMetaData
from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token

DATASET_V1_ID = 9991
DATASET_V2_ID = 9992

# Credenciales del Seeder
USER_EMAIL = "user1@example.com"
USER_PASSWORD = "password"


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    host = "http://localhost:5000"

    def on_start(self):
        """
        Se ejecuta una vez por usuario simulado al arrancar.
        Aquí hacemos el login obligatorio.
        """
        logging.info("--- Iniciando Usuario: Intentando Login ---")
        self.login()

    def login(self):
        response = self.client.get("/login")
        csrf_token = self.get_csrf_token(response.text)

        if not csrf_token:
            logging.error("!!! Error: No se pudo obtener CSRF Token del login !!!")
            return

        response = self.client.post(
            "/login",
            data={
                "email": USER_EMAIL,
                "password": USER_PASSWORD,
                "csrf_token": csrf_token,
            },
        )

        if response.status_code == 200 and "login" not in response.url:
            logging.info(f"Login Exitoso: {USER_EMAIL}")
        else:
            if "/login" in response.url:
                logging.error(
                    "!!! Login Fallido: Credenciales incorrectas o error de servidor !!!"
                )
            else:
                logging.info("Login parece exitoso (Redirección correcta)")

    def get_csrf_token(self, html_content):
        """Helper para extraer el token oculto del formulario Flask-WTF"""
        soup = BeautifulSoup(html_content, "html.parser")
        token = soup.find("input", {"name": "csrf_token"})
        if token:
            return token.get("value")
        return ""

    @task(3)
    def test_compare_datasets(self):
        """
        Prueba la comparación entre las versiones fijas V1 y V2.
        """
        url = f"/dataset/compare/{DATASET_V1_ID}/{DATASET_V2_ID}"

        with self.client.get(
            url, catch_response=True, name="/dataset/compare/[id]/[id]"
        ) as response:
            if response.status_code == 200:
                self.extract_and_request_file_diff(response.text)
            elif response.status_code == 404:
                response.failure(
                    f"Dataset no encontrado (404). ¿Ejecutaste el seeder nuevo? IDs esperadas: {DATASET_V1_ID}"
                    + "/{DATASET_V2_ID}"
                )
            else:
                response.failure(f"Error al cargar comparacion: {response.status_code}")

    @task(1)
    def test_create_version_page(self):
        """
        Entra a la página de crear nueva versión desde la V2
        """
        self.client.get(
            f"/dataset/{DATASET_V2_ID}/create_version",
            name="/dataset/[id]/create_version",
        )


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
                DatasetUser._cached_dois = [
                    doi[0] for doi in datasets_with_doi if doi[0]
                ]
        except Exception:
            DatasetUser._cached_dois = []

    @task(2)
    def list_datasets(self):
        self.client.get("/dataset/list")

    @task(3)
    def view_dataset(self):
        dataset_id = random.randint(1, 2)
        if (dataset_id == 1):
            dataset_id = DATASET_V1_ID
        else:
            dataset_id = DATASET_V2_ID
        self.client.get(f"/dataset/unsynchronized/{dataset_id}/")

    @task(2)
    def download_dataset(self):
        dataset_id = random.randint(1, 2)
        if (dataset_id == 1):
            dataset_id = DATASET_V1_ID
        else:
            dataset_id = DATASET_V2_ID
        self.client.get(f"/dataset/download/{dataset_id}")

    @task(1)
    def compare_datasets(self):
        old_id = DATASET_V1_ID
        new_id = DATASET_V2_ID
        self.client.get(f"/dataset/compare/{old_id}/{new_id}")

    @task(3)  # Aumento de peso para simular más tráfico en esta ruta
    def view_dataset_and_recommendations(self):
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
        dataset_id = random.randint(1, 2)
        if (dataset_id == 1):
            dataset_id = DATASET_V1_ID
        else:
            dataset_id = DATASET_V2_ID
        self.client.get(f"/dataset/{dataset_id}/create_version")

    @task(1)
    def create_version_post(self):
        dataset_id = random.randint(1, 2)
        if (dataset_id == 1):
            dataset_id = DATASET_V1_ID
        else:
            dataset_id = DATASET_V2_ID
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
        old_file_id = DATASET_V1_ID
        new_file_id = DATASET_V2_ID
        if old_file_id != new_file_id:
            self.client.get(f"/file/diff/{old_file_id}/{new_file_id}")

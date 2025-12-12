from bs4 import BeautifulSoup
from locust import HttpUser, between, task

from core.locust.common import get_csrf_token

DATASET_V1_ID = 9991
DATASET_V2_ID = 9992

USER_EMAIL = "user1@example.com"
USER_PASSWORD = "1234"


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://localhost:5000"

    def on_start(self):
        """
        Se ejecuta al iniciar el usuario.
        Usamos la función importada get_csrf_token, igual que en CartUser.
        """
        response = self.client.get("/login")
        csrf_token = get_csrf_token(response)

        if not csrf_token:
            print("Error: No se pudo obtener CSRF token en login.")
            self.stop()
            return

        self.client.post(
            "/login",
            data={
                "email": USER_EMAIL,
                "password": USER_PASSWORD,
                "csrf_token": csrf_token,
            },
        )

    @task(3)
    def test_compare_datasets(self):
        """
        Tests compare datasets page and file diffs.
        """
        url = f"/dataset/compare/{DATASET_V1_ID}/{DATASET_V2_ID}"

        with self.client.get(url, catch_response=True, name="/dataset/compare/[id]/[id]") as response:
            if response.status_code == 200:
                self.extract_and_request_file_diff(response.text)
                response.success()
            elif response.status_code == 404:
                response.failure(f"Dataset no encontrado (404). IDs esperados: {DATASET_V1_ID}/{DATASET_V2_ID}")
            else:
                response.failure(f"Error {response.status_code} al cargar comparación")

    @task(1)
    def test_create_version_page(self):
        """
        Visits the create version page for a dataset.
        """
        self.client.get(
            f"/dataset/{DATASET_V2_ID}/create_version",
            name="/dataset/[id]/create_version",
        )

    @task(1)
    def test_upload_github(self):
        """
        Prueba la subida de ficheros desde GitHub.
        """
        payload = {
            "repo_url": "https://github.com/JoseLu2121/pix_files.git",
            "path": "files/"
        }
        self.client.post("/dataset/file/upload_github", json=payload, name="/dataset/file/upload_github")

    def extract_and_request_file_diff(self, html_content):
        """
        This function parses the HTML content to find file diff buttons and simulates
        the AJAX requests that would be made when those buttons are clicked.
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            button = soup.find("button", attrs={"onclick": "showDiff(this)"})

            if button:
                old_id = button.get("data-old-id")
                new_id = button.get("data-new-id")

                if old_id and new_id:
                    self.client.get(f"/file/diff/{old_id}/{new_id}", name="/file/diff/[id]/[id]")
        except Exception as e:
            print(f"Error parseando diffs: {e}")

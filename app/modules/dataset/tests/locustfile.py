import logging

from bs4 import BeautifulSoup
from locust import HttpUser, between, task

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
            "/login", data={"email": USER_EMAIL, "password": USER_PASSWORD, "csrf_token": csrf_token}
        )

        if response.status_code == 200 and "login" not in response.url:
            logging.info(f"Login Exitoso: {USER_EMAIL}")
        else:
            if "/login" in response.url:
                logging.error("!!! Login Fallido: Credenciales incorrectas o error de servidor !!!")
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

        with self.client.get(url, catch_response=True, name="/dataset/compare/[id]/[id]") as response:
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
        self.client.get(f"/dataset/{DATASET_V2_ID}/create_version", name="/dataset/[id]/create_version")

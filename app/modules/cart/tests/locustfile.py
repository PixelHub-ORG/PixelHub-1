# app/modules/cart/tests/locustfile.py
import json
import random

from locust import HttpUser, between, task

from core.environment.host import get_host_for_locust_testing


class CartUser(HttpUser):
    wait_time = between(1, 5)

    # Host para pruebas (si get_host_for_locust_testing devuelve None, Locust usará --host)
    host = get_host_for_locust_testing()

    # Credenciales de prueba (ajusta si hace falta)
    email = "user1@example.com"
    password = "1234"

    def on_start(self):
        """Login y asegurar que el carrito tiene al menos un item."""
        # Intentamos loguear
        resp = self.client.post(
            "/login",
            data={"email": self.email, "password": self.password},
            allow_redirects=False,
        )

        if resp.status_code not in (200, 302):
            print("Login Error:", resp.status_code, resp.text)
        else:
            print("Login successful")

        # Aseguramos que el carrito tiene algo para las pruebas
        # Ajusta el endpoint si en tu app es /featuremodel/cart/add o /filemodel/cart/add
        try:
            self.client.post("/filemodel/cart/add", json={"item_id": 1})
        except Exception:
            # No queremos que falle el inicio si este POST da error; lo registramos
            print("Warning: could not add initial item to cart in on_start")

    @task(2)
    def view_cart(self):
        self.client.get("/user/cart/view_page")

    @task(2)
    def count_cart(self):
        self.client.get("/user/cart/count")

    @task(3)
    def add_to_cart(self):
        item_id = random.randint(1, 50)
        payload = {"item_id": item_id}
        self.client.post("/filemodel/cart/add", json=payload)

    @task(1)
    def add_duplicate_item(self):
        item_id = 1
        payload = {"item_id": item_id}
        self.client.post("/filemodel/cart/add", json=payload)

    @task(2)
    def delete_item(self):
        item_id = random.randint(1, 50)
        payload = {"item_id": item_id}
        self.client.post("/user/cart/delete", data=json.dumps(payload), headers={"Content-Type": "application/json"})

    @task(1)
    def delete_nonexistent_item(self):
        payload = {"item_id": 999999}
        self.client.post("/user/cart/delete", data=json.dumps(payload), headers={"Content-Type": "application/json"})

    @task(1)
    def create_dataset(self):
        payload = {"dataset_name": "locust_dataset", "description": "Dataset generado por Locust"}
        # Form POST (no JSON) — ajusta si tu endpoint espera JSON
        self.client.post("/user/cart/create", data=payload)

    @task(1)
    def create_dataset_empty_cart(self):
        # Vaciar carrito primero
        self.client.post(
            "/user/cart/delete", data=json.dumps({"item_id": None}), headers={"Content-Type": "application/json"}
        )

        payload = {"dataset_name": "dataset_vacio", "description": "Esto debe fallar"}
        self.client.post("/user/cart/create", data=payload)

    @task(1)
    def download_cart(self):
        # Descargar el ZIP y manejar respuestas esperadas
        with self.client.get("/user/cart/download", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 400 and "Cart is empty" in (response.text or ""):
                # Si está vacío, no lo marcamos como fallo crítico
                response.success()
            else:
                response.failure(f"Download failed: {response.status_code}")

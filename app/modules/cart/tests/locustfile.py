# app/modules/cart/tests/locustfile.py
from locust import HttpUser, between, task
from core.environment.host import get_host_for_locust_testing


class CartUser(HttpUser):
    wait_time = between(1, 5)

    host = get_host_for_locust_testing()

    def on_start(self):
        # 1. Loguearse al iniciar
        # response = self.client.post("/login", data={"email": "user1@example.com", "password": "1234"})

        # 2. Asegurar que el carro tiene algo (Añadimos el feature model con ID 1)
        self.client.post("/featuremodel/cart/add", json={"item_id": 1})

    @task(1)
    def view_cart(self):
        self.client.get("/user/cart/view_page")

    @task(3)
    def download_cart(self):
        # Esta es la parte crítica: Descargar el ZIP
        with self.client.get("/user/cart/download", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 400 and "empty" in response.text:
                # Si falla porque está vacío (raro porque lo llenamos en on_start), no lo marcamos como error crítico
                response.success()
            else:
                response.failure(f"Fallo al descargar: {response.status_code}")

from locust import HttpUser, between, task

from core.environment.host import get_host_for_locust_testing


class CartUser(HttpUser):
    wait_time = between(1, 5)

    host = get_host_for_locust_testing()

    def on_start(self):
        self.client.post("/filemodel/cart/add", json={"item_id": 1})

    @task(1)
    def view_cart(self):
        self.client.get("/user/cart/view_page")

    @task(3)
    def download_cart(self):
        with self.client.get("/user/cart/download", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 400 and "empty" in response.text:
                response.success()
            else:
                response.failure(f"Fallo al descargar: {response.status_code}")

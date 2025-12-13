import json
import random

from locust import HttpUser, between, task


class CartUser(HttpUser):
    wait_time = between(1, 3)

    email = "user1@example.com"
    password = "1234"

    def on_start(self):
        resp = self.client.post("/login", data={"email": self.email, "password": self.password}, allow_redirects=False)

        if resp.status_code not in (200, 302):
            print("Login Error:", resp.status_code, resp.text)
        else:
            print("Login successful")

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

        self.client.post("/filemodel/cart/add", data=json.dumps(payload), headers={"Content-Type": "application/json"})

    @task(1)
    def add_duplicate_item(self):
        item_id = 1
        payload = {"item_id": item_id}

        self.client.post("/filemodel/cart/add", data=json.dumps(payload), headers={"Content-Type": "application/json"})

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

        self.client.post("/user/cart/create", data=payload)

    @task(1)
    def create_dataset_empty_cart(self):
        self.client.post(
            "/user/cart/delete", data=json.dumps({"item_id": None}), headers={"Content-Type": "application/json"}
        )

        payload = {"dataset_name": "dataset_vacio", "description": "Esto debe fallar"}

        self.client.post("/user/cart/create", data=payload)

    @task(1)
    def download_cart(self):
        self.client.get("/user/cart/download")

    @task(1)
    def download_empty_cart(self):
        self.client.post(
            "/user/cart/delete", data=json.dumps({"item_id": None}), headers={"Content-Type": "application/json"}
        )

        self.client.get("/user/cart/download")

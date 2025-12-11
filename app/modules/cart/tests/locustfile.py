from locust import HttpUser, between, task

from core.locust.common import get_csrf_token


class CartUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        response = self.client.get("/login")
        csrf_token = get_csrf_token(response)
        
        self.client.post("/login", data={
            "email": "user1@example.com",
            "password": "1234",
            "csrf_token": csrf_token
        })

    @task(3)
    def view_cart(self):
        """Tarea frecuente: Ver el carrito"""
        self.client.get("/user/cart/view_page")

    @task(2)
    def add_item(self):
        """Tarea media: Añadir item (ID 1, asumiendo que existe por seeders)"""
        self.client.post("/filemodel/cart/add", json={"item_id": 1})

    @task(1)
    def create_dataset(self):
        """Tarea pesada: Crear dataset (requiere CSRF)"""
        # Primero añadimos algo para que no falle por vacío
        self.client.post("/filemodel/cart/add", json={"item_id": 1})
        
        # Obtener formulario para el token
        resp = self.client.get("/user/cart/create")
        csrf = get_csrf_token(resp)

        self.client.post("/user/cart/create", data={
            "title": "Locust Load Test",
            "publication_type": "none",
            "csrf_token": csrf
        })

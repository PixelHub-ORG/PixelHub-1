from locust import HttpUser, TaskSet, between, task

# Importamos el 'host' desde tu módulo de core
from core.environment.host import get_host_for_locust_testing

# No necesitamos get_csrf_token para estas rutas GET simples


class ZenodoBehavior(TaskSet):
    """
    Define el comportamiento de un usuario que interactúa
    con los endpoints de Zenodo.
    """

    @task(1)
    def view_zenodo_index(self):
        """
        Simula a un usuario visitando la página principal de Zenodo.
        """
        self.client.get("/zenodo", name="/zenodo")

    @task(3)
    def test_zenodo_connection(self):
        """
        Simula a un usuario llamando al endpoint de prueba de conexión.
        """
        self.client.get("/zenodo/test", name="/zenodo/test")


class ZenodoUser(HttpUser):
    """
    Define el tipo de usuario que ejecutará las tareas de Zenodo.
    """

    tasks = [ZenodoBehavior]

    wait_time = between(5, 9)  # Equivalente a min_wait/max_wait de 5000/9000 ms

    host = get_host_for_locust_testing()

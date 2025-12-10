import random

from locust import HttpUser, TaskSet, between, events, task
from core.environment.host import get_host_for_locust_testing

CACHED_FILE_IDS = []


@events.init.add_listener
def load_file_ids(environment, **kwargs):
    """
    Precarga IDs solo cuando Locust se ejecuta de verdad.
    Evita romper tests, 'locust --check', o imports del locustfile.
    """

    # Si no existe runner → estamos en modo check/test → NO ejecutar
    if environment.runner is None:
        return

    global CACHED_FILE_IDS

    try:
        # Lazy import para evitar fallos al importar este archivo en tests
        from app import create_app, db
        from app.modules.hubfile.models import Hubfile

        app = create_app()

        with app.app_context():
            ids = db.session.query(Hubfile.id).limit(50).all()
            CACHED_FILE_IDS = [row[0] for row in ids]

        if not CACHED_FILE_IDS:
            print("WARNING: No Hubfiles found in database for load testing")

    except Exception as exc:
        # Nunca detener Locust: solo avisar
        print(f"Error fetching file IDs: {exc}")
        CACHED_FILE_IDS = []


class PixcheckerBehavior(TaskSet):
    def on_start(self):
        if not CACHED_FILE_IDS:
            print("WARNING: Hubfile ID cache empty; pixchecker tasks will be skipped")

    @task
    def check_pix_valid_file(self):
        if not CACHED_FILE_IDS:
            return

        file_id = random.choice(CACHED_FILE_IDS)
        with self.client.get(f"/pixchecker/check_pix/{file_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(weight=1)
    def check_pix_missing_file(self):
        with self.client.get("/pixchecker/check_pix/9999999999", catch_response=True) as response:
            if response.status_code == 404:
                response.success()
            else:
                response.failure(f"Expected 404, got {response.status_code}")


class PixcheckerUser(HttpUser):
    tasks = [PixcheckerBehavior]
    wait_time = between(5, 9)
    host = get_host_for_locust_testing()

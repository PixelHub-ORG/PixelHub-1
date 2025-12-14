from locust import HttpUser, TaskSet, task

from app import create_app
from app.modules.auth.models import User
from core.environment.host import get_host_for_locust_testing

app = create_app()


class ProfileBehavior(TaskSet):

    def on_start(self):
        self.user_id = self.get_first_available_user_id()

        if self.user_id:
            self.view_public_profile()
        else:
            print("WARNING: No hay usuarios en la BBDD para probar.")

    def get_first_available_user_id(self):
        """
        Consulta la BBDD directamente para sacar el primer ID de usuario que exista.
        """
        try:
            with app.app_context():
                user = User.query.first()
                if user:
                    return user.id
        except Exception as e:
            print(f"Error conectando a la BBDD desde Locust: {e}")

        return None

    @task
    def view_public_profile(self):
        if not self.user_id:
            return

        response = self.client.get(f"/profile/{self.user_id}")

        if response.status_code != 200:
            print(
                f"Profile view failed for User ID {
                    self.user_id}: {
                    response.status_code}"
            )


class ProfileUser(HttpUser):
    tasks = [ProfileBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()

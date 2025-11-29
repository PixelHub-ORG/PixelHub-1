from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing


class ProfileBehavior(TaskSet):
    def on_start(self):
        self.view_public_profile()

    @task
    def view_public_profile(self):
        response = self.client.get("/profile/1")
        if response.status_code != 200:
            print(f"Profile view failed: {response.status_code}")


class ProfileUser(HttpUser):
    tasks = [ProfileBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()

from locust import HttpUser, TaskSet

from core.environment.host import get_host_for_locust_testing


class PixcheckerBehavior(TaskSet):
    def on_start(self):
        self.index()


class PixcheckerUser(HttpUser):
    tasks = [PixcheckerBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()

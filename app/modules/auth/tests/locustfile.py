from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token


class SignupBehavior(TaskSet):
    def on_start(self):
        self.signup()

    @task
    def signup(self):
        response = self.client.get("/signup")
        csrf_token = get_csrf_token(response)

        response = self.client.post(
            "/signup", data={"email": fake.email(), "password": fake.password(), "csrf_token": csrf_token}
        )
        if response.status_code != 200:
            print(f"Signup failed: {response.status_code}")


class LoginBehavior(TaskSet):
    def on_start(self):
        self.ensure_logged_out()
        self.login()

    @task
    def ensure_logged_out(self):
        response = self.client.get("/logout")
        if response.status_code != 200:
            print(f"Logout failed or no active session: {response.status_code}")

    @task
    def login(self):
        response = self.client.get("/login")
        if response.status_code != 200 or "Login" not in response.text:
            print("Already logged in or unexpected response, redirecting to logout")
            self.ensure_logged_out()
            response = self.client.get("/login")

        csrf_token = get_csrf_token(response)

        response = self.client.post(
            "/login", data={"email": "user1@example.com", "password": "1234", "csrf_token": csrf_token}
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")


class OrcidBehavior(TaskSet):
    @task
    def start_orcid_login(self):
        # We expect a redirect to ORCID, but we don't want to follow it to avoid loading their servers
        response = self.client.get("/auth/orcid/login", allow_redirects=False)
        if response.status_code != 302:
            print(f"Orcid login did not redirect: {response.status_code}")

    @task
    def orcid_callback_failure(self):
        # Test callback with invalid code - should fail gracefully (e.g. redirect to login with error)
        response = self.client.get("/auth/orcid/callback?code=invalid_code", allow_redirects=True)
        # We expect it to redirect us back to login page or just load the login page with an error
        # Assuming it handles exceptions and renders the login form (status 200)
        if response.status_code != 200:
            print(f"Orcid callback failed to handle error: {response.status_code}")


class AuthUser(HttpUser):
    tasks = [SignupBehavior, LoginBehavior, OrcidBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()

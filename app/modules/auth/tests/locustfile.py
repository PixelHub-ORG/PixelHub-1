from locust import HttpUser, TaskSet, between, events, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token

CACHED_2FA_USERS = []


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    global CACHED_2FA_USERS
    try:
        from app import create_app, db
        from app.modules.auth.models import User

        app = create_app()
        with app.app_context():
            users_with_2fa = (
                db.session.query(User)
                .filter(User.is_two_factor_enabled)
                .filter(User.two_factor_secret.isnot(None))
                .limit(20)
                .all()
            )
            for user in users_with_2fa:
                CACHED_2FA_USERS.append({"email": user.email, "secret": user.two_factor_secret, "password": "1234"})
            print(f"✓ Loaded {len(CACHED_2FA_USERS)} users with 2FA for testing")
            if not CACHED_2FA_USERS:
                print("⚠ WARNING: No users with 2FA enabled found.")
    except Exception as e:
        print(f"✗ Error loading 2FA users: {e}")
        CACHED_2FA_USERS = []


class SignupBehavior(TaskSet):
    def on_start(self):
        self.signup()

    @task
    def signup(self):
        response = self.client.get("/signup")
        csrf_token = get_csrf_token(response)
        email = fake.email()
        password = fake.password()
        name = fake.first_name()
        surname = fake.last_name()
        with self.client.post(
            "/signup",
            data={"email": email, "password": password, "name": name, "surname": surname, "csrf_token": csrf_token},
            catch_response=True,
            name="POST /signup",
        ) as response:
            if response.status_code in [200, 302]:
                response.success()
            elif "in use" in response.text:
                response.success()
            else:
                response.failure(f"Signup failed: {response.status_code}")


class LoginBehavior(TaskSet):
    def on_start(self):
        self.ensure_logged_out()
        self.login()

    @task
    def ensure_logged_out(self):
        with self.client.get("/logout", catch_response=True, name="GET /logout") as response:
            if response.status_code in [200, 302]:
                response.success()

    @task
    def login(self):
        response = self.client.get("/login")
        if response.status_code != 200 or "Login" not in response.text:
            self.ensure_logged_out()
            response = self.client.get("/login")
        csrf_token = get_csrf_token(response)
        with self.client.post(
            "/login",
            data={"email": "user1@example.com", "password": "1234", "csrf_token": csrf_token},
            catch_response=True,
            name="POST /login (no 2FA)",
        ) as response:
            if response.status_code in [200, 302]:
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")


class TwoFactorSetupBehavior(TaskSet):
    def on_start(self):
        self.signup_and_setup_2fa()

    def signup_for_2fa_setup(self):
        response = self.client.get("/signup")
        csrf_token = get_csrf_token(response)
        email = fake.email()
        password = fake.password()
        with self.client.post(
            "/signup",
            data={
                "email": email,
                "password": password,
                "name": fake.first_name(),
                "surname": fake.last_name(),
                "csrf_token": csrf_token,
            },
            catch_response=True,
            name="POST /signup (for 2FA setup)",
        ) as response:
            if response.status_code in [200, 302]:
                response.success()
                return email, password
        return None, None

    @task(3)
    def signup_and_setup_2fa(self):
        email, password = self.signup_for_2fa_setup()
        if not email:
            return
        with self.client.get("/2fa/enable", catch_response=True, name="GET /2fa/enable") as response:
            if response.status_code != 200:
                response.failure(f"Failed to access 2FA setup: {response.status_code}")
                return
            response.success()
            try:
                csrf_token = get_csrf_token(response)
            except ValueError:
                return
        with self.client.post(
            "/2fa/enable",
            data={"code": "123456", "csrf_token": csrf_token},
            catch_response=True,
            name="POST /2fa/enable",
        ) as response:
            response.success()
            if response.status_code not in [200, 302]:
                print(f"POST /2fa/enable returned {response.status_code}")

    @task(2)
    def test_2fa_enable_with_code(self):
        response = self.client.get("/login")
        csrf_token = get_csrf_token(response)
        self.client.post("/login", data={"email": "user1@example.com", "password": "1234", "csrf_token": csrf_token})
        response = self.client.get("/2fa/enable")
        try:
            csrf_token = get_csrf_token(response)
        except ValueError:
            return
        with self.client.post(
            "/2fa/enable",
            data={"code": "999999", "csrf_token": csrf_token},
            catch_response=True,
            name="POST /2fa/enable",
        ) as response:
            response.success()


class AuthUser(HttpUser):
    tasks = [SignupBehavior, LoginBehavior, TwoFactorSetupBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
    wait_time = between(1, 3)

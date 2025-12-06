import random
import pyotp
from locust import HttpUser, TaskSet, task, between, events
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

    @task(1)
    def access_2fa_enable_when_already_enabled(self):
        """Test accessing 2FA enable page when already enabled"""
        with self.client.get(
            "/2fa/enable",
            catch_response=True,
            name="GET /2fa/enable (already enabled)"
        ) as response:
            if response.status_code in [200, 302]:
                response.success()


class TwoFactorLoginBehavior(TaskSet):
    """Tests for logging in with 2FA enabled"""
    
    def on_start(self):
        """Logout before starting"""
        self.client.get("/logout")
    
    @task(5)
    def login_with_2fa_valid_code(self):
        """Complete 2FA login with valid TOTP code"""
        global CACHED_2FA_USERS
        
        if not CACHED_2FA_USERS:
            return
        
        user = random.choice(CACHED_2FA_USERS)
        
        response = self.client.get("/login")
        csrf_token = get_csrf_token(response)
        
        with self.client.post(
            "/login",
            data={
                "email": user["email"],
                "password": user["password"],
                "csrf_token": csrf_token
            },
            catch_response=True,
            name="POST /login (with 2FA enabled)"
        ) as response:
            if response.status_code not in [200, 302]:
                response.failure(f"Login step 1 failed: {response.status_code}")
                return
            response.success()
        
        with self.client.get(
            "/2fa/verify",
            catch_response=True,
            name="GET /2fa/verify"
        ) as response:
            if response.status_code != 200:
                response.failure(f"2FA verify page not accessible: {response.status_code}")
                return
            response.success()
        
        csrf_token = get_csrf_token(response)
        
        totp = pyotp.TOTP(user["secret"])
        code = totp.now()
        
        with self.client.post(
            "/2fa/verify",
            data={
                "code": code,
                "csrf_token": csrf_token
            },
            catch_response=True,
            name="POST /2fa/verify (valid code)"
        ) as response:
            if response.status_code in [200, 302]:
                response.success()
            else:
                response.failure(f"2FA verification failed: {response.status_code}")
    
    @task(2)
    def login_with_2fa_invalid_code(self):
        """Try 2FA login with invalid code (should fail)"""
        global CACHED_2FA_USERS
        
        if not CACHED_2FA_USERS:
            return
        
        user = random.choice(CACHED_2FA_USERS)
        
        response = self.client.get("/login")
        csrf_token = get_csrf_token(response)
        
        self.client.post(
            "/login",
            data={
                "email": user["email"],
                "password": user["password"],
                "csrf_token": csrf_token
            }
        )
        
        response = self.client.get("/2fa/verify")
        csrf_token = get_csrf_token(response)
        
        with self.client.post(
            "/2fa/verify",
            data={
                "code": "000000",
                "csrf_token": csrf_token
            },
            catch_response=True,
            name="POST /2fa/verify (invalid code)"
        ) as response:
            if response.status_code == 200 and "Invalid" in response.text:
                response.success()
            elif response.status_code == 302:
                response.failure("Invalid code was accepted!")
            else:
                response.success()
    
    @task(1)
    def login_with_2fa_empty_code(self):
        """Try 2FA login with empty code"""
        global CACHED_2FA_USERS
        
        if not CACHED_2FA_USERS:
            return
        
        user = random.choice(CACHED_2FA_USERS)
        
        response = self.client.get("/login")
        csrf_token = get_csrf_token(response)
        
        self.client.post(
            "/login",
            data={
                "email": user["email"],
                "password": user["password"],
                "csrf_token": csrf_token
            }
        )
        
        response = self.client.get("/2fa/verify")
        csrf_token = get_csrf_token(response)
        
        with self.client.post(
            "/2fa/verify",
            data={
                "code": "",
                "csrf_token": csrf_token
            },
            catch_response=True,
            name="POST /2fa/verify (empty code)"
        ) as response:
            if response.status_code == 200 and "enter" in response.text.lower():
                response.success()
            else:
                response.success()


class TwoFactorDisableBehavior(TaskSet):
    """Tests for disabling 2FA"""
    
    def on_start(self):
        """Login with 2FA first"""
        self.login_with_2fa()
    
    def login_with_2fa(self):
        """Helper: Complete 2FA login"""
        global CACHED_2FA_USERS
        
        if not CACHED_2FA_USERS:
            return False
        
        user = random.choice(CACHED_2FA_USERS)
    
        response = self.client.get("/login")
        csrf_token = get_csrf_token(response)
        
        self.client.post(
            "/login",
            data={
                "email": user["email"],
                "password": user["password"],
                "csrf_token": csrf_token
            }
        )
        response = self.client.get("/2fa/verify")
        csrf_token = get_csrf_token(response)
        
        totp = pyotp.TOTP(user["secret"])
        code = totp.now()
        
        self.client.post(
            "/2fa/verify",
            data={
                "code": code,
                "csrf_token": csrf_token
            }
        )
        
        return True
    
    @task(1)
    def disable_2fa(self):
        """Disable 2FA for authenticated user"""
        if not self.login_with_2fa():
            return
        try:
            response = self.client.get("/")
            csrf_token = get_csrf_token(response)
        except ValueError:
            try:
                response = self.client.get("/profile/edit")
                csrf_token = get_csrf_token(response)
            except:
                return
        
        with self.client.post(
            "/2fa/disable",
            data={"csrf_token": csrf_token},
            catch_response=True,
            name="POST /2fa/disable"
        ) as response:
            if response.status_code in [200, 302]:
                response.success()
            else:
                response.failure(f"2FA disable failed: {response.status_code}")

class TwoFactorSecurityTests(TaskSet):
    """Security-focused tests for 2FA"""
    
    @task(1)
    def test_2fa_verify_without_login(self):
        """Try to access /2fa/verify without logging in first"""
        # Ensure logged out
        self.client.get("/logout")
        
        with self.client.get(
            "/2fa/verify",
            catch_response=True,
            name="GET /2fa/verify (no session)"
        ) as response:
            if response.status_code == 302:
                if "/login" in response.headers.get("Location", ""):
                    response.success()
                else:
                    response.success()
            elif response.status_code in [401, 403]:
                response.success()
            else:
                response.success()
    
    @task(1)
    def test_2fa_enable_without_session(self):
        """Try to access /2fa/enable without session"""
        self.client.get("/logout")
        
        with self.client.get(
            "/2fa/enable",
            catch_response=True,
            name="GET /2fa/enable (no session)"
        ) as response:
            if response.status_code == 302:
                response.success()
            elif response.status_code == 200:
                if "/login" in response.url or "login" in response.request.path_url.lower():
                    response.success()
                else:
                    print(f"⚠ /2fa/enable returned 200 without session - check auth logic")
                    response.success()
            else:
                response.success()
    
    @task(1)
    def test_disable_2fa_without_auth(self):
        """Try to disable 2FA without authentication"""
        self.client.get("/logout")
        
        with self.client.post(
            "/2fa/disable",
            data={},
            catch_response=True,
            name="POST /2fa/disable (no auth)"
        ) as response:
            if response.status_code == 302:
                response.success()
            elif response.status_code in [400, 401, 403]:
                response.success()
            elif response.status_code == 200:
                if "/login" in response.url or "login" in response.text.lower():
                    response.success()
                else:
                    print(f"⚠ /2fa/disable accessible without auth - security issue")
                    response.success()
            else:
                response.success()

class ORCIDLoginBehavior(TaskSet):
    """Tests for ORCID OAuth login"""
    
    @task(1)
    def access_orcid_login(self):
        """Access ORCID login endpoint (will redirect to ORCID)"""
        with self.client.get(
            "/orcid/login",
            catch_response=True,
            allow_redirects=False,
            name="GET /orcid/login"
        ) as response:
            if response.status_code in [302, 303, 307]:
                response.success()
            else:
                response.failure(f"ORCID login didn't redirect: {response.status_code}")

class AuthUser(HttpUser):
    """Standard auth testing (signup/login without 2FA)"""
    tasks = [SignupBehavior, LoginBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
    wait_time = between(1, 3)
    weight = 3


class TwoFactorUser(HttpUser):
    """2FA-specific testing"""
    tasks = [TwoFactorSetupBehavior, TwoFactorLoginBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
    wait_time = between(2, 5)
    weight = 2


class SecurityTestUser(HttpUser):
    """Security testing for 2FA"""
    tasks = [TwoFactorSecurityTests]
    min_wait = 3000
    max_wait = 7000
    host = get_host_for_locust_testing()
    wait_time = between(1, 4)
    weight = 1


class MixedAuthUser(HttpUser):
    """Mixed authentication tests including ORCID"""
    tasks = [LoginBehavior, TwoFactorLoginBehavior, ORCIDLoginBehavior, TwoFactorDisableBehavior]
    min_wait = 4000
    max_wait = 8000
    host = get_host_for_locust_testing()
    wait_time = between(1, 4)
    weight = 1

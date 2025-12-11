import socket
import uuid
from threading import Thread
from unittest.mock import patch
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import create_app, db
from app.modules.auth.models import User
from app.modules.auth.services import AuthenticationService
from core.selenium.common import initialize_driver
from app.modules.profile.models import UserProfile

def get_free_port():
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port

class TestSelenium2FA:

    def setup_method(self, method):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()

        unique_email = f"user_{uuid.uuid4().hex}@example.com"
        self.user = User(
            email=unique_email,
            is_two_factor_enabled=True,
            two_factor_secret="MOCKSECRET"
        )
        self.user.set_password("1234")
        db.session.add(self.user)
        db.session.commit()

        profile = UserProfile(
            user_id=self.user.id,
            name="Sypha",
            surname="Belnades",
            orcid="0000-0001-2345-6789",
            affiliation="Test Lab"
        )
        db.session.add(profile)
        db.session.commit()
        assert self.user.id is not None
        self.port = get_free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        def run_app():
            self.app.run(port=self.port, debug=False, use_reloader=False)
        self.server_thread = Thread(target=run_app)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.driver = initialize_driver()
        self.patcher = patch.object(
            AuthenticationService, "verify_two_factor_code", return_value=True
        )
        self.patcher.start()

    def teardown_method(self, method):
        self.patcher.stop()
        self.driver.quit()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login_with_2fa(self):
        self.driver.get(self.base_url)
        self.driver.set_window_size(1200, 1000)
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "email").send_keys(self.user.email)
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.ID, "submit").click()
        code_input = self.driver.find_element(By.ID, "code")
        code_input.send_keys("000000")
        code_input.send_keys(Keys.ENTER)
        user_span = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "span.text-dark"))
        )
        assert "Sypha" in user_span.text and "Belnades" in user_span.text

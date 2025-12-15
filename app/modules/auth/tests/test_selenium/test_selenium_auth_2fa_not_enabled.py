import socket
import uuid
from threading import Thread

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app import create_app, db
from app.modules.auth.models import User
from app.modules.profile.models import UserProfile
from core.selenium.common import initialize_driver


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
        unique_email_no2fa = f"user_no2fa_{uuid.uuid4().hex}@example.com"
        self.user_no2fa = User(
            email=unique_email_no2fa,
            is_two_factor_enabled=False)
        self.user_no2fa.set_password("1234")
        db.session.add(self.user_no2fa)
        db.session.commit()

        profile2 = UserProfile(
            user_id=self.user_no2fa.id,
            name="Trevor",
            surname="Belmont",
            orcid="0000-0002-1111-2222",
            affiliation="Test Lab",
        )
        db.session.add(profile2)
        db.session.commit()
        self.port = get_free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"

        def run_app():
            self.app.run(port=self.port, debug=False, use_reloader=False)

        self.server_thread = Thread(target=run_app)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.driver = initialize_driver()

    def teardown_method(self, method):
        self.driver.quit()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login_without_2fa(self):
        self.driver.get(self.base_url)
        self.driver.find_element(By.LINK_TEXT, "Login").click()

        self.driver.find_element(
            By.ID, "email").send_keys(
            self.user_no2fa.email)
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.ID, "submit").click()

        with pytest.raises(Exception):
            self.driver.find_element(By.ID, "code")

        user_span = WebDriverWait(
            self.driver, 10).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "span.text-dark")))

        assert "Trevor" in user_span.text
        assert "Belmont" in user_span.text

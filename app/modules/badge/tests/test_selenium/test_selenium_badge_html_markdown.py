import socket
import uuid
from threading import Thread

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app import create_app, db
from app.modules.auth.models import User
from app.modules.dataset.models import Author, DataSet, DSMetaData
from app.modules.profile.models import UserProfile
from core.selenium.common import initialize_driver


def get_free_port():
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class TestDownloadSVG:

    def setup_method(self, method):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()
        unique_email = f"user_{uuid.uuid4().hex}@example.com"
        self.user = User(email=unique_email)
        self.user.set_password("1234")
        db.session.add(self.user)
        db.session.commit()
        profile = UserProfile(
            user_id=self.user.id,
            name="Maria",
            surname="Renard",
            orcid="0000-0000-0000-0000",
            affiliation="Test Lab")
        db.session.add(profile)
        db.session.commit()
        self.metadata = DSMetaData(
            title="Test Dataset",
            description="This is a test dataset",
            publication_type="NONE")
        db.session.add(self.metadata)
        db.session.commit()
        author = Author(name="Maria Renard", ds_meta_data_id=self.metadata.id)
        db.session.add(author)
        db.session.commit()
        self.dataset = DataSet(
            user_id=self.user.id,
            ds_meta_data_id=self.metadata.id)
        db.session.add(self.dataset)
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

    def test_badge_embed_endpoint(self):
        self.driver.get(f"{self.base_url}/badge/{self.dataset.id}/embed")
        self.driver.set_window_size(1200, 800)

        table = WebDriverWait(
            self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "treeTable")))

        print(table)

        html_cell = self.driver.find_element(
            By.XPATH, '//tr[@id="/html"]//td[contains(@class,"treeValueCell")]')
        markdown_cell = self.driver.find_element(
            By.XPATH, '//tr[@id="/markdown"]//td[contains(@class,"treeValueCell")]')

        html_value = html_cell.text
        markdown_value = markdown_cell.text

        assert html_value
        assert markdown_value

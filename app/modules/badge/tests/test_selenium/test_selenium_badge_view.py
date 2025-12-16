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
            user_id=self.user.id, name="Richter", surname="Belmont", orcid="0000-0000-0000-0000", affiliation="Test Lab"
        )
        db.session.add(profile)
        db.session.commit()
        self.metadata = DSMetaData(title="Test Dataset", description="This is a test dataset", publication_type="NONE")
        db.session.add(self.metadata)
        db.session.commit()
        author = Author(name="Richter Belmont", ds_meta_data_id=self.metadata.id)
        db.session.add(author)
        db.session.commit()
        self.dataset = DataSet(user_id=self.user.id, ds_meta_data_id=self.metadata.id)
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

    def test_viewsvg(self):
        self.driver.get(f"{self.base_url}/badge/{self.dataset.id}/svg")
        svg_element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "svg")))

        assert svg_element is not None
        outer_html = svg_element.get_attribute("outerHTML")
        assert outer_html.startswith("<svg")
        assert "<text" in outer_html

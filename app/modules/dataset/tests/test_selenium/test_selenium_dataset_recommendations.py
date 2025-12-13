import time
from unittest.mock import patch

from selenium.webdriver.common.by import By

from app import create_app, db
from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import initialize_driver


class FakeDataset:
    """Dataset simulado para pruebas Selenium."""

    def __init__(self, title, recommendations=None):
        self.title = title
        self.recommendations = recommendations or []


class TestRelatedDB:
    def setup_method(self, method):

        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        self.ds1 = FakeDataset("Sample dataset 1")
        self.ds2 = FakeDataset("Sample dataset 2")
        self.ds3 = FakeDataset("Sample dataset 3")
        self.ds4 = FakeDataset("Sample dataset 4", recommendations=[self.ds1, self.ds2, self.ds3])

        self.patcher = patch("app.modules.dataset.models.DataSet.query.get", side_effect=self.fake_get)
        self.patcher.start()

        self.driver = initialize_driver()
        self.driver.get(get_host_for_selenium_testing())

    def teardown_method(self, method):
        self.patcher.stop()
        self.driver.quit()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def fake_get(self, id):
        """Devuelve un dataset fake según el id solicitado."""
        mapping = {1: self.ds1, 2: self.ds2, 3: self.ds3, 4: self.ds4}
        return mapping.get(id, FakeDataset(f"Sample dataset {id}"))

    def test_relatedDB(self):
        """Test Selenium: abre dataset 4 y navega por recomendaciones fake."""
        self.driver.get(get_host_for_selenium_testing())
        self.driver.set_window_size(1600, 1000)

        self.driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        time.sleep(1)

        for rec_title in ["Sample dataset 1", "Sample dataset 2", "Sample dataset 3"]:
            self.driver.find_element(By.LINK_TEXT, rec_title).click()
            time.sleep(1)
            self.driver.back()
            time.sleep(1)

        self.driver.find_element(By.LINK_TEXT, "Sample dataset 3").click()
        time.sleep(1)
        assert "Sample dataset 3" in self.driver.page_source

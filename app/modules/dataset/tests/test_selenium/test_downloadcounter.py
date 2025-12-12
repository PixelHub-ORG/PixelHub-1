from selenium.webdriver.common.by import By

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


class TestDownloadcounter:
    def setup_method(self, method):
        self.driver = initialize_driver()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_downloadcounter(self):
        host = get_host_for_selenium_testing()
        self.driver.get(host)
        self.driver.set_window_size(810, 1095)
        self.driver.find_element(By.LINK_TEXT, "Download (21.18 KB)").click()
        close_driver(self.driver)

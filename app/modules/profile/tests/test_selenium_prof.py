import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def test_view_user_profile_from_dataset():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        driver.get(f"{host}/doi/10.1234/dataset1")
        time.sleep(4)

        try:
            user_link = driver.find_element(
                By.XPATH, "//a[contains(@href, '/profile/')]")
        except NoSuchElementException:
            raise AssertionError("User profile link not found on dataset page")

        user_link.click()
        time.sleep(4)

        current_url = driver.current_url
        if not current_url.startswith(f"{host}/profile/"):
            raise AssertionError(
                f"Unexpected URL after clicking user profile link: {current_url}")

        try:
            driver.find_element(
                By.XPATH, "//h1[contains(@class, 'h3') and contains(., 'User profile')]")
        except NoSuchElementException:
            raise AssertionError(
                "User profile header not found on profile page")

    finally:
        close_driver(driver)

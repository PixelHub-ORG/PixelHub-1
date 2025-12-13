import os
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def wait_for_page_to_load(driver, timeout=4):
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )


def test_dataset_creation_with_fakenodo_enabled():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)

        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")
        password_field.send_keys(Keys.RETURN)

        time.sleep(3)
        wait_for_page_to_load(driver)

        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        title = driver.find_element(By.ID, "title")
        title.send_keys("Ejemplo Fakenodo")

        desc = driver.find_element(By.NAME, "desc")
        desc.send_keys("Hola")

        dropdown = driver.find_element(By.ID, "publication_type")
        dropdown.click()
        dropdown.find_element(By.XPATH, "//option[. = 'Working Paper']").click()
        wait_for_page_to_load(driver)

        file_input_element = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        file_path = os.path.abspath("app/modules/dataset/uvl_examples/file1.uvl")
        file_input_element.send_keys(file_path)

        agree_checkbox = driver.find_element(By.ID, "agreeCheckbox")
        agree_checkbox.click()

        upload_button = driver.find_element(By.ID, "upload_button")
        upload_button.click()
        time.sleep(5)
        wait_for_page_to_load(driver)

        first_dataset_link = driver.find_element(By.CSS_SELECTOR, "tbody tr:first-child a")
        first_dataset_link.click()
        wait_for_page_to_load(driver)
        time.sleep(2)

        original_tab = driver.current_window_handle
        selector = "a[href^='http://localhost:5001/api/depositions/']"
        fakenodo_link = driver.find_element(By.CSS_SELECTOR, selector)
        driver.execute_script("arguments[0].click();", fakenodo_link)
        time.sleep(2)
        all_tabs = driver.window_handles

        new_tab = [tab for tab in all_tabs if tab != original_tab][0]
        driver.switch_to.window(new_tab)

        try:

            json_text = driver.find_element(By.TAG_NAME, "pre").text
        except NoSuchElementException:

            json_text = driver.find_element(By.TAG_NAME, "body").text

        # checks if fakenodo object exists
        assert "Not Found" not in json_text
        assert "404" not in json_text

        print("Fakenodo JSON exists!")
        print("Fakenodo test passed!")

    finally:
        close_driver(driver)


test_dataset_creation_with_fakenodo_enabled()

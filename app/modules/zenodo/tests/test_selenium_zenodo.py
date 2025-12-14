import os
import time

import pyotp
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def wait_for_page_to_load(driver, timeout=15):
    WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")


def signup_and_handle_2fa_enable(driver, host, email, password):
    wait = WebDriverWait(driver, 15)

    driver.get(f"{host}/signup/")
    wait.until(EC.presence_of_element_located((By.NAME, "name")))

    driver.find_element(By.NAME, "name").send_keys("Zenodo")
    driver.find_element(By.NAME, "surname").send_keys("Tester")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

    wait.until(lambda d: "/2fa/enable" in d.current_url or d.current_url.startswith(host))

    if "/2fa/enable" in driver.current_url:
        p = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.mb-3")))
        secret = p.text.split("Manual secret:")[-1].strip()
        code = pyotp.TOTP(secret).now()
        code_input = wait.until(EC.presence_of_element_located((By.NAME, "code")))
        code_input.clear()
        code_input.send_keys(code)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(lambda d: "/2fa/enable" not in d.current_url)


def test_dataset_creation_with_fakenodo_enabled():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        ts = str(int(time.time()))
        email = f"user_zenodo_{ts}@example.com"
        password = "1234"

        signup_and_handle_2fa_enable(driver, host, email, password)

        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.ID, "title")))

        driver.find_element(By.ID, "title").send_keys("Ejemplo Fakenodo")
        driver.find_element(By.NAME, "desc").send_keys("Hola")

        dropdown = driver.find_element(By.ID, "publication_type")
        dropdown.click()
        dropdown.find_element(By.XPATH, "//option[normalize-space(.) = 'Working Paper']").click()

        file_input = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        file_path = os.path.join(
            os.getcwd(),
            "app",
            "modules",
            "dataset",
            "pix_examples",
            "file1.pix",
        )
        file_input.send_keys(file_path)

        WebDriverWait(driver, 15).until(lambda d: len(d.find_elements(By.CLASS_NAME, "dz-preview")) > 0)

        agree_checkbox = driver.find_element(By.ID, "agreeCheckbox")
        driver.execute_script("arguments[0].click();", agree_checkbox)

        upload_button = wait.until(EC.presence_of_element_located((By.ID, "upload_button")))
        driver.execute_script("arguments[0].scrollIntoView(true);", upload_button)
        driver.execute_script("arguments[0].click();", upload_button)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr:first-child a")))
        driver.find_element(By.CSS_SELECTOR, "tbody tr:first-child a").click()
        wait_for_page_to_load(driver)

        link = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/depositions/']")))
        href = link.get_attribute("href")
        deposition_id = href.rstrip("/").split("/depositions/")[-1].split("/")[0]
        assert deposition_id

        api_url = f"http://localhost:5001/api/depositions/{deposition_id}"
        driver.execute_script("window.open(arguments[0], '_blank');", api_url)

        WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])

        try:
            json_text = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "pre"))).text
        except Exception:
            json_text = driver.find_element(By.TAG_NAME, "body").text

        assert "Not Found" not in json_text
        assert "404" not in json_text

    finally:
        close_driver(driver)

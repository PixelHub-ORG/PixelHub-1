import time

import pyotp
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def test_login_and_check_element():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        wait = WebDriverWait(driver, 15)

        driver.get(f"{host}/signup/")
        wait.until(EC.presence_of_element_located((By.NAME, "name")))

        ts = str(int(time.time()))
        email = f"user_px2_{ts}@example.com"
        password = "1234"

        driver.find_element(By.NAME, "name").send_keys("User")
        driver.find_element(By.NAME, "surname").send_keys("PX2")
        driver.find_element(By.NAME, "email").send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        if "/2fa/enable" in driver.current_url:
            p = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "p.mb-3")))
            secret = p.text.split("Manual secret:")[-1].strip()
            code = pyotp.TOTP(secret).now()
            code_input = wait.until(
                EC.presence_of_element_located(
                    (By.NAME, "code")))
            code_input.clear()
            code_input.send_keys(code)
            driver.find_element(
                By.CSS_SELECTOR,
                "button[type='submit']").click()

        if "/2fa/verify" in driver.current_url:
            raise AssertionError(
                "Unexpected /2fa/verify without having the secret available in the test flow.")

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH,
                 "//h1[contains(@class, 'h2 mb-3') and contains(., 'Latest datasets')]")))
    finally:
        close_driver(driver)

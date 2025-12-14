import time
import re
import urllib.parse

import pyotp
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def wait_ready(driver, timeout=20):
    WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")


def accept_alert_if_any(driver, timeout=3):
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        Alert(driver).accept()
        return True
    except Exception:
        return False


def wait_ready_safe(driver, timeout=20):
    end = time.time() + timeout
    last = None
    while time.time() < end:
        try:
            if accept_alert_if_any(driver, 1):
                continue
            if driver.execute_script("return document.readyState") == "complete":
                return
        except Exception as e:
            last = e
            accept_alert_if_any(driver, 1)
        time.sleep(0.2)
    if last:
        raise last


def extract_secret(driver):
    text = driver.find_element(By.TAG_NAME, "body").text or ""
    m = re.search(r"\b[A-Z2-7]{16,}\b", text.replace(" ", ""))
    if not m:
        raise AssertionError(f"2FA secret not found. url={driver.current_url}")
    return m.group(0)


def signup_enable_2fa(driver, host):
    ts = str(int(time.time()))
    email = f"user_cart_{ts}@example.com"
    password = "1234"

    driver.get(f"{host}/signup/")
    wait_ready_safe(driver)

    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "name"))).send_keys("Cart")
    driver.find_element(By.NAME, "surname").send_keys("Selenium")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

    WebDriverWait(driver, 20).until(lambda d: "/2fa/enable" in d.current_url or d.current_url.startswith(host))

    if "/2fa/enable" not in driver.current_url:
        driver.get(f"{host}/2fa/enable")
        wait_ready_safe(driver)
        WebDriverWait(driver, 20).until(lambda d: "/2fa/enable" in d.current_url)

    secret = extract_secret(driver)
    code = pyotp.TOTP(secret).now()

    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "code"))).send_keys(code)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit'],input[type='submit']").click()

    WebDriverWait(driver, 20).until(lambda d: "/2fa/enable" not in d.current_url)
    wait_ready_safe(driver)

    driver.get(f"{host}/logout")
    wait_ready_safe(driver)
    return email, password, secret


def login_with_2fa_to_next(driver, host, email, password, secret, next_path):
    next_q = urllib.parse.quote(next_path, safe="")
    driver.get(f"{host}/login?next={next_q}")
    wait_ready_safe(driver)

    email_inputs = driver.find_elements(By.NAME, "email") or driver.find_elements(By.ID, "email")
    pass_inputs = driver.find_elements(By.NAME, "password") or driver.find_elements(By.ID, "password")
    if not email_inputs or not pass_inputs:
        raise AssertionError(f"Login inputs not found. url={driver.current_url}")

    email_inputs[0].send_keys(email)
    pass_inputs[0].send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit'],input[type='submit']").click()

    WebDriverWait(driver, 20).until(lambda d: "/2fa/verify" in d.current_url or "/login" not in d.current_url)
    wait_ready_safe(driver)

    if "/2fa/verify" in driver.current_url:
        code = pyotp.TOTP(secret).now()
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "code"))).send_keys(code)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit'],input[type='submit']").click()
        WebDriverWait(driver, 20).until(lambda d: "/2fa/verify" not in d.current_url)
        wait_ready_safe(driver)

    if "/login" in driver.current_url:
        raise AssertionError(f"Login did not stick. url={driver.current_url}")

    if next_path not in driver.current_url:
        driver.get(f"{host}{next_path}")
        wait_ready_safe(driver)
        if "/login" in driver.current_url:
            raise AssertionError(f"Still not authenticated. url={driver.current_url}")


def login_with_2fa(driver, host, email, password, secret):
    login_with_2fa_to_next(driver, host, email, password, secret, "/")


class TestCreateDataset:
    def setup_method(self, method):
        self.driver = initialize_driver()
        self.vars = {}

    def teardown_method(self, method):
        close_driver(self.driver)

    def test_createDataset(self):
        host = get_host_for_selenium_testing()
        email, password, secret = signup_enable_2fa(self.driver, host)
        login_with_2fa(self.driver, host, email, password, secret)

        self.driver.get(f"{host}/")
        wait_ready_safe(self.driver)

        WebDriverWait(self.driver, 20).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, 'a[href*="/doi/"]')) > 0)
        self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/doi/"]')[0].click()
        wait_ready_safe(self.driver)

        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[test='add-to-car-mclaren']"))).click()
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".feather-shopping-cart"))).click()
        wait_ready_safe(self.driver)

        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, "create-dataset-btn"))).click()
        wait_ready_safe(self.driver)

        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, "title"))).send_keys("Example3")
        self.driver.find_element(By.ID, "desc").send_keys("Example3")

        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-outline-danger"))).click()
        accept_alert_if_any(self.driver, 5)
        wait_ready_safe(self.driver)

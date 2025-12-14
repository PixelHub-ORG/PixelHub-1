import os
import re
import time
import urllib.parse

import pyotp
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver

_STATE = {"email": None, "password": None, "secret": None}


def wait_ready(driver, timeout=20):
    WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")


def extract_secret(driver):
    text = driver.find_element(By.TAG_NAME, "body").text or ""
    m = re.search(r"\b[A-Z2-7]{16,}\b", text.replace(" ", ""))
    if not m:
        raise AssertionError(f"2FA secret not found. url={safe_current_url(driver)}")
    return m.group(0)


def safe_current_url(driver):
    try:
        return driver.current_url
    except Exception:
        return ""


def safe_handles(driver):
    try:
        return driver.window_handles
    except Exception:
        return []


def safe_switch_to_any_window(driver):
    hs = safe_handles(driver)
    if not hs:
        return False
    try:
        driver.switch_to.window(hs[0])
        return True
    except Exception:
        return False


def signup_enable_2fa(driver, host):
    if _STATE["email"]:
        return _STATE["email"], _STATE["password"], _STATE["secret"]

    wait = WebDriverWait(driver, 20)
    ts = str(int(time.time()))
    email = f"user_ds_px2_{ts}@example.com"
    password = "1234"

    driver.get(f"{host}/signup/")
    wait.until(EC.presence_of_element_located((By.NAME, "name")))
    driver.find_element(By.NAME, "name").send_keys("Dataset")
    driver.find_element(By.NAME, "surname").send_keys("PX2")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

    wait.until(lambda d: "/2fa/enable" in safe_current_url(d) or safe_current_url(d).startswith(host))

    if "/2fa/enable" not in safe_current_url(driver):
        driver.get(f"{host}/2fa/enable")
        wait_ready(driver)
        wait.until(lambda d: "/2fa/enable" in safe_current_url(d) or safe_current_url(d).startswith(host))

    if "/2fa/enable" not in safe_current_url(driver):
        raise AssertionError(f"Could not reach /2fa/enable after signup. url={safe_current_url(driver)}")

    secret = extract_secret(driver)
    code = pyotp.TOTP(secret).now()

    code_inputs = (
        driver.find_elements(By.NAME, "code")
        or driver.find_elements(By.NAME, "token")
        or driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='tel'], input[type='number']")
    )
    if not code_inputs:
        raise AssertionError(f"2FA code input not found. url={safe_current_url(driver)}")
    try:
        code_inputs[0].clear()
    except Exception:
        pass
    code_inputs[0].send_keys(code)

    submit_btns = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']") or driver.find_elements(
        By.CSS_SELECTOR, "input[type='submit']"
    )
    if not submit_btns:
        raise AssertionError(f"2FA enable submit button not found. url={safe_current_url(driver)}")
    submit_btns[0].click()

    wait.until(lambda d: "/2fa/enable" not in safe_current_url(d))
    wait_ready(driver)

    _STATE["email"] = email
    _STATE["password"] = password
    _STATE["secret"] = secret

    driver.get(f"{host}/logout")
    wait_ready(driver)
    return email, password, secret


def login_with_2fa_to_next(driver, host, email, password, secret, next_path):
    wait = WebDriverWait(driver, 20)
    next_q = urllib.parse.quote(next_path, safe="")
    driver.get(f"{host}/login?next={next_q}")
    wait_ready(driver)

    email_inputs = (
        driver.find_elements(By.NAME, "email")
        or driver.find_elements(By.ID, "email")
        or driver.find_elements(By.CSS_SELECTOR, "input[type='email']")
    )
    pass_inputs = (
        driver.find_elements(By.NAME, "password")
        or driver.find_elements(By.ID, "password")
        or driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
    )
    if not email_inputs or not pass_inputs:
        raise AssertionError(f"Login inputs not found. url={safe_current_url(driver)}")

    try:
        email_inputs[0].clear()
    except Exception:
        pass
    email_inputs[0].send_keys(email)
    try:
        pass_inputs[0].clear()
    except Exception:
        pass
    pass_inputs[0].send_keys(password)

    submit = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']") or driver.find_elements(
        By.CSS_SELECTOR, "input[type='submit']"
    )
    if submit:
        submit[0].click()
    else:
        pass_inputs[0].send_keys(Keys.RETURN)

    wait.until(
        lambda d: "/2fa/verify" in safe_current_url(d)
        or "/login" in safe_current_url(d)
        or safe_current_url(d).startswith(host)
    )
    wait_ready(driver)

    if "/2fa/verify" in safe_current_url(driver):
        code = pyotp.TOTP(secret).now()
        code_inputs = (
            driver.find_elements(By.NAME, "code")
            or driver.find_elements(By.NAME, "token")
            or driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='tel'], input[type='number']")
        )
        if not code_inputs:
            raise AssertionError(f"2FA verify code input not found. url={safe_current_url(driver)}")
        try:
            code_inputs[0].clear()
        except Exception:
            pass
        code_inputs[0].send_keys(code)

        submit2 = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']") or driver.find_elements(
            By.CSS_SELECTOR, "input[type='submit']"
        )
        if not submit2:
            raise AssertionError(f"2FA verify submit button not found. url={safe_current_url(driver)}")
        submit2[0].click()

        wait.until(lambda d: "/2fa/verify" not in safe_current_url(d))
        wait_ready(driver)

    if "/login" in safe_current_url(driver):
        raise AssertionError(f"Login did not stick (still on login). url={safe_current_url(driver)}")

    if next_path not in safe_current_url(driver):
        driver.get(f"{host}{next_path}")
        wait_ready(driver)
        if "/login" in safe_current_url(driver):
            raise AssertionError(f"Still not authenticated after login+2FA. url={safe_current_url(driver)}")


def count_datasets(driver, host):
    driver.get(f"{host}/dataset/list")
    wait_ready(driver)
    return len(driver.find_elements(By.XPATH, "//table//tbody//tr"))


def pix_file_paths():
    base = os.path.dirname(os.path.dirname(__file__))
    pix_dir = os.path.join(base, "pix_examples")
    f1 = os.path.abspath(os.path.join(pix_dir, "file1.pix"))
    f2 = os.path.abspath(os.path.join(pix_dir, "file2.pix"))
    assert os.path.exists(f1)
    assert os.path.exists(f2)
    return f1, f2


def zip_file_path():
    base = os.path.dirname(os.path.dirname(__file__))
    z = os.path.abspath(os.path.join(base, "pix_examples", "files1.zip"))
    assert os.path.exists(z)
    return z


def find_title_input(driver):
    wait = WebDriverWait(driver, 20)
    locs = [
        (By.ID, "title"),
        (By.NAME, "title"),
        (By.CSS_SELECTOR, "input[id*='title'], input[name*='title']"),
        (By.XPATH, "//label[contains(translate(normalize-space(.),'TITLE','title'),'title')]/following::input[1]"),
    ]
    last = None
    for by, sel in locs:
        try:
            return wait.until(EC.presence_of_element_located((by, sel)))
        except Exception as e:
            last = e
    raise last


def fill(driver, locs, value):
    wait = WebDriverWait(driver, 20)
    last = None
    for by, sel in locs:
        try:
            el = wait.until(EC.presence_of_element_located((by, sel)))
            try:
                el.clear()
            except Exception:
                pass
            el.send_keys(value)
            return
        except Exception as e:
            last = e
    raise last


def try_click_agree(driver):
    els = driver.find_elements(By.ID, "agreeCheckbox")
    if els:
        try:
            els[0].click()
        except Exception:
            driver.execute_script("arguments[0].click();", els[0])


def click_upload(driver):
    wait = WebDriverWait(driver, 20)
    btn = wait.until(EC.presence_of_element_located((By.ID, "upload_button")))
    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
    try:
        btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", btn)
    time.sleep(2)
    try:
        wait_ready(driver)
    except Exception:
        pass


def open_upload(driver, host, email, password, secret):
    login_with_2fa_to_next(driver, host, email, password, secret, "/dataset/upload")
    if "/dataset/upload" not in safe_current_url(driver):
        driver.get(f"{host}/dataset/upload")
        wait_ready(driver)
    if "/login" in safe_current_url(driver):
        raise AssertionError(f"Not authenticated to access upload. url={safe_current_url(driver)}")
    find_title_input(driver)


def wait_for_list_or_rows_without_current_url(driver, timeout=75):
    end = time.time() + timeout
    last = None
    while time.time() < end:
        try:
            if not safe_handles(driver):
                time.sleep(0.2)
                continue
            safe_switch_to_any_window(driver)
            rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
            if rows:
                return True
            if driver.find_elements(
                By.XPATH,
                "//*[contains(translate(.,'SUCCESS','success'),'success') or contains(translate(.,'UPLOADED','uploaded'),'uploaded') or contains(translate(.,'CREATED','created'),'created')]",
            ):
                return True
        except Exception as e:
            last = e
        time.sleep(0.5)
    if last:
        raise last
    return False


def test_upload_dataset():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        email, password, secret = signup_enable_2fa(driver, host)

        before = count_datasets(driver, host)

        open_upload(driver, host, email, password, secret)

        title = f"Test dataset {int(time.time())}"
        find_title_input(driver).send_keys(title)

        fill(
            driver,
            [
                (By.NAME, "desc"),
                (By.ID, "desc"),
                (By.NAME, "description"),
                (By.ID, "description"),
                (By.TAG_NAME, "textarea"),
            ],
            "Description for selenium upload test",
        )
        fill(driver, [(By.NAME, "tags"), (By.ID, "tags")], "tag1,tag2")

        f1, f2 = pix_file_paths()
        file_inputs = driver.find_elements(By.CLASS_NAME, "dz-hidden-input") or driver.find_elements(
            By.CSS_SELECTOR, "input[type='file']"
        )
        assert file_inputs
        file_inputs[0].send_keys(f1)
        WebDriverWait(driver, 15).until(lambda d: len(d.find_elements(By.CLASS_NAME, "dz-preview")) > 0)
        file_inputs = driver.find_elements(By.CLASS_NAME, "dz-hidden-input") or driver.find_elements(
            By.CSS_SELECTOR, "input[type='file']"
        )
        file_inputs[0].send_keys(f2)

        try_click_agree(driver)
        click_upload(driver)

        expected = before + 1
        for _ in range(15):
            if count_datasets(driver, host) == expected:
                break
            time.sleep(1)
        assert count_datasets(driver, host) == expected
    finally:
        close_driver(driver)


def test_upload_dataset_from_github():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        email, password, secret = signup_enable_2fa(driver, host)

        before = count_datasets(driver, host)

        open_upload(driver, host, email, password, secret)

        title = f"Test dataset GitHub {int(time.time())}"
        find_title_input(driver).send_keys(title)

        fill(
            driver,
            [
                (By.NAME, "desc"),
                (By.ID, "desc"),
                (By.NAME, "description"),
                (By.ID, "description"),
                (By.TAG_NAME, "textarea"),
            ],
            "Description for selenium upload test from GitHub",
        )
        fill(driver, [(By.NAME, "tags"), (By.ID, "tags")], "tag1,tag2,github")

        fill(
            driver,
            [(By.ID, "github-repo"), (By.ID, "github_repo"), (By.NAME, "github-repo"), (By.NAME, "github_repo")],
            "https://github.com/JoseLu2121/pix_files.git",
        )
        fill(
            driver,
            [(By.ID, "github-path"), (By.ID, "github_path"), (By.NAME, "github-path"), (By.NAME, "github_path")],
            "files/",
        )

        btns = driver.find_elements(By.ID, "github-add-btn") or driver.find_elements(By.ID, "github_add_btn")
        assert btns
        try:
            btns[0].click()
        except Exception:
            driver.execute_script("arguments[0].click();", btns[0])

        WebDriverWait(driver, 60).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#file-list li")) > 0)

        try_click_agree(driver)
        click_upload(driver)

        assert wait_for_list_or_rows_without_current_url(driver, 75)
        assert count_datasets(driver, host) >= before + 1
    finally:
        close_driver(driver)


def test_upload_dataset_from_zip():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        email, password, secret = signup_enable_2fa(driver, host)

        before = count_datasets(driver, host)

        open_upload(driver, host, email, password, secret)

        title = f"Test dataset ZIP {int(time.time())}"
        find_title_input(driver).send_keys(title)

        fill(
            driver,
            [
                (By.NAME, "desc"),
                (By.ID, "desc"),
                (By.NAME, "description"),
                (By.ID, "description"),
                (By.TAG_NAME, "textarea"),
            ],
            "Dataset from zip upload test",
        )
        fill(driver, [(By.NAME, "tags"), (By.ID, "tags")], "tag1,tag2,zip")

        zp = zip_file_path()
        file_inputs = driver.find_elements(By.CLASS_NAME, "dz-hidden-input") or driver.find_elements(
            By.CSS_SELECTOR, "input[type='file']"
        )
        assert file_inputs
        file_inputs[0].send_keys(zp)

        try_click_agree(driver)
        click_upload(driver)

        assert wait_for_list_or_rows_without_current_url(driver, 75)
        assert count_datasets(driver, host) >= before + 1
    finally:
        close_driver(driver)

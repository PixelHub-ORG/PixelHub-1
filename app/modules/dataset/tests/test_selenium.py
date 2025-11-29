import os
import time

from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def wait_for_page_to_load(driver, timeout=6):
    WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")


def count_datasets(driver, host):
    driver.get(f"{host}/dataset/list")
    wait_for_page_to_load(driver)
    rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
    return len(rows)


def click_agree_checkbox_if_present(driver):
    try:
        check = driver.find_element(By.ID, "agreeCheckbox")
        try:
            check.click()
        except ElementNotInteractableException:
            driver.execute_script("arguments[0].click();", check)
        wait_for_page_to_load(driver)
    except NoSuchElementException:
        pass


def click_upload_button(driver):
    upload_btn = driver.find_element(By.ID, "upload_button")
    try:
        upload_btn.click()
    except ElementNotInteractableException:
        driver.execute_script("arguments[0].click();", upload_btn)
    wait_for_page_to_load(driver)
    time.sleep(2)


def get_pix_file_paths():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    pix_dir = os.path.join(base_dir, "pix_examples")
    file1_path = os.path.abspath(os.path.join(pix_dir, "file1.pix"))
    file2_path = os.path.abspath(os.path.join(pix_dir, "file2.pix"))
    assert os.path.exists(file1_path)
    assert os.path.exists(file2_path)
    return file1_path, file2_path


def login_as_user1(driver, host):
    driver.get(f"{host}/login")
    wait_for_page_to_load(driver)
    email_field = driver.find_element(By.NAME, "email")
    password_field = driver.find_element(By.NAME, "password")
    email_field.clear()
    password_field.clear()
    email_field.send_keys("user1@example.com")
    password_field.send_keys("1234")
    password_field.send_keys(Keys.RETURN)
    time.sleep(4)
    wait_for_page_to_load(driver)


def open_latest_dataset_view(driver, host):
    driver.get(f"{host}/dataset/list")
    wait_for_page_to_load(driver)
    rows = driver.find_elements(By.XPATH, "(//table)[1]//tbody//tr")
    assert rows
    latest_row = rows[0]
    title_link = latest_row.find_element(By.XPATH, ".//td[1]/a")
    title_link.click()
    wait_for_page_to_load(driver)
    time.sleep(2)


def test_upload_dataset():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        login_as_user1(driver, host)

        initial_datasets = count_datasets(driver, host)

        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        unique_title = f"Test dataset {int(time.time())}"

        driver.find_element(By.NAME, "title").send_keys(unique_title)
        driver.find_element(By.NAME, "desc").send_keys("Description for selenium upload test")
        driver.find_element(By.NAME, "tags").send_keys("tag1,tag2")

        add_author_button = driver.find_element(By.ID, "add_author")
        add_author_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)
        add_author_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        driver.find_element(By.NAME, "authors-0-name").send_keys("Author0")
        driver.find_element(By.NAME, "authors-0-affiliation").send_keys("Club0")
        driver.find_element(By.NAME, "authors-0-orcid").send_keys("0000-0000-0000-0000")

        driver.find_element(By.NAME, "authors-1-name").send_keys("Author1")
        driver.find_element(By.NAME, "authors-1-affiliation").send_keys("Club1")

        file1_path, file2_path = get_pix_file_paths()

        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file1_path)
        wait_for_page_to_load(driver)

        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file2_path)
        wait_for_page_to_load(driver)

        click_agree_checkbox_if_present(driver)
        click_upload_button(driver)

        expected = initial_datasets + 1
        final_datasets = count_datasets(driver, host)

        for _ in range(5):
            if final_datasets == expected:
                break
            time.sleep(1)
            final_datasets = count_datasets(driver, host)

        assert final_datasets == expected

        driver.get(f"{host}/dataset/list")
        wait_for_page_to_load(driver)
        links = driver.find_elements(
            By.XPATH,
            f"//table[1]//tbody//tr//td[1]//a[normalize-space(text())='{unique_title}']",
        )
        assert links

    finally:
        close_driver(driver)


def test_dataset_versioning_and_comparison_flow():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        login_as_user1(driver, host)

        initial_count = count_datasets(driver, host)

        open_latest_dataset_view(driver, host)

        create_version_button = driver.find_element(By.LINK_TEXT, "Create new version")
        create_version_button.click()
        wait_for_page_to_load(driver)
        time.sleep(2)

        assert "/dataset/" in driver.current_url and "create_version" in driver.current_url

        desc_field = driver.find_element(By.NAME, "desc")
        tags_field = driver.find_element(By.NAME, "tags")

        desc_field.clear()
        desc_field.send_keys("Updated description for selenium version")

        tags_field.clear()
        tags_field.send_keys("tag1,tag2,selenium-version")

        file1_path, file2_path = get_pix_file_paths()
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file1_path)
        wait_for_page_to_load(driver)

        click_agree_checkbox_if_present(driver)
        click_upload_button(driver)

        expected_after_version = initial_count + 1
        final_count = count_datasets(driver, host)

        for _ in range(5):
            if final_count == expected_after_version:
                break
            time.sleep(1)
            final_count = count_datasets(driver, host)

        assert final_count == expected_after_version

        open_latest_dataset_view(driver, host)

        version_history_header = driver.find_element(By.XPATH, "//h5[contains(., 'Version History')]")
        assert version_history_header.is_displayed()

        badges = driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'timeline-item')]//span[contains(@class,'badge') and contains(., 'v')]",
        )
        versions_text = [b.text.strip() for b in badges]

        assert any("v1" in v for v in versions_text)
        assert len(versions_text) >= 2

        diff_link = driver.find_element(
            By.XPATH,
            "//div[contains(@class,'timeline-item')]//a[@title='Compare with current view']",
        )
        diff_link.click()
        wait_for_page_to_load(driver)
        time.sleep(2)

        assert "/dataset/compare/" in driver.current_url

        heading = driver.find_element(By.XPATH, "//h1[contains(., 'Comparison Report')]")
        assert heading.is_displayed()

        assert driver.find_element(By.ID, "mod-tab").is_displayed()
        assert driver.find_element(By.ID, "add-tab").is_displayed()
        assert driver.find_element(By.ID, "del-tab").is_displayed()

    finally:
        close_driver(driver)

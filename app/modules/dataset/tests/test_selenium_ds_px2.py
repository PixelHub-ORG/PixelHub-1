import os
import time

from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
)
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


def get_zip_file_path():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    zip_dir = os.path.join(base_dir, "pix_examples")
    zip_path = os.path.abspath(os.path.join(zip_dir, "files1.zip"))
    assert os.path.exists(zip_path)
    return zip_path


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


def test_upload_dataset_from_github():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        login_as_user1(driver, host)

        initial_datasets = count_datasets(driver, host)

        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        unique_title = f"Test dataset GitHub {int(time.time())}"

        driver.find_element(By.NAME, "title").send_keys(unique_title)
        driver.find_element(By.NAME, "desc").send_keys("Description for selenium upload test from GitHub")
        driver.find_element(By.NAME, "tags").send_keys("tag1,tag2,github")

        # Fill GitHub info
        repo_input = driver.find_element(By.ID, "github-repo")
        repo_input.clear()
        repo_input.send_keys("https://github.com/JoseLu2121/pix_files.git")

        path_input = driver.find_element(By.ID, "github-path")
        path_input.clear()
        path_input.send_keys("files/")

        add_btn = driver.find_element(By.ID, "github-add-btn")
        add_btn.click()

        # Wait for files to be processed and listed
        # The JS adds elements to 'file-list'
        # We can wait for at least one list item in file-list
        WebDriverWait(driver, 30).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#file-list li")) > 0)

        # Check if file1.pix or file2.pix is present
        file_list = driver.find_element(By.ID, "file-list")
        file_list_text = file_list.text
        # Check for presence of base filenames, ignoring potential numeric suffixes added by the system
        assert "file_github_path1" in file_list_text or "file_github_path2" in file_list_text

        click_agree_checkbox_if_present(driver)
        click_upload_button(driver)

        expected = initial_datasets + 1
        final_datasets = count_datasets(driver, host)

        for _ in range(10):  # Increased wait time as GitHub fetch might take time
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


def test_upload_dataset_from_zip():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        login_as_user1(driver, host)

        initial_datasets = count_datasets(driver, host)

        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        unique_title = f"Test dataset {int(time.time())}"

        driver.find_element(By.NAME, "title").send_keys(unique_title)
        driver.find_element(By.NAME, "desc").send_keys("Dataset from zip upload test")
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

        zip_path = get_zip_file_path()

        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(zip_path)
        wait_for_page_to_load(driver)

        agree_checkbox = driver.find_element(By.ID, "agreeCheckbox")
        driver.execute_script("arguments[0].click();", agree_checkbox)

        # Esperar a que el botón de subida exista
        upload_button = WebDriverWait(driver, 10).until(lambda d: d.find_element(By.ID, "upload_button"))

        # Asegurar visibilidad
        driver.execute_script("arguments[0].scrollIntoView(true);", upload_button)
        time.sleep(1)

        # Hacer click con JS
        driver.execute_script("arguments[0].click();", upload_button)
        time.sleep(5)
        wait_for_page_to_load(driver)

        expected = initial_datasets + 1
        final_datasets = count_datasets(driver, host)

        for _ in range(5):
            if final_datasets == expected:
                break
            time.sleep(5)
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

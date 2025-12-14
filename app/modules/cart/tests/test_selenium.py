# app/modules/cart/tests/test_selenium.py

import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def login_user(driver, host):
    driver.get(f"{host}/login")
    email_field = driver.find_element(By.NAME, "email")
    password_field = driver.find_element(By.NAME, "password")
    email_field.send_keys("user1@example.com")
    password_field.send_keys("1234")
    password_field.send_keys(Keys.RETURN)
    time.sleep(2)


def clean_cart(driver, host):
    """Vacía el carrito usando JS para asegurar un estado limpio al inicio."""
    driver.get(f"{host}/user/cart/view_page")
    time.sleep(1)
    driver.execute_script(
        """
        fetch("/user/cart/delete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ item_id: null })
        });
    """
    )
    time.sleep(1)


def test_cart_is_empty():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        login_user(driver, host)
        clean_cart(driver, host)

        driver.get(f"{host}/user/cart/view_page")
        time.sleep(1)

        empty_message = driver.find_element(By.TAG_NAME, "h1")
        assert "Your cart is empty" in empty_message.text
        print("✅ Test 1: Carrito vacío verificado.")

    finally:
        close_driver(driver)


def test_cart_manual_add_and_download():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        login_user(driver, host)
        clean_cart(driver, host)

        driver.get(f"{host}/dataset/list")
        time.sleep(2)

        first_dataset_link = driver.find_element(By.XPATH, "//table//tbody//tr[1]//td[1]//a")
        first_dataset_link.click()
        time.sleep(2)

        add_button = driver.find_element(By.XPATH, "//button[contains(@onclick, 'addCart')]")
        add_button.click()

        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            time.sleep(1)
        except TimeoutException:
            print("⚠️ No apareció alerta, continuando...")

        driver.get(f"{host}/user/cart/view_page")
        time.sleep(2)

        download_btn = driver.find_element(By.XPATH, "//a[contains(@href, '/user/cart/download')]")
        assert download_btn is not None, "El botón de descarga no está"

        download_btn.click()
        time.sleep(3)

        # 7. Verificar que no hay errores en pantalla
        assert "404" not in driver.page_source
        assert "Internal Server Error" not in driver.page_source

        print("✅ Test 2: Flujo completo (Añadir manual -> Descargar) exitoso.")

    finally:
        close_driver(driver)

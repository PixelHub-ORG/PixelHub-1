# app/modules/cart/tests/test_selenium.py
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def setup_method(self, method):
    self.driver = webdriver.Firefox()
    self.vars = {}


def teardown_method(self, method):
    self.driver.quit()


def test_createDataset(self):
    self.driver.get("http://127.0.0.1:5000/")
    self.driver.set_window_size(1083, 787)
    self.driver.find_element(By.LINK_TEXT, "Login").click()
    self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
    self.driver.find_element(By.ID, "password").send_keys("1234")
    self.driver.find_element(By.ID, "submit").click()
    self.driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
    assert self.driver.switch_to.alert.text == "Item added to cart."
    self.driver.find_element(By.ID, "add-to-cart-67").click()
    assert self.driver.switch_to.alert.text == "Item added to cart."
    self.driver.find_element(By.CSS_SELECTOR, ".feather-shopping-cart").click()
    self.driver.find_element(By.ID, "create-dataset-btn").click()
    self.driver.find_element(By.ID, "title").click()
    self.driver.find_element(By.ID, "title").send_keys("Example3")
    self.driver.find_element(By.ID, "desc").click()
    self.driver.find_element(By.ID, "desc").send_keys("Example3")


def test_download_cart_button():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()

        # 1. Login (Usamos el usuario creado por los seeders)
        driver.get(f"{host}/login")
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")
        password_field.send_keys(Keys.RETURN)

        # Esperar a que el login complete
        time.sleep(2)

        # 2. Asegurarnos de tener algo en el carro (Truco: Añadimos via API oculta o JS para el test)
        # Ojo: Asumimos que el usuario ya tiene items o los añadimos.
        # Para asegurar que el test no falle si el carro está vacío, vamos a añadir uno rápido con JS
        driver.execute_script(
            """
            fetch("/featuremodel/cart/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ item_id: 1 })
            });
        """
        )
        time.sleep(1)

        # 3. Ir a la página del carrito
        driver.get(f"{host}/user/cart/view_page")
        time.sleep(2)

        # 4. Verificar que el botón de descarga existe
        # Buscamos por el texto que pusimos en el HTML o por el enlace
        download_btn = driver.find_element(By.XPATH, "//a[contains(@href, '/user/cart/download')]")

        assert download_btn is not None
        assert "Download models" in download_btn.text

        print("✅ Test Selenium: El botón de descarga del carrito aparece correctamente.")

    finally:
        close_driver(driver)

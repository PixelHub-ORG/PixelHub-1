# app/modules/cart/tests/test_selenium.py
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


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

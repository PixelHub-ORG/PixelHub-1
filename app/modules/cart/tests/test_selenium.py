import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def test_cart_is_empty():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()

        driver.get(f"{host}/login")
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")
        password_field.send_keys(Keys.RETURN)

        time.sleep(2)

        driver.get(f"{host}/user/cart/view_page")
        time.sleep(2)

        empty_message = driver.find_element(By.TAG_NAME, "h1")

        assert empty_message is not None
        assert "Your cart is empty" in empty_message.text

        print("Test Selenium: El mensaje 'Your cart is empty.' aparece correctamente.")

    finally:
        close_driver(driver)
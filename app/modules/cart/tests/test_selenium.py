import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.selenium.common import close_driver, initialize_driver


def wait_for_page_to_load(driver, timeout=4):
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )

def test_cart_workflow_selenium():
    driver = initialize_driver()
    try:
        driver.get("http://localhost:5000/login")
        driver.find_element(By.NAME, "email").send_keys("user1@example.com")
        driver.find_element(By.NAME, "password").send_keys("1234")
        driver.find_element(By.ID, "submit").click()
        
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "navbarDropdownMenuLink")))

        driver.get("http://localhost:5000/explore")
        
        add_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "add-to-cart-1"))
        )
        add_btn.click()
        
        time.sleep(1) 

        driver.get("http://localhost:5000/user/cart/view_page")
        
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        assert len(rows) > 0, "El carrito debería tener items"

        create_btn = driver.find_element(By.ID, "create-dataset-btn") #
        create_btn.click()

        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "title")))
        driver.find_element(By.NAME, "title").send_keys("Selenium Dataset")
        driver.find_element(By.ID, "submit").click()

        success_alert = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )
        assert "created" in success_alert.text

    finally:
        close_driver(driver)
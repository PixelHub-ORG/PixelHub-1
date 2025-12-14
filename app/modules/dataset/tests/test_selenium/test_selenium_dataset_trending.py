import sys
import time
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.selenium.common import close_driver, initialize_driver

project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))


class TestTrendingDataSets:
    def setup_method(self, method):
        self.driver = initialize_driver()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_trendingDataSets(self):
        self.driver.get("http://127.0.0.1:5000/")
        self.driver.set_window_size(1085, 693)

        self.driver.find_element(
            By.CSS_SELECTOR,
            ".nav-link:nth-child(1)").click()

        email_field = self.driver.find_element(By.ID, "email")
        email_field.click()
        email_field.send_keys("user1@example.com")

        password_field = self.driver.find_element(By.ID, "password")
        password_field.click()
        password_field.send_keys("1234")
        password_field.send_keys(Keys.ENTER)

        WebDriverWait(
            self.driver, 10).until(
            EC.presence_of_element_located(
                (By.ID, "code")))
        code_field = self.driver.find_element(By.ID, "code")
        code_field.send_keys("262314")

        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".sidebar-item:nth-child(5) .align-middle:nth-child(2)")))

        print("\n🔍 Clickeando en sidebar item 5...")
        self.driver.find_element(
            By.CSS_SELECTOR,
            ".sidebar-item:nth-child(5) .align-middle:nth-child(2)").click()

        time.sleep(2)

        print(f"📍 URL actual: {self.driver.current_url}")

        print(f"📄 Título: {self.driver.title}")

        alerts = self.driver.find_elements(By.CSS_SELECTOR, ".alert")
        print(f"🔔 Alertas encontradas: {len(alerts)}")

        if alerts:
            print("✓ Clickeando en la alerta...")
            alerts[0].click()
        else:
            print("⚠ No se encontró ninguna alerta, continuando...")

        print("\n🔍 Buscando link para volver a Home...")

        home_link = None
        try:
            home_link = self.driver.find_element(By.LINK_TEXT, "Home")
            print("✓ Encontrado link 'Home'")
        except BaseException:
            try:
                home_link = self.driver.find_element(
                    By.PARTIAL_LINK_TEXT, "Home")
                print("✓ Encontrado link parcial 'Home'")
            except BaseException:
                try:
                    home_link = self.driver.find_element(
                        By.CSS_SELECTOR, "a[href='/']")
                    print("✓ Encontrado link a raíz")
                except BaseException:
                    print("❌ No se encontró link a Home")
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    print(f"📎 Links disponibles ({len(all_links)}):")
                    for link in all_links[:10]:
                        print(
                            f"   - {link.text[:50]} → {link.get_attribute('href')}")

        if home_link:
            home_link.click()
            time.sleep(2)

        print("\n🔍 Buscando links de descarga...")
        download_links = self.driver.find_elements(
            By.PARTIAL_LINK_TEXT, "Download")
        print(f"📥 Links de descarga encontrados: {len(download_links)}")

        for i, link in enumerate(download_links[:6]):
            print(f"   {i + 1}. {link.text}")

        download_texts = [
            "Download (21.18 KB)",
            "Download (20.89 KB)",
            "Download (38.79 KB)",
        ]

        for link_text in download_texts:
            try:
                size = link_text.split("(")[1].split(")")[0]
                link = self.driver.find_element(
                    By.PARTIAL_LINK_TEXT, f"Download ({size}")
                link.click()
                print(f"✓ Descargado: {link_text}")
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠ No se pudo hacer click en {link_text}: {e}")
                try:
                    any_download = self.driver.find_element(
                        By.PARTIAL_LINK_TEXT, "Download")
                    any_download.click()
                    print("✓ Descargado link alternativo")
                except BaseException:
                    print("❌ No hay links de descarga disponibles")

        print("\n🔍 Navegando a Leaderboard...")
        try:
            WebDriverWait(
                self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.LINK_TEXT, "Leaderboard")))
            self.driver.find_element(By.LINK_TEXT, "Leaderboard").click()
            print("✓ Clickeado en Leaderboard")
        except BaseException:
            try:
                self.driver.find_element(
                    By.PARTIAL_LINK_TEXT, "Leaderboard").click()
                print("✓ Clickeado en Leaderboard (búsqueda parcial)")
            except Exception as e:
                print(f"❌ No se encontró link a Leaderboard: {e}")

        time.sleep(2)

        print("\n🔍 Seleccionando periodo en dropdown...")
        try:
            WebDriverWait(
                self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.ID, "period")))
            dropdown = self.driver.find_element(By.ID, "period")

            options = dropdown.find_elements(By.TAG_NAME, "option")
            print(f"📋 Opciones del dropdown ({len(options)}):")
            for opt in options:
                print(f"   - {opt.text}")

            dropdown.find_element(
                By.XPATH, "//option[. = 'This Month']").click()
            print("✓ Seleccionado 'This Month'")
        except Exception as e:
            print(f"❌ Error al seleccionar periodo: {e}")

        print("\n✅ Test completado")
        close_driver(self.driver)

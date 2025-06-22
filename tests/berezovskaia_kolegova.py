
import unittest
import time
from urllib.parse import urlencode

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

BASE_URL = "http://localhost:8000"


def build_url(balance=33000, reserved=2000, **extra):
    params = {"balance": balance, "reserved": reserved}
    params.update(extra)
    return f"{BASE_URL}/?{urlencode(params)}"


class TestTransferCore(unittest.TestCase):
    def setUp(self) -> None:
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        service = ChromeService(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(5)

    def tearDown(self) -> None:
        self.driver.quit()

    def fill_card_and_amount(self, card: str, amount: str):
        self.driver.find_element(By.CSS_SELECTOR, "input[name='card']").clear()
        self.driver.find_element(By.CSS_SELECTOR, "input[name='card']").send_keys(card)
        amt = self.driver.find_element(By.CSS_SELECTOR, "input[name='amount']")
        amt.clear()
        amt.send_keys(amount)

    def click_send(self):
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    def get_fee(self) -> str:
        return self.driver.find_element(By.CSS_SELECTOR, "#fee").text.replace(" ", "")

    def get_toast(self) -> str | None:
        try:
            return self.driver.find_element(By.CSS_SELECTOR, ".toast").text
        except Exception:
            return None

    def test_tc_001_commission_recalculation(self):
        self.driver.get(build_url(balance=20000, reserved=0))
        self.fill_card_and_amount("5559000000000000", "5000")
        self.assertTrue(self.get_fee().startswith("500"))

        self.click_send()
        time.sleep(1)
        self.assertIn("успешно", self.get_toast().lower())

        self.fill_card_and_amount("5559000000000000", "1000")
        self.assertTrue(self.get_fee().startswith("100"))

    def test_tc_002_success_message_amount_and_fee(self):
        self.driver.get(build_url(balance=20000, reserved=0))
        self.fill_card_and_amount("4111111111111111", "1000")
        self.click_send()
        time.sleep(1)
        toast = self.get_toast().lower().replace(" ", "")
        self.assertIn("1000", toast)
        self.assertIn("100", toast)

    def test_tc_003_usd_overdraft_validation(self):
        self.driver.get(build_url(balance=100, reserved=0, currency="USD"))
        try:
            self.driver.find_element(By.CSS_SELECTOR, "select[name='currency'] option[value='USD']").click()
        except Exception:
            pass

        self.fill_card_and_amount("4000123456789000", "3111")
        self.click_send()
        time.sleep(1)
        toast = self.get_toast().lower()
        self.assertIn("недостаточно средств", toast)

    def test_tc_004_commission_floor_small_amount(self):
        self.driver.get(build_url(balance=1000, reserved=0))
        self.fill_card_and_amount("1234567890901122", "99")
        self.assertTrue(self.get_fee().startswith("9"))

    def test_tc_005_card_number_length_validation(self):
        self.driver.get(build_url(balance=10000, reserved=0))

        for card, should_pass in [
            ("123456789012", False),
            ("123456789012345678", False),
            ("5559000000000000", True)
        ]:
            self.fill_card_and_amount(card, "1000")
            send_disabled = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").get_property("disabled")
            if should_pass:
                self.assertFalse(send_disabled, msg=f"Card {card} should be accepted")
            else:
                self.assertTrue(send_disabled, msg=f"Card {card} should be rejected")


if __name__ == "__main__":
    unittest.main(verbosity=2)
"""

with open('/mnt/data/unittest_transfer_core_v2.py', 'w', encoding='utf-8') as f:
    f.write(unittest_code)

"✅ Файл unittest_transfer_core_v2.py с TC-001…TC-005 (в формате unittest) успешно создан."

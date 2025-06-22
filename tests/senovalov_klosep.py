import unittest
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:8000/"


class TestTransferAdditional(unittest.TestCase):
    def setUp(self):
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        service = ChromeService(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(5)

    def tearDown(self):
        self.driver.quit()

    def get_text(self, selector: str) -> str:
        return self.driver.find_element(By.CSS_SELECTOR, selector).text

    def wait_error(self) -> str:
        return WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".error, .toast-error"))
        ).text.lower()

    def test_tc_006_invalid_balance_reserved_query(self):
        url = BASE_URL + "?balance=" + quote("330%1.4") + "&reserved=%21"
        self.driver.get(url)

        balance_text = self.get_text("#balance")
        reserve_text = self.get_text("#reserved")

        self.assertNotIn("%", balance_text)
        self.assertNotIn("!", reserve_text)
        self.assertTrue(balance_text.replace(" ", "").replace("₽", "").isdigit())
        self.assertTrue(reserve_text.replace(" ", "").replace("₽", "").isdigit())

    def test_tc_007_reserved_exceeds_balance(self):
        self.driver.get(f"{BASE_URL}?balance=33001&reserved=330014")
        try:
            msg = self.wait_error()
            self.assertIn("резерв", msg)
            self.assertIn("баланс", msg)
        except Exception:
            reserve = self.get_text("#reserved")
            balance = self.get_text("#balance")
            rv = int("".join(filter(str.isdigit, reserve)))
            bv = int("".join(filter(str.isdigit, balance)))
            self.assertLessEqual(rv, bv)

    def test_tc_008_euro_transfer_exceeds_balance(self):
        self.driver.get(f"{BASE_URL}?currency=EUR&balance=1000&reserved=0")
        try:
            self.driver.find_element(By.CSS_SELECTOR, "select[name='currency'] option[value='EUR']").click()
        except Exception:
            pass

        self.driver.find_element(By.CSS_SELECTOR, "input[name='card']").send_keys("4111111111111111")
        amt = self.driver.find_element(By.CSS_SELECTOR, "input[name='amount']")
        amt.clear()
        amt.send_keys("1500")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        msg = self.wait_error()
        self.assertIn("недостаточно средств", msg)

    def test_tc_009_balance_updates_after_rub_transfer(self):
        self.driver.get(f"{BASE_URL}?balance=30000&reserved=2000")

        self.driver.find_element(By.CSS_SELECTOR, "input[name='card']").send_keys("5559000000000000")
        amt = self.driver.find_element(By.CSS_SELECTOR, "input[name='amount']")
        amt.clear()
        amt.send_keys("1000")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        success = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".toast"))
        )
        self.assertIn("успешно", success.text.lower())

        new_balance_text = self.get_text("#balance")
        new_balance = int("".join(filter(str.isdigit, new_balance_text)))
        self.assertEqual(new_balance, 28900)

    def test_tc_010_amount_starts_with_zero(self):
        self.driver.get(f"{BASE_URL}?balance=33000&reserved=2000")

        self.driver.find_element(By.CSS_SELECTOR, "input[name='card']").send_keys("5559000000000000")
        amt = self.driver.find_element(By.CSS_SELECTOR, "input[name='amount']")
        amt.clear()
        amt.send_keys("0123")

        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        self.assertTrue(submit_btn.get_property("disabled"))

        err_text = self.wait_error()
        self.assertTrue("недопустимый формат" in err_text or "сумма" in err_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
"""

with open('/mnt/data/unittest_transfer_additional.py', 'w', encoding='utf-8') as f:
    f.write(unittest_additional_tests)

"✅ Файл unittest_transfer_additional.py с TC-006…TC-010 (в формате unittest) успешно создан."

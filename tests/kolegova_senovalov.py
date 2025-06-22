
import unittest
import time

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


BASE_URL = "http://localhost:8000"


class TestTransferCore(unittest.TestCase):
    # ---------- set-up / tear-down ---------- #
    def setUp(self) -> None:
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-infobars")

        service = ChromeService(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def tearDown(self) -> None:
        self.driver.quit()

    # ---------- служебные методы ---------- #
    def open_app(self, balance: int | float, reserved: int | float, **query):
        url = f"{BASE_URL}/?balance={balance}&reserved={reserved}"
        for k, v in query.items():
            url += f"&{k}={v}"
        self.driver.get(url)

    def card_input(self, card_number: str) -> str:
        field = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input')
        field.clear()
        field.send_keys(card_number)
        return field.get_attribute("value").replace(" ", "")

    def amount_input(self, amount: str) -> str:
        field = self.driver.find_element(
            By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]'
        )
        field.clear()
        field.send_keys(amount)
        return field.get_attribute("value").replace(" ", "")

    def get_fee_value(self) -> str:
        fee_el = self.driver.find_element(By.XPATH, '//*[@id="fee"]')
        return fee_el.text.replace(" ", "")

    def click_send(self):
        btn = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/button')
        btn.click()

    def get_toast(self) -> str | None:
        try:
            toast = self.driver.find_element(By.XPATH, '//div[contains(@class,"toast")]')
            return toast.text
        except:
            return None

    # ---------- TC-011 ---------- #
    def test_exact_available_balance_transfer(self):
        """
        Баланс 1 100 ₽, перевод 1 000 ₽ + комиссия 100 ₽ = 0 ₽.
        Должно пройти успешно и обнулить баланс.
        """
        self.open_app(balance=1100, reserved=0)
        time.sleep(2)

        self.card_input("5559000000000000")
        self.amount_input("1000")
        initial_fee = self.get_fee_value()
        self.assertTrue(initial_fee.startswith("100"), "Комиссия не равна 100 ₽")

        self.click_send()
        time.sleep(2)

        toast = self.get_toast()
        self.assertIsNotNone(toast)
        self.assertIn("успешно", toast.lower())

        balance_el = self.driver.find_element(By.XPATH, '//*[@id="balance"]')
        self.assertIn(balance_el.text.replace(" ", ""), ("0₽", "0"))

    # ---------- TC-012 ---------- #
    def test_amount_with_comma(self):
        self.open_app(balance=10000, reserved=0)
        time.sleep(2)

        self.card_input("5559000000000000")
        self.amount_input("1234,56")
        fee = self.get_fee_value()
        self.assertTrue(fee.startswith("123"), "Комиссия должна быть 123 ₽")

        self.click_send()
        time.sleep(1)
        toast = self.get_toast()
        self.assertIn("успешно", toast.lower())

    # ---------- TC-013 ---------- #
    def test_amount_with_thousand_separator(self):
        self.open_app(balance=10000, reserved=0)
        time.sleep(2)

        self.card_input("5559000000000000")
        self.amount_input("1 000")            # ввод с пробелом
        amount_val = self.amount_input("1 000")
        self.assertEqual(amount_val, "1000", "Разделитель тысяч не убран")

        self.click_send()
        time.sleep(1)
        self.assertIn("успешно", self.get_toast().lower())

    # ---------- TC-014 ---------- #
    def test_amount_more_than_two_decimals(self):
        self.open_app(balance=10000, reserved=0)
        time.sleep(2)

        self.card_input("5559000000000000")
        self.amount_input("1234,567")         # 3 знака после запятой

        # должно появиться сообщение об ошибке и кнопка стать неактивной
        error_msg = self.driver.find_element(By.XPATH, '//*[@id="amountError"]').text
        self.assertIn("два знака", error_msg.lower())

        send_btn_disabled = self.driver.find_element(
            By.XPATH, '//*[@id="root"]/div/div/div[2]/button'
        ).get_attribute("disabled")
        self.assertTrue(send_btn_disabled)

    # ---------- TC-015 ---------- #
    def test_parallel_transfers(self):
        """
        Параллельный перевод из двух вкладок:
        1) 2 000 ₽ проходит.
        2) 3 000 ₽ во второй вкладке должен быть отклонён.
        """
        # первая вкладка
        self.open_app(balance=5000, reserved=0)
        time.sleep(2)
        self.card_input("5559000000000000")
        self.amount_input("2000")
        self.click_send()
        time.sleep(1)
        self.assertIn("успешно", self.get_toast().lower())

        # открываем вторую вкладку тем же водителем
        self.driver.execute_script('window.open("", "_blank");')
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.open_app(balance=5000, reserved=0)
        time.sleep(2)

        self.card_input("5559000000000000")
        self.amount_input("3000")
        self.click_send()
        time.sleep(1)
        toast = self.get_toast().lower()
        self.assertIn("недостаточно средств", toast)


if __name__ == "__main__":
    unittest.main(verbosity=2)

import unittest
import time

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


class TestCardInput(unittest.TestCase):
    def setUp(self) -> None:
        chrome_options = ChromeOptions()

        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--disable-infobars")

        service = ChromeService(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.get(url='http://localhost:8000/?balance=33000&reserved=2000')

    def enable_rubles(self):
        rubles_field = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[1]/div[1]/div')
        rubles_field.click()

    def card_input(self, card_number: str) -> str:
        input_field = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input')
        input_field.send_keys(card_number)
        value = input_field.get_attribute("value")
        return value.replace(" ", "")

    def amount_input(self, amount: str) -> str:
        input_field = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
        input_field.send_keys(amount)
        value = input_field.get_attribute("value")
        return value.replace(" ", "")

    def get_send_button(self) -> WebElement | None:
        try:
            send_button = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/button/span')
            return send_button
        except:
            return None

    def test_card_number_length(self):
        time.sleep(5)
        self.enable_rubles()
        time.sleep(2)
        value = self.card_input("12345678901234567")
        self.assertLessEqual(len(value), 16, "Card number accepts more then 16 digits")

    def check_negative_amount(self):
        self.driver.get(url='http://localhost:8000/?balance=33000&reserved=2000')
        time.sleep(5)
        self.enable_rubles()
        time.sleep(2)
        self.card_input("1111111111111111")
        time.sleep(1)
        self.amount_input("-100")

    def tearDown(self) -> None:
        self.driver.quit()

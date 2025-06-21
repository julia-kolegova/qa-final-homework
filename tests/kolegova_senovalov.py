
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:8000"

# ---------- Fixtures ---------- #
@pytest.fixture(scope="function")
def driver():
    """Spin-up Chrome (or another webdriver) for each test."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # remove if you need UI
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    yield driver
    driver.quit()


# ---------- Helper functions ---------- #
def open_with_balance(driver, balance: int | float, reserved: int | float):
    driver.get(f"{BASE_URL}?balance={balance}&reserved={reserved}")


def fill_transfer_form(driver, card_number: str, amount: str):
    """Enter card and amount without clicking the button."""
    driver.find_element(By.CSS_SELECTOR, "input[name='card']").clear()
    driver.find_element(By.CSS_SELECTOR, "input[name='card']").send_keys(card_number)

    amt_input = driver.find_element(By.CSS_SELECTOR, "input[name='amount']")
    amt_input.clear()
    amt_input.send_keys(str(amount))


def click_transfer(driver):
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()


def get_toast_text(driver) -> str:
    toast = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".toast"))
    )
    return toast.text


# ---------- TC-011 ---------- #
def test_exact_available_balance_transfer(driver):
    \"\"\"Баланс 1 100 ₽, перевод 1 000 ₽ + комиссия 100 ₽ = 0 ₽.
    Операция должна пройти успешно.\"\"\"
    open_with_balance(driver, 1100, 0)
    fill_transfer_form(driver, "5559000000000000", "1000")
    click_transfer(driver)

    assert "успешно" in get_toast_text(driver).lower()
    new_balance = driver.find_element(By.CSS_SELECTOR, "#balance").text
    assert new_balance.replace(" ", "").replace("₽", "") in {"0", "0.00"}


# ---------- TC-012 ---------- #
@pytest.mark.parametrize("amount_raw, expected_commission", [("1234,56", "123"), ("987,65", "98")])
def test_amount_with_comma(driver, amount_raw, expected_commission):
    open_with_balance(driver, 10000, 0)
    fill_transfer_form(driver, "5559000000000000", amount_raw)

    commission_text = driver.find_element(By.CSS_SELECTOR, "#fee").text
    assert commission_text.startswith(expected_commission)

    click_transfer(driver)
    assert "успешно" in get_toast_text(driver).lower()


# ---------- TC-013 ---------- #
def test_amount_with_thousand_separator(driver):
    open_with_balance(driver, 10000, 0)
    fill_transfer_form(driver, "5559000000000000", "1 000")  # пробел

    amount_field = driver.find_element(By.CSS_SELECTOR, "input[name='amount']")
    assert amount_field.get_property("value") == "1000"

    click_transfer(driver)
    assert "успешно" in get_toast_text(driver).lower()


# ---------- TC-014 ---------- #
def test_amount_more_than_two_decimals(driver):
    open_with_balance(driver, 10000, 0)
    fill_transfer_form(driver, "5559000000000000", "1234,567")  # 3 знака после запятой

    error = driver.find_element(By.CSS_SELECTOR, "#amountError").text
    assert "два знака" in error.lower()

    submit_disabled = driver.find_element(By.CSS_SELECTOR, "button[type='submit']").get_property("disabled")
    assert submit_disabled is True


# ---------- TC-015 ---------- #
def test_parallel_transfers(driver):
    \"\"\"Открываем две вкладки (два драйвера) и пытаемся списать > доступного.\"\"\"
    second_options = webdriver.ChromeOptions()
    second_options.add_argument("--headless=new")
    driver2 = webdriver.Chrome(options=second_options)
    driver2.implicitly_wait(5)

    try:
        open_with_balance(driver, 5000, 0)
        open_with_balance(driver2, 5000, 0)

        fill_transfer_form(driver, "5559000000000000", "2000")
        click_transfer(driver)
        assert "успешно" in get_toast_text(driver).lower()

        fill_transfer_form(driver2, "5559000000000000", "3000")
        click_transfer(driver2)

        toast2 = get_toast_text(driver2).lower()
        assert "недостаточно средств" in toast2
    finally:
        driver2.quit()
'''

with open('/mnt/data/test_transfer.py', 'w', encoding='utf-8') as f:
    f.write(TESTS)

print("✅ test_transfer.py written to /mnt/data")



import pytest
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:8000/"

# ---------- Fixtures ---------- #
@pytest.fixture(scope="function")
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(5)
    yield drv
    drv.quit()


def get_text(driver, selector: str) -> str:
    return driver.find_element(By.CSS_SELECTOR, selector).text


def wait_error(driver):
    return WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".error, .toast-error"))
    ).text.lower()


# ---------- TC-006 ---------- #
def test_invalid_balance_reserved_query(driver):
    """
    URL содержит balance=330%1.4 & reserved=!
    UI не должен отображать это "мусорное" значение.
    """
    invalid_url = BASE_URL + "?balance=" + quote("330%1.4") + "&reserved=%21"
    driver.get(invalid_url)

    balance_text = get_text(driver, "#balance")
    reserve_text = get_text(driver, "#reserved")

    # Проверяем, что нет символов '%' или '!' и значение числовое
    assert "%" not in balance_text
    assert "!" not in reserve_text
    assert balance_text.replace(" ", "").replace("₽", "").isdigit()
    assert reserve_text.replace(" ", "").replace("₽", "").isdigit()


# ---------- TC-007 ---------- #
def test_reserved_exceeds_balance(driver):
    """
    balance=33001, reserved=330014 -> ошибка "резерв > баланс" или ограничение значения.
    """
    driver.get(f"{BASE_URL}?balance=33001&reserved=330014")

    # Либо появится alert / toast, либо значение резерв скорректируется <= баланса
    try:
        msg = wait_error(driver)
        assert "резерв" in msg and "баланс" in msg
    except Exception:
        reserve_value = get_text(driver, "#reserved")
        balance_value = get_text(driver, "#balance")
        rv = int("".join(filter(str.isdigit, reserve_value)))
        bv = int("".join(filter(str.isdigit, balance_value)))
        assert rv <= bv


# ---------- TC-008 ---------- #
def test_euro_transfer_exceeds_balance(driver):
    """
    Баланс EUR = 1 000, перевод 1 500 => ошибка.
    """
    # Открываем евро-счёт через query (если есть поддержка)
    driver.get(f"{BASE_URL}?currency=EUR&balance=1000&reserved=0")

    # Если нужно вручную выбирать счет
    try:
        driver.find_element(By.CSS_SELECTOR, "select[name='currency'] option[value='EUR']").click()
    except Exception:
        pass  # выпадающее меню может отсутствовать

    # Заполняем форму
    driver.find_element(By.CSS_SELECTOR, "input[name='card']").send_keys("4111111111111111")
    amt = driver.find_element(By.CSS_SELECTOR, "input[name='amount']")
    amt.clear()
    amt.send_keys("1500")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    msg = wait_error(driver)
    assert "недостаточно средств" in msg


# ---------- TC-009 ---------- #
def test_balance_updates_after_rub_transfer(driver):
    """
    Перед переводом баланс 30000, резерв 2000 (доступно 28000).
    Переводим 1000 => баланс должен стать 28900.
    """
    driver.get(f"{BASE_URL}?balance=30000&reserved=2000")

    driver.find_element(By.CSS_SELECTOR, "input[name='card']").send_keys("5559000000000000")
    amt = driver.find_element(By.CSS_SELECTOR, "input[name='amount']")
    amt.clear()
    amt.send_keys("1000")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    success = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".toast"))
    )
    assert "успешно" in success.text.lower()

    new_balance_text = get_text(driver, "#balance")
    new_balance = int("".join(filter(str.isdigit, new_balance_text)))
    assert new_balance == 28900


# ---------- TC-010 ---------- #
def test_amount_starts_with_zero(driver):
    """
    Ввод суммы 0123 => ошибка "недопустимый формат" + кнопка disable.
    """
    driver.get(f"{BASE_URL}?balance=33000&reserved=2000")

    driver.find_element(By.CSS_SELECTOR, "input[name='card']").send_keys("5559000000000000")
    amt = driver.find_element(By.CSS_SELECTOR, "input[name='amount']")
    amt.clear()
    amt.send_keys("0123")

    # кнопка должна быть disabled
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    assert submit_btn.get_property("disabled")

    err_text = wait_error(driver)
    assert "недопустимый формат" in err_text or "сумма" in err_text
'''

with open('/mnt/data/test_transfer_additional.py', 'w', encoding='utf-8') as f:
    f.write(ADDITIONAL_TESTS)

print("✅ test_transfer_additional.py created with TC-006 … TC-010")


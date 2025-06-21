
import pytest
from urllib.parse import urlencode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:8000/"

# ---------- helpers ---------- #
def build_url(balance=33000, reserved=2000, **extra):
    params = {"balance": balance, "reserved": reserved}
    params.update(extra)
    return f"{BASE_URL}?{urlencode(params)}"


def wait_toast(driver):
    return WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".toast, .toast-success, .toast-error"))
    )


@pytest.fixture(scope="function")
def driver():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    drv = webdriver.Chrome(options=opts)
    drv.implicitly_wait(5)
    yield drv
    drv.quit()


def fill_card_and_amount(driver, card, amount):
    driver.find_element(By.CSS_SELECTOR, "input[name='card']").clear()
    driver.find_element(By.CSS_SELECTOR, "input[name='card']").send_keys(card)
    amt = driver.find_element(By.CSS_SELECTOR, "input[name='amount']")
    amt.clear()
    amt.send_keys(str(amount))


# ---------- TC‑001 ---------- #
def test_commission_recalculation(driver):
    driver.get(build_url(balance=20000, reserved=0))

    fill_card_and_amount(driver, "5559000000000000", "5000")
    fee_sel = "#fee"
    init_fee = driver.find_element(By.CSS_SELECTOR, fee_sel).text
    assert init_fee.startswith("500")  # 10 percent of 5000

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    assert "успешно" in wait_toast(driver).text.lower()

    # Change amount to 1000 without reload
    fill_card_and_amount(driver, "5559000000000000", "1000")
    new_fee = driver.find_element(By.CSS_SELECTOR, fee_sel).text
    assert new_fee.startswith("100")  # commission should update


# ---------- TC‑002 ---------- #
def test_success_message_amount_and_fee(driver):
    driver.get(build_url(balance=20000, reserved=0))

    fill_card_and_amount(driver, "4111111111111111", "1000")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    toast = wait_toast(driver).text.lower().replace(" ", "")
    assert "1000" in toast
    assert "100" in toast  # commission part


# ---------- TC‑003 ---------- #
def test_usd_overdraft_validation(driver):
    driver.get(build_url(balance=100, reserved=0, currency="USD"))

    # if currency dropdown exists, switch
    try:
        driver.find_element(By.CSS_SELECTOR, "select[name='currency'] option[value='USD']").click()
    except Exception:
        pass

    fill_card_and_amount(driver, "4000123456789000", "3111")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    toast = wait_toast(driver).text.lower()
    assert "недостаточно средств" in toast or "insufficient" in toast


# ---------- TC‑004 ---------- #
def test_commission_floor_small_amount(driver):
    driver.get(build_url(balance=1000, reserved=0))
    fill_card_and_amount(driver, "1234567890901122", "99")

    fee_text = driver.find_element(By.CSS_SELECTOR, "#fee").text
    assert fee_text.startswith("9")  # floor(9.9)=9


# ---------- TC‑005 ---------- #
@pytest.mark.parametrize("card, is_valid", [
    ("123456789012", False),           # 12 digits
    ("123456789012345678", False),     # 18 digits
    ("5559000000000000", True),        # 16 digits
])
def test_card_number_length_validation(driver, card, is_valid):
    driver.get(build_url(balance=10000, reserved=0))
    fill_card_and_amount(driver, card, "1000")

    error_present = False
    try:
        err = driver.find_element(By.CSS_SELECTOR, "#cardError").text
        error_present = bool(err.strip())
    except Exception:
        error_present = False

    submit_disabled = driver.find_element(By.CSS_SELECTOR, "button[type='submit']").get_property("disabled") or error_present

    if is_valid:
        assert not submit_disabled
    else:
        assert submit_disabled
'''

with open('/mnt/data/test_transfer_core.py', 'w', encoding='utf-8') as f:
    f.write(CORE_TESTS)

print("✅ test_transfer_core.py with TC-001…TC-005 created")


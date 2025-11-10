import unittest
import time
import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

LOGS = "logs.csv"

class TestApp(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.get("https://127.0.0.1")
        time.sleep(2)

    def tearDown(self):
        self.driver.quit()

    def _last_log_entry(self):
        """Возвращает последнюю строку из logs.csv"""
        if not os.path.exists(LOGS):
            return None
        with open(LOGS, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            if len(rows) > 1:
                return rows[-1]
        return None

    def test_admin_login(self):
        driver = self.driver
        driver.find_element(By.NAME, "username").send_keys("admin")
        driver.find_element(By.NAME, "password").send_keys("12345")
        driver.find_element(By.XPATH, "//form/button").click()
        time.sleep(2)
        header = driver.find_element(By.TAG_NAME, "h2")
        self.assertEqual(header.text, "Добро пожаловать, admin!")

        last = self._last_log_entry()
        self.assertIsNotNone(last)
        self.assertEqual(last[2], "Успешный вход")

    def test_admin_registration_and_user_login(self):
        driver = self.driver
        TESTING_NICKNAME = "testSuiteUser"
        TESTING_PWD = "1234"

        driver.find_element(By.NAME, "username").send_keys("admin")
        driver.find_element(By.NAME, "password").send_keys("12345")
        driver.find_element(By.XPATH, "//form/button").click()
        time.sleep(2)

        driver.get("https://127.0.0.1/register")
        time.sleep(2)

        driver.find_element(By.NAME, "username").send_keys(TESTING_NICKNAME)
        driver.find_element(By.NAME, "password").send_keys(TESTING_PWD)
        driver.find_element(By.NAME, "admin_login").send_keys("admin")
        driver.find_element(By.NAME, "admin_password").send_keys("12345")
        driver.find_element(By.XPATH, "//form/button").click()
        time.sleep(2)

        last = self._last_log_entry()
        self.assertIsNotNone(last)
        self.assertEqual(last[2], "Регистрация нового пользователя")

        driver.get("https://127.0.0.1/logout")
        time.sleep(2)

        last = self._last_log_entry()
        self.assertIsNotNone(last)
        self.assertEqual(last[2], "Выход из системы")

        driver.find_element(By.NAME, "username").send_keys(TESTING_NICKNAME)
        driver.find_element(By.NAME, "password").send_keys(TESTING_PWD)
        driver.find_element(By.XPATH, "//form/button").click()
        time.sleep(2)

        header = driver.find_element(By.TAG_NAME, "h2")
        self.assertEqual(header.text, f"Добро пожаловать, {TESTING_NICKNAME}!")

    def test_incorrect_pwd(self):
        driver = self.driver
        driver.find_element(By.NAME, "username").send_keys("admin")
        driver.find_element(By.NAME, "password").send_keys("wrongpwd")
        driver.find_element(By.XPATH, "//form/button").click()
        time.sleep(2)
        try:
            error_msg = driver.find_element(By.CLASS_NAME, "error")
            self.assertIn("Неверный", error_msg.text)
        except NoSuchElementException:
            self.fail("Не найдено сообщение об ошибке")

        last = self._last_log_entry()
        self.assertIsNotNone(last)
        self.assertEqual(last[2], "Неверный пароль")

    def test_404(self):
        driver = self.driver
        driver.get("https://127.0.0.1/some/nonexistent/page")
        time.sleep(2)
        header = driver.find_element(By.TAG_NAME, "h1")
        self.assertEqual(header.text, "404 — Страница не найдена")

        last = self._last_log_entry()
        self.assertIsNotNone(last)
        self.assertEqual(last[2], "Страница не найдена")

    def test_403(self):
        driver = self.driver
        driver.get("https://127.0.0.1/register")
        time.sleep(2)
        header = driver.find_element(By.TAG_NAME, "h1")
        self.assertEqual(header.text, "403 — Доступ запрещён")

        last = self._last_log_entry()
        self.assertIsNotNone(last)
        self.assertEqual(last[2], "Доступ запрещён")

    def test_session_timeout(self):
        driver = self.driver
        driver.find_element(By.NAME, "username").send_keys("admin")
        driver.find_element(By.NAME, "password").send_keys("12345")
        driver.find_element(By.XPATH, "//form/button").click()
        time.sleep(2)

        time.sleep(190)

        header = driver.find_element(By.TAG_NAME, "h2")
        self.assertEqual(header.text, "Вход")

        last = self._last_log_entry()
        self.assertIsNotNone(last)
        self.assertEqual(last[2], "Сессия завершена по таймауту")

if __name__ == '__main__':
    unittest.main()

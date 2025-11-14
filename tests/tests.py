import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestSite(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://127.0.0.1:443"
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(5)
        self.wait = WebDriverWait(self.driver, 10)

        self.test_username = "proverka"
        self.test_password = "12345"

    def tearDown(self):
        self.driver.quit()

    def test_01_open_login(self):
        self.driver.get(f"{self.base_url}/login")
        self.assertIn("вход", self.driver.page_source.lower())

    def test_02_register_user(self):
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys("admin1")
        self.driver.find_element(By.NAME, "password").send_keys("qwerty")
        self.driver.find_element(By.XPATH, "/html/body/div/form[1]/button").click()

        self.driver.find_element(By.XPATH, "/html/body/a[2]").click()
        self.wait.until(EC.presence_of_element_located((By.NAME, "admin_login")))

        self.driver.find_element(By.NAME, "username").send_keys(self.test_username)
        self.driver.find_element(By.NAME, "password").send_keys(self.test_password)
        self.driver.find_element(By.NAME, "admin_login").send_keys("admin")
        self.driver.find_element(By.NAME, "admin_password").send_keys("12345")
        self.driver.find_element(By.XPATH, "/html/body/div/form/button").click()

        self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/h2")))
        self.assertIn("добро пожаловать", self.driver.page_source.lower())

    def test_03_login_user(self):
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(self.test_username)
        self.driver.find_element(By.NAME, "password").send_keys(self.test_password)
        self.driver.find_element(By.XPATH, "/html/body/div/form[1]/button").click()

        self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/h2")))

    def test_04_login_bad_password(self):
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(self.test_username)
        self.driver.find_element(By.NAME, "password").send_keys("asdzxc")
        self.driver.find_element(By.XPATH, "/html/body/div/form[1]/button").click()

        self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div/p")))

    def test_05_login_bad_username(self):
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys("qweqweasdasdzxcasdzc")
        self.driver.find_element(By.NAME, "password").send_keys(self.test_password)
        self.driver.find_element(By.XPATH, "/html/body/div/form[1]/button").click()

        self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div/p")))

    def test_06_admin_page_access_denied(self):
        self.driver.get(f"{self.base_url}/main/{self.test_username}")
        self.assertIn("вход", self.driver.page_source.lower())

    def test_07_login_admin_and_main(self):
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys("admin1")
        self.driver.find_element(By.NAME, "password").send_keys("qwerty")
        self.driver.find_element(By.XPATH, "/html/body/div/form[1]/button").click()

        self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/h2")))

        self.driver.get(f"{self.base_url}/main/admin")
        self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/header/div/div/a[1]")))

    def test_08_logout(self):
        self.driver.get(f"{self.base_url}/logout")
        self.assertIn("вход", self.driver.page_source.lower())

    def test_09_404error_1(self):
        self.driver.get(f"{self.base_url}/asdasd")
        self.assertIn("вход", self.driver.page_source.lower())

    def test_10_404error_2(self):
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys(self.test_username)
        self.driver.find_element(By.NAME, "password").send_keys(self.test_password)
        self.driver.find_element(By.XPATH, "/html/body/div/form[1]/button").click()
        self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/h2")))

        self.driver.get(f"{self.base_url}/qqqqq")

        self.assertIn("404", self.driver.page_source.lower())
    
    def test_11_403(self):
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "username").send_keys("admin1")
        self.driver.find_element(By.NAME, "password").send_keys("qwerty")
        self.driver.find_element(By.XPATH, "/html/body/div/form[1]/button").click()
        self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/h2")))
        self.driver.find_element(By.XPATH, "/html/body/a[1]").click()
        self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/main/section[1]/div/div/p"))) 

        self.driver.find_element(By.XPATH, "/html/body/header/div/div/a[4]").click()
        self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div/h2")))   

        self.driver.find_element(By.NAME, "username").send_keys(self.test_username)
        self.driver.find_element(By.NAME, "password").send_keys(self.test_password)
        self.driver.find_element(By.XPATH, "/html/body/div/form[1]/button").click()
        self.wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/h1"))) 
        self.assertIn("403", self.driver.page_source.lower())


if __name__ == "__main__":
    unittest.main()
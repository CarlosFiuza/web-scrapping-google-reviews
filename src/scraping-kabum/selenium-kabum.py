from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

url = 'https://www.kabum.com.br/computadores/monitores/monitor-gamer'

option = Options()
option.headless = True
driver = webdriver.Chrome()  # options

driver.get(url)

sleep(10)

driver.find_element(
    by=By.XPATH, value='//button[@title="Visualizar em Lista"]').click()

sleep(20)
driver.quit()

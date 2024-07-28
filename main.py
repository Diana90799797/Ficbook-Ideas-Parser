from selenium import webdriver as wd
from selenium.webdriver.common.by import By
import time

# Opens ficbook page 'popular ideas' and copies html body(simple request method have not worked)
options = wd.ChromeOptions()
options.page_load_strategy = 'eager'
driver = wd.Chrome(options=options)
driver.get('https://ficbook.net/requests-346578/popular')
time.sleep(1)
html = driver.find_element(By.TAG_NAME, 'body').get_attribute('outerHTML')
driver.quit()


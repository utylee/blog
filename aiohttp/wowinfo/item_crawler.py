from selenium import webdriver
from selenium.webdriver.firefox.options import Options

options = Options()
#options.headless = True;
driver = webdriver.Firefox(executable_path='/usr/local/bin/geckodriver', firefox_options=options)

driver.get('https://www.naver.com')



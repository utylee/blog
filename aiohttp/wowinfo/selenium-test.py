from selenium import webdriver
from selenium.webdriver.firefox.options import Options


'''
os.environ['MOZ_HEADLESS'] = '1'
drv = webdriver.Firefox()
drv.get('https://google.com')
drv.close()
'''

'''
drv = webdriver.Chrome('/usr/local/bin/chromedriver')
drv.get("https://www.naver.com")
drv.implicitly_wait(3)
drv.get_screenshot_as_file('/mnt/d/naver.png')
drv.quit()
'''

options = Options()
#options.headless = True
#drv = webdriver.Firefox(firefox_options=options )
drv = webdriver.Firefox(firefox_options=options, executable_path = '/usr/bin/geckodriver')
#drv = webdriver.Firefox(firefox_options=options, executable_path = '/usr/bin/firefox')
drv.implicitly_wait(3)
drv.get("https://www.naver.com")
drv.quit()

'''
#options = webdriver.FirefoxOptions()
#options.add_argument("-headless")
#drv = webdriver.Firefox(firefox_options=options, executable_path = '/usr/local/bin/geckodriver')
#drv = webdriver.Firefox(firefox_options=options) 
drv = webdriver.PhantomJS('/usr/bin/phantomjs')
drv.set_window_size(1024, 768)
drv.set_page_load_timeout(600)
drv.close()
'''


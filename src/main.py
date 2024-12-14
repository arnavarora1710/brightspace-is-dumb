import json, os
from bp_web import get_bp_page
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

def save_cookie(driver, path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, 'w') as filehandler:
        json.dump(driver.get_cookies(), filehandler)

def load_cookie(driver, path):
    with open(path, 'r') as cookiesfile:
        cookies = json.load(cookiesfile)
    for cookie in cookies:
        driver.add_cookie(cookie)

website = get_bp_page()
cookie_path = '../cookies/cur_session_cookies.json'
service = Service()
options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
driver = webdriver.Chrome(service=service, options=options)
if not os.path.exists(cookie_path):
    driver.get(website)
    while True:
        print('Please log in and press enter when you are done.')
        if input() == '':
            break
    save_cookie(driver, cookie_path)
    print('Cookies saved! Log in again to see the content.')
    driver.quit()
else:
    home_page = "https://purdue.brightspace.com/"
    driver.get(home_page)
    load_cookie(driver, cookie_path)
    driver.refresh()
    driver.get(website)
    matches = driver.find_elements(By.CLASS_NAME, 'd2l-htmlblock-untrusted')
    for match in matches:
        print(match.text)
    driver.quit()
import json, time, os, glob
from bp_web import get_bp_page
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

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

def get_last_downloaded_file(download_dir):
    download_dir = os.path.expanduser(download_dir)
    files = glob.glob(os.path.join(download_dir, "*"))
    # remove all files with crdownload
    files = [f for f in files if not f.endswith('crdownload')]
    latest_file = max(files, key=os.path.getctime)
    return latest_file

bad = ["Syllabus", "Course Schedule", "Bookmarks", "Table of Contents", "Start Here", "University Policies and Statements", "Student Support and Resources"]
vis = set()
cnt = 0
def scrape(driver):
    global vis, cnt, bad
    nav_class = ".d2l-le-TreeAccordionItem-anchor.vui-heading-4"
    all_navs = driver.find_elements(By.CSS_SELECTOR, nav_class)
    all_navs = all_navs[4:]
    for nav in all_navs:
        child_navs = nav.find_elements(By.CSS_SELECTOR, nav_class)
        # remove from all_navs
        for child in child_navs:
            all_navs.remove(child)
    print(len(all_navs))
    ans = [['', '', []]]
    for nav in all_navs:
        print('Nav:', nav.text)
        print('ID:', nav.get_attribute('id'))
        print('Class:', nav.get_attribute('class'))
        print('Tag:', nav.tag_name)
        if nav.get_attribute('id') in vis:
            continue
        vis.add(nav.get_attribute('id'))
        nav.click()
        time.sleep(1)

        # get titles
        heading = "d2l-page-title d2l-heading bsi-set-solid vui-heading-1"
        heading_list = heading.split(' ')
        element = driver.find_element(By.CSS_SELECTOR, f".{'.'.join(heading_list)}")
        print('Title:', element.text)
        if element.text in bad:
            continue
        ans[0][0] = element.text
        print('Title:', element.text)

        # get content
        content_cur = driver.find_element(By.CLASS_NAME, 
                    "d2l-htmlblock-untrusted").find_element(By.TAG_NAME, 
                    'd2l-html-block').get_attribute('html')
        soup = BeautifulSoup(content_cur, 'html.parser')
        for element in soup.find_all(class_=True):
            del element['class']
        cleaned_html = str(soup)
        ans[0][1] = cleaned_html
        print('Content:', cleaned_html)

        # precompute pdf files to download
        pdf_content = driver.find_elements(By.XPATH, "//*[@href[substring(., string-length(.) - string-length('View') +1) = 'View']]")
        precomp = []
        for pdfs in pdf_content:
            precomp.append([pdfs.text, pdfs.get_attribute('href')])

        # get next page
        ret = scrape(driver)

        # get files in order of dfs
        for v in precomp:
            txt = v[0]
            link = v[1]
            if link in vis:
                continue
            vis.add(link)
            ans[0][2].append([txt, link])
            print('File:', txt, link)

        if ret != []:
            ans.extend(ret)
        break
    return ans

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
    ans = scrape(driver)
    print(len(ans))
    for i in range(len(ans)):
        print(i, ans[i][0], type(ans[i][1]))
    if not os.path.exists('../output'):
        os.makedirs('../output')
    for i in range(len(ans)):
        # make output[i] directories
        if not os.path.exists(f'../output/{ans[i][0]}'):
            os.makedirs(f'../output/{ans[i][0]}')
        if ans[i][1] != "":
            with open(f'../output/{ans[i][0]}/content.html', 'w') as filehandler:
                filehandler.write(f"<h1>{ans[i][0]}</h1>")
                filehandler.write(ans[i][1])
        for j in range(len(ans[i][2])):
            driver.get(ans[i][2][j][1])
            latest_file = get_last_downloaded_file('~/Downloads')
            try:
                button = driver.find_element(By.XPATH, "//*[starts-with(@id, 'd2l_content_')]")
            except Exception as e:
                continue
            button.click()
            while latest_file == get_last_downloaded_file('~/Downloads'):
                continue
            latest_file = get_last_downloaded_file('~/Downloads')
            os.rename(latest_file, f'../output/{ans[i][0]}/{latest_file.split("/")[-1]}')
    driver.quit()
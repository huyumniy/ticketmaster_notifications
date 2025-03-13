import undetected_chromedriver as webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from .proxyExtension import ProxyExtension
import os, sys
import time
import random

def selenium_connect(proxy):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    #options.add_argument("--incognito")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--lang=EN')
    cwd= os.getcwd()
    slash = "\\" if sys.platform == "win32" else "/"
    directory_name = cwd + slash + "vpn"
    extension = os.path.join(cwd, directory_name)
    if proxy and proxy != 'vpn':
        proxy = proxy.split(":", 3)
        proxy[1] = int(proxy[1])
        proxy_extension = ProxyExtension(*proxy)
        options.add_argument(f"--load-extension={proxy_extension.directory}")
    elif proxy == '': pass
    else: options.add_argument(f"--load-extension={extension}")

    prefs = {"credentials_enable_service": False,
        "profile.password_manager_enabled": False}
    options.add_experimental_option("prefs", prefs)

    chromedriver_path = os.path.join(os.getcwd(), 'chromedriver.exe')
    service = Service(executable_path=chromedriver_path)

    # choose different webdriver version for server users
    if os.getlogin() in ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12', 'S13', 'S14', 'S15',
    'S3U1', 'S3U2', 'S3U3', 'S3U4', 'S3U5', 'S3U6', 'S3U7', 'S3U8', 'S3U9', 'S3U10', 'S3U11', 'S3U12', 'S3U13', 'S3U14', 'S3U15', 'S3U16',
    'Admin3']:
        driver = webdriver.Chrome(
            version_main=129,
            options=options,
            enable_cdp_events=True
        )
    else:
        driver = webdriver.Chrome(
            options=options,
            enable_cdp_events=True
        )

    # screen_width, screen_height = driver.execute_script(
    #     "return [window.screen.width, window.screen.height];")
    
    # desired_width = int(screen_width / 2)
    # desired_height = int(screen_height / 3)
    # driver.set_window_position(0, 0)
    # driver.set_window_size(screen_width, screen_height)

    return driver


def wait_for_element(driver, selector, click=False, timeout=10, xpath=False, debug=False, scrollToBottom=False):
    try:
        if xpath:
            element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, selector)))
        else:
            element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        
        if click:
            driver.execute_script("arguments[0].scrollIntoView();", element)
            if scrollToBottom: driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", check_for_element(driver, '#main-content'))
            element.click()
        return element
    except Exception as e:
        if debug: print("selector: ", selector, "\n", e)
        return False


def check_for_element(driver, selector, click=False, xpath=False, debug=False):
    try:
        if xpath:
            element = driver.find_element(By.XPATH, selector)
        else:
            element = driver.find_element(By.CSS_SELECTOR, selector)
        if click: 
            driver.execute_script("arguments[0].scrollIntoView();", element)
            # slow_mouse_move_to_element(driver, element)
            element.click()
        return element
    except Exception as e: 
        if debug: print("selector: ", selector, "\n", e)
        return False

def check_for_elements(driver, selector, xpath=False, debug=False):
    try:
        if xpath:
            element = driver.find_elements(By.XPATH, selector)
        else:
            element = driver.find_elements(By.CSS_SELECTOR, selector)
        return element
    except Exception as e: 
        if debug: print("selector: ", selector, "\n", e)
        return False


def reconnect_vpn(driver):
    countries = ['UK', 'Singapore', 'Netherlands', 'France']
    while True:
        try:
            driver.get('chrome://extensions/')
            js_code = """
                const callback = arguments[0];
                chrome.management.getAll((extensions) => {
                    callback(extensions);
                });
            """
            extensions = driver.execute_async_script(js_code)
            filtered_extensions = [extension for extension in extensions if 'VeePN' in extension['name']]
            
            vpn_id = [extension['id'] for extension in filtered_extensions if 'id' in extension][0]
            vpn_url = f'chrome-extension://{vpn_id}/src/popup/popup.html'
            driver.get(vpn_url)
            for _ in range(0, 2):
                wait_for_element(driver, 'button[class="intro-steps__btn"]', timeout=5)
                check_for_element(driver, 'button[class="intro-steps__btn"]', click=True)
            check_for_element(driver, 'button[class="premium-banner__skip btn"]', click=True)
            check_for_element(driver, 'button[class="rate-us-modal__close"]', click=True)
            is_connected = check_for_element(driver, 'button[class="connect-button connect-button--connected"]')
            if is_connected: 
                is_connected.click()
            # select_element = driver.find_element(By.CSS_SELECTOR, 'div[class="select-location"]')
            # select_element.click()
            time.sleep(2)
            
            check_for_element(driver, 'button[class="connect-region__location"]', click=True)
            wait_for_element(driver, 'div[class="scroll-panel fullheight locations-view"]', timeout=3)
            element = check_for_element(driver, f'//*[@id="root"]/div[2]/div/div/main/ul/li[1]/div/div[2]/div/ul/li/div/div/span/span[1][contains(text(), "{random.choice(countries)}")]', xpath=True)
            driver.execute_script("arguments[0].scrollIntoView();", element)
            element.click()
            wait_for_element(driver, 'button[class="connect-button connect-button--disconnected"]', timeout=3)
            check_for_element(driver,'button[class="connect-button connect-button--disconnected"]', click=True)
            time.sleep(5)
            break
        except Exception as e: print(e)
    return True

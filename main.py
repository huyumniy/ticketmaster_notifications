import requests
import time
import json
import undetected_chromedriver as webdriver
import re
import logging
from random import choice
import os, sys
import shutil, tempfile
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SPREADSHEET_ID = '1tn6J2g7Hyk57tx51TCaczsEIFEw1uHhwu96Cyfr3AOA'

class ProxyExtension:
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]},
        "minimum_chrome_version": "76.0.0"
    }
    """

    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: %d
            },
            bypassList: ["localhost"]
        }
    };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
        callbackFn,
        { urls: ["<all_urls>"] },
        ['blocking']
    );
    """

    def __init__(self, host, port, user, password):
        self._dir = os.path.normpath(tempfile.mkdtemp())

        manifest_file = os.path.join(self._dir, "manifest.json")
        with open(manifest_file, mode="w") as f:
            f.write(self.manifest_json)

        background_js = self.background_js % (host, port, user, password)
        background_file = os.path.join(self._dir, "background.js")
        with open(background_file, mode="w") as f:
            f.write(background_js)

    @property
    def directory(self):
        return self._dir

    def __del__(self):
        shutil.rmtree(self._dir)

def selenium_connect(proxy):
    print(proxy)
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
    directory_name2 = cwd + slash + "vpn"
    extension2 = os.path.join(cwd, directory_name2)
    if proxy and proxy != 'vpn':
        proxy = proxy.split(":", 3)
        proxy[1] = int(proxy[1])
        print(proxy)
        proxy_extension = ProxyExtension(*proxy)
        options.add_argument(f"--load-extension={proxy_extension.directory}")
    else: options.add_argument(f"--load-extension={extension2}")

    prefs = {"credentials_enable_service": False,
        "profile.password_manager_enabled": False}
    options.add_experimental_option("prefs", prefs)

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


def get_random_proxy():
    with open('proxies.txt', "r") as file:
        lines = file.readlines()

    random_line = choice(lines)
    random_line = random_line.strip()  # Remove leading/trailing whitespace and newline characters
    return random_line
    # PROXY = {
    #     'http': f'http://{user}:{password}@{host}:{port}',
    #     'https': f'http://{user}:{password}@{host}:{port}'
    # }
    print(PROXY)
    return PROXY

credentials = None
processed_rows = set()

def authorize():
    global credentials
    if os.path.exists("token.json"):
        credentials = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            credentials = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(credentials.to_json())


def reconnect_vpn(driver):
    while True:
        try:
            driver.get('chrome-extension://empilmpffmhdehbkamjbfkclkadeiffg/popup/index.html')
            wait_for_element(driver, 'button[class="button button--pink consent-text-controls__action"]', click=True, timeout=5)
            is_connected = check_for_element(driver, 'div[class="play-button play-button--pause"]')
            if is_connected: 
                driver.find_element(By.CSS_SELECTOR, 'div[class="play-button play-button--pause"]').click()
            print('select-location')
            select_element = driver.find_element(By.CSS_SELECTOR, 'div[class="select-location"]')
            print('click-select')
            select_element.click()
            print('random-choice')
            time.sleep(2)
            element = random.choice(check_for_elements(driver, '//ul[@class="locations"][2]/li', xpath=True))
            driver.execute_script("arguments[0].scrollIntoView();", element)
            element.click()
            time.sleep(5)
            break
        except Exception as e: pass


def get_data_from_google_sheets():
    try:
        # Authenticate with Google Sheets API using the credentials file
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)

            with open("token.json", "w") as token:
                token.write(creds.to_json())

        # Connect to Google Sheets API
        service = build("sheets", "v4", credentials=creds)

        # Define the range to fetch (assuming the data is in the first worksheet and starts from cell A2)
        range_name = "main!A2:I"

        # Fetch the data using batchGet
        request = service.spreadsheets().values().batchGet(spreadsheetId=SPREADSHEET_ID, ranges=[range_name])
        response = request.execute()

        # Extract the values from the response
        values = response['valueRanges'][0]['values']

        return values
    
    except HttpError as error:
        print(f"An HTTP error occurred: {error}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def update_status(service, row, color):
    requests = []
    requests.append({
        "updateCells": {
            "range": {
                "sheetId": 0,
                "startRowIndex": row - 1,
                "endRowIndex": row,
                "startColumnIndex": 0,
                "endColumnIndex": 1
            },
            "rows": [
                {
                    "values": [
                        {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 1.0 if color == "red" else 0.0,
                                    "green": 1.0  if color == "green" else 0.0,
                                    "blue": 0.0,
                                    "alpha": 1.0
                                }
                            }
                        }
                    ]
                }
            ],
            "fields": "userEnteredFormat.backgroundColor"
        }
    })

    batch_update_request = {
        "requests": requests
    }

    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=batch_update_request
    ).execute()


def offset(link, whitelist, price, quantity, name, date, city, driver, i = 0):
    print(quantity)
    data = {"link": link, "price": price}
    base_url = data['link']
    print('checking for ' + base_url)
    match = None
    match_old = None
    try:
        pattern = r"(https:\/\/www\.ticketmaster\.)(?P<domain>(?:co|com)\.)?(?P<country>\w{2})\/(?P<name>.*)\/(?P<event>event)\/(?P<last_code>[A-Z0-9]+)"
        match = re.search(pattern, base_url)
    except Exception as e:
        print(e)

    try:
        pattern_old = r"(https:\/\/www\.ticketmaster\.)(?P<domain>(?:co|com)\.)?(?P<country>\w{2})\/(?P<event>event)\/(?P<name>.*)\/(?P<last_code>[0-9]+)"
        match_old = re.match(pattern_old, base_url)
    except Exception as e:
        print(e)
    if match:
        base = match.group(1)
        domain = match.group('domain')[:-1] if match.group('domain') else None
        rest = match.group(4)
        country_code = match.group("country")
        last_code = match.group("last_code")
        max_price = data['price']
        full_link = f"{base}{domain}.{country_code}{rest}{last_code}"
    elif match_old:
        country_code = match_old.group('country').upper()
        last_id = match_old.group('last_code')
        max_price = data['price']
        full_link = match_old.group(0)
    else:
        print("No match found.")
        return False
    if match:
        if domain:
            formatted_url = f"https://www.ticketmaster.{domain}.{country_code}/api/quickpicks/{last_code}/list?&qty={quantity}&offset={i}&resale=false&min=0&max={max_price}"
            if not max_price: formatted_url = f"https://www.ticketmaster.{domain}.{country_code}/api/quickpicks/{last_code}/list?&qty={quantity}&offset={i}&resale=false"
        else:
            formatted_url = f"https://www.ticketmaster.{country_code}/api/quickpicks/{last_code}/list?&qty={quantity}&offset={i}&resale=false&min=0&max={max_price}"
            if not max_price: formatted_url = f"https://www.ticketmaster.{country_code}/api/quickpicks/{last_code}/list?&qty={quantity}&offset={i}&resale=false"
    elif match_old:
        formatted_url = f"https://availability.ticketmaster.eu/api/v2/TM_{country_code}/availability/{last_id}?subChannelId={i}&min=0&max={max_price}"
        if not max_price: formatted_url = f"https://availability.ticketmaster.eu/api/v2/TM_{country_code}/availability/{last_id}?subChannelId={i}"
    print(formatted_url)
    data = None
    # while True:
    #     try:
    #         headers = genhead()
    #         response = requests.get(url=formatted_url, headers=headers, timeout=10, proxies=get_random_proxy())
    #         print(response)
    #         logging.info("Request successful. Status code: %d", response.status_code)
    #         if response.status_code == 200:
    #             data = response.json()
    #         try:
    #             if data['response'] == 'block' or 'correlationId' in data:
    #                 break
    #         except Exception as e:
    #             logging.exception("Block error: %s", str(e))

    #         break

    #     except requests.exceptions.RequestException as e:
    #         logging.error("Request error: %s", str(e))
    #     except Exception as e:
    #         logging.exception("An unexpected error occurred: %s", str(e))
    # if not data: return

    driver.get(formatted_url)
    data_raw = None
    ban = check_for_element(driver, '#t1')
    if ban: return '403'
    try: data_raw = driver.find_element(By.TAG_NAME, 'pre').text
    except Exception as e: print(e)
    data = json.loads(data_raw)
    success = False
    should_wait = False
    try:
        if match:
            total = data.get('total')
            if total is None or total < 1:
                return False
            if whitelist:
                for pick in data['picks']:
                    if pick['name'] in whitelist:
                        success = True
            else:
                success = True

        elif match_old:
            if whitelist and data["offers"]:
                for el in data['offers']:
                    if el['type'] in whitelist and re.match(r"(.+?)\s-\s", el['restrictions'][0]).group(1) in whitelist:
                        success = True
                        should_wait = True
                        break
            elif not whitelist and data['offers']:
                success = True
                should_wait = True
            print(success)
    except Exception as e:
        print(e)
    if success:
        try:
            json_data = json.dumps(f"З'явилися нові квитки на матч:\nназва: {name}\nдата: {date}\
            \nмісто: {city}\n{full_link}")
            # Set the headers to specify the content type as JSON
            headers = {
                "Content-Type": "application/json"
            }

            # Send the POST request
            try:
                response = requests.post("http://localhost:40/book", data=json_data, headers=headers)
                if response.status_code == 200:
                    print("POST request successful!")
                else:
                    raise Exception("POST request failed with status code: " + str(response.status_code))
            except Exception as e:
                print(e)
                with open('exception_log.txt', 'a') as file:
                    file.write(str(e) + "\n")
        except Exception as e:
            print(e)
            # Save exception information to a text file
            with open('exception_log.txt', 'a') as file:
                file.write(str(e) + "\n")
    return should_wait


def process_row(driver, data):
    status, whitelist, price, quantity, link, name, date, city = data
    # update_status(service, row, "green")
    if link is None or price is None:
        return
    if whitelist:
        whitelist = whitelist.split('  ')
    if type(whitelist) != list: whitelist = [whitelist]
    print(whitelist)
    counter = 0
    print(link)
    if re.match(r"(https:\/\/www\.ticketmaster\.)(?P<domain>(?:co|com)\.)?(?P<country>\w{2})\/(?P<event>event)\/(?P<name>.*)\/(?P<last_code>[0-9]+)", link):
        for i in range(1, 55, 1):
            if counter > 5: break
            value = offset(link, whitelist, price, quantity, name, date, city, driver, i=i)
            if value == False: counter+=1
            elif value == '403': reconnect_vpn(driver)

    elif not whitelist and re.match(r"(https:\/\/www\.ticketmaster\.)(?P<domain>(?:co|com)\.)?(?P<country>\w{2})\/(?P<name>.*)\/(?P<event>event)\/(?P<last_code>[A-Z0-9]+)", link):
        value = offset(link, whitelist, price, quantity, name, date, driver, city)
        if value == '403': reconnect_vpn(driver)

    elif whitelist and re.match(r"(https:\/\/www\.ticketmaster\.)(?P<domain>(?:co|com)\.)?(?P<country>\w{2})\/(?P<name>.*)\/(?P<event>event)\/(?P<last_code>[A-Z0-9]+)", link):
        for i in range(0, 101, 20):
            if counter > 5: break
            value = offset(link, whitelist, price, quantity, name, date, city, driver, i=i)
            if value == False: counter+=1
            elif value == '403': reconnect_vpn(driver)
    
    else:
        try:
            json_data = json.dumps(f"{link}\nБули передані невірні дані в таблицю або LINK, перевірте вміст таблиці або зверніться до <@U056PUY23A6|Vlad>.")
            # Set the headers to specify the content type as JSON
            headers = {
                "Content-Type": "application/json"
            }
            # Send the POST request
            try:
                response = requests.post("http://localhost:40/book", data=json_data, headers=headers)
                if response.status_code == 200:
                    print("POST request successful!")
                else:
                    raise Exception("POST request failed with status code: " + str(response.status_code))
            except Exception as e:
                print(e)
                with open('exception_log.txt', 'a') as file:
                    file.write(str(e) + "\n")
        except Exception as e:
            print(e)
            # Save exception information to a text file
            with open('exception_log.txt', 'a') as file:
                file.write(str(e) + "\n")
    # update_status(service, row, "red")

def ua():
    with open('uas') as ugs:
        uas = [x.strip() for x in ugs.readlines()]
        ugs.close()
    return choice(uas)

def genhead():
    headers = {
        "User-Agent": ua(),
        "Referer": "http://example.com",  # Replace with a valid referer URL
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }
    return headers

def main():
    rows = get_data_from_google_sheets()
    proxy = rows[0][8]
    if proxy == 'vpn' or proxy == '':
        driver = selenium_connect(proxy)
        reconnect_vpn(driver)
    else:
        driver = selenium_connect(get_random_proxy())
    while True:
        rows = get_data_from_google_sheets()
        for row in rows:
            status, whitelist, quantity, price, link, name, date, city, proxy = row
            data = [status, whitelist, price, quantity, link, name, date, city]
            if not link: break
            process_row(driver, data)

            # Clear the processed_rows set to start processing from the beginning of the sheet
        

if __name__ == "__main__":
    
    main()

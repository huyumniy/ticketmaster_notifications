import requests
import json
import re
import logging
import os, sys
import time
import random
from selenium.webdriver.common.by import By
from Utils.seleniumUtil import check_for_element, reconnect_vpn, selenium_connect
from Utils.proxyExtension import ProxyExtension
from Utils.sheetsApi import get_data_from_google_sheets
import datetime


def offset(link, whitelist, price, quantity, name, date, city, driver, i=0):
    print(quantity)
    data = {"link": link, "price": price}
    base_url = data['link']
    # print('Checking for: ' + base_url)
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
            formatted_url = f"https://www.ticketmaster.{domain}.{country_code}/api/quickpicks/{last_code}/list?" \
                f"{'&qty=' + str(quantity) if quantity else ''}" \
                f"&offset={i}&resale=false" \
                f"{'&min=0&max=' + str(max_price) if max_price else '&sort=price'}"
        else:
            formatted_url = f"https://www.ticketmaster.{country_code}/api/quickpicks/{last_code}/list?" \
                f"{'&qty=' + str(quantity) if quantity else ''}" \
                f"&offset={i}&resale=false" \
                f"{'&min=0&max=' + str(max_price) if max_price else '&sort=price'}"
    elif match_old:
        subdomain = "ae" if country_code.lower() == "ae" else "eu"
        formatted_url = f"https://availability.ticketmaster.{subdomain}/" \
            f"api/v2/TM_{country_code}/availability/{last_id}?subChannelId={i}" \
            f"{'&min=0&max=' + str(max_price) if max_price else '&sort=price'}"

    print(formatted_url)
    data = None

    driver.get(formatted_url)
    data_raw = None
    ban = check_for_element(driver, '#t1')
    if ban: 
        print("HTTP 403")
        return '403'
    else:
        print("HTTP 200")  # Status code
    try: 
        data_raw = driver.find_element(By.TAG_NAME, 'pre').text
        print("Raw data received: ", data_raw)  # Add this line to print the raw data
    except Exception as e: 
        print(e)
        return False  # Return if there's an issue fetching the data

    if not data_raw:
        print("No data received from the URL.")
        return False  # Return if the data is empty

    try:
        data = json.loads(data_raw)
    except json.JSONDecodeError as e:
        print(f"JSON decoding failed: {e}")
        return False  # Return if there's an issue parsing the JSON

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
            if whitelist:
                if data["offers"]:
                    for el in data['offers']:
                        if el['type'] in whitelist and re.match(r"(.+?)\s-\s", el['restrictions'][0]).group(1) in whitelist:
                            success = True
                            should_wait = True
                            break
            elif not whitelist:
                if data['offers']:
                    success = True
                    should_wait = True
            print(success)
    except Exception as e:
        print(e)
    if success:
        try:
            json_data = json.dumps(f"З'явилися нові квитки на матч:\nназва: {name}\nдата: {date}\nмісто: {city}\n{full_link}")
            # Set the headers to specify the content type as JSON
            headers = {
                "Content-Type": "application/json"
            }

            # Send the POST request
            try:
                response = requests.post("http://localhost:4040/book", data=json_data, headers=headers)
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
    whitelist, price, quantity, link, name, date, city, proxy = data
    if link is None:
        print("Link is required!")
        return 
    if whitelist:
        whitelist = whitelist.split('  ')
    if type(whitelist) != list: whitelist = [whitelist]
    counter = 0
    if re.match(r"(https:\/\/www\.ticketmaster\.)(?P<domain>(?:co|com)\.)?(?P<country>\w{2})\/(?P<event>event)\/(?P<name>.*)\/(?P<last_code>[0-9]+)", link):
        for i in range(1, 55, 1):
            if counter > 5: break
            value = offset(link, whitelist, price, quantity, name, date, city, driver, i=i)
            if value == False: counter+=1
            elif value == '403' and proxy == 'vpn': reconnect_vpn(driver)

    elif not whitelist and re.match(r"(https:\/\/www\.ticketmaster\.)(?P<domain>(?:co|com)\.)?(?P<country>\w{2})\/(?P<name>.*)\/(?P<event>event)\/(?P<last_code>[A-Z0-9]+)", link):
        value = offset(link, whitelist, price, quantity, name, date, driver, city)
        if value == '403' and proxy == 'vpn': reconnect_vpn(driver)

    elif whitelist and re.match(r"(https:\/\/www\.ticketmaster\.)(?P<domain>(?:co|com)\.)?(?P<country>\w{2})\/(?P<name>.*)\/(?P<event>event)\/(?P<last_code>[A-Z0-9]+)", link):
        for i in range(0, 101, 20):
            if counter > 5: break
            value = offset(link, whitelist, price, quantity, name, date, city, driver, i=i)
            if value == False: counter+=1
            elif value == '403' and proxy == 'vpn': reconnect_vpn(driver)
    
    else:
        print(link + "\n" +"Були передані невірні дані в таблицю.")


def main():
    sheets_link = input('Enter googlesheets link: ')
    sheets_id = sheets_link.split('/d/')[1].split('/')[0]
    
    rows = get_data_from_google_sheets("A1:H", sheets_id)
    proxy = rows[0][7] if rows and len(rows[0]) >= 8 else ''

    # Initialize driver based on proxy value
    driver = selenium_connect(proxy)
    if proxy == 'vpn':
        reconnect_vpn(driver)

    while True:
        rows = get_data_from_google_sheets("A1:H", sheets_id)
        for row in rows:
            print(row)
            whitelist, quantity, price, link, name, date, city, _ = row
            if not link:
                break
            data = [whitelist, price, quantity, link, name, date, city, proxy]
            process_row(driver, data)
        

if __name__ == "__main__":
    main()

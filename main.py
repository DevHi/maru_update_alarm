from selenium import webdriver
import getpass
import requests
from bs4 import BeautifulSoup as bs
import os
import time
import json
import re
import codecs
import smtplib
from sys import exit
from email.mime.text import MIMEText
from email.header import Header


def main():  # main
    print(alert_info() + 'Manga Update Alarm v0.0.1')
    cur_dir = os.path.realpath(os.path.dirname(__file__))
    print(alert_info() + 'Loading properties...')
    settings = properties(cur_dir)
    print(alert_info() + 'Initialising PhantomJS...')
    driver_dir = settings['PhantomJS_directory']
    url = 'http://marumaru.in/b/mangaup'
    if driver_dir == '':
        driver_dir = cur_dir + '\\phantomjs\\bin\\phantomjs.exe'
        driver = phantomjs_starter(driver_dir)
    else:
        driver = phantomjs_starter(driver_dir)
    print(alert_info() + 'Connecting to {}...'.format(url))
    rcode = url_request(url)
    if rcode == 200:
        print(alert_info() + 'Connection Successful!')
        lastlogin = maru_login(driver, url, settings, cur_dir)
    else:
        print(alert_error() + 'Connection Failed (code: {}). Please restart the program.'.format(rcode))
        exit()
    email = email_login(settings)
    t = settings['update_check_interval_in_second']
    while 1:
        update_checker(driver, url, email, settings, lastlogin, cur_dir)
        print(alert_info() + "Next update check in {} second(s).".format(t))
        time.sleep(t)


def alert_info():  # Prefix format for information messages
    return '[INFO][{}] '.format(timer())


def alert_error():  # Prefix format for error messages
    return '[ERROR][{}] '.format(timer())


def timer():  # Time prefix format for messages
    t = time.localtime()
    return time.strftime('%Y-%m-%d %H:%M:%S', t)


def properties(file_dir):  # Load/create properties file
    try:
        settings = open(file_dir + "\\properties.json", 'r')
        data = settings.read()
        return json.loads(data)
    except FileNotFoundError:
        print(alert_info() + "Missing 'properties.json', Creating new file...")
        settings = open(file_dir + "\\properties.json", 'w')
        default_settings = {
            'maru_auto_login': False,  # Automatically log in to 'http://marumaru.in'. ( default: False )
            'maru_id': '',
            'maru_password': '',
            'email_auto_login': False,  # Automatically log in to SMTP server. ( default: False )
            'email_full_address': '',
            'email_password': '',
            'last_login': '',  # Recently logged in account
            'PhantomJS_directory': '',
            'update_check_interval_in_second': 600,  # Set update checking interval. ( default: 600(10min) )
            'use_safe_password_input': True  # Use 'getpass' when entering password. False if Windows. ( default: True )
        }
        data = json.dumps(default_settings, sort_keys=True, indent=4)
        settings.write(str(data))
        settings.close()
        return default_settings


def properties_writer(key, value, file_dir):  # Updates properties file
    try:
        settings = open(file_dir + "\\properties.json", 'r')
        data = settings.read()
        settings.close()
        settings_dict = json.loads(data)
        settings_dict[key] = value
        settings = open(file_dir + "\\properties.json", 'w')
        new_data = json.dumps(settings_dict, sort_keys=True, indent=4)
        settings.write(str(new_data))
        settings.close()
    except FileNotFoundError:
        print(alert_info() + "Missing 'properties.json', Creating new file...")
        settings = open(file_dir + "\\properties.json", 'w')
        default_settings = {
            'maru_auto_login': False,  # Automatically log in to 'http://marumaru.in'. ( default: False )
            'maru_id': '',
            'maru_password': '',
            'email_auto_login': False,  # Automatically log in to SMTP server. ( default: False )
            'email_full_address': '',
            'email_password': '',
            'last_login': '',  # Recently logged in account
            'PhantomJS_directory': '',
            'update_check_interval_in_second': 600,  # Set update checking interval. ( default: 600(10min) )
            'use_safe_password_input': True  # Use 'getpass' when entering password. False if Windows. ( default: True )
        }
        data = json.dumps(default_settings, sort_keys=True, indent=4)
        settings.write(str(data))
        settings.close()


def phantomjs_starter(driver_dir):  # PhantomJS initiator
    try:
        driver = webdriver.PhantomJS(driver_dir)
        return driver
    except:
        print(alert_error() + 'Unable to load PhantomJS.')
        print(alert_error() + "Please specify the location of PhantomJS in 'properties.json', then restart the program.")
        return exit()


def url_request(url):  # Check website's status
    try:
        r = requests.get(url)
        return r.status_code
    except ConnectionError:
        print(alert_error() + 'Please check your Internet connectivity, then restart the program.')
        return exit()


def get_html(driver):  # Get current page's html, convert into BeautifulSoup object
    soup = bs(driver.page_source, 'lxml')
    return soup


def maru_login(driver, url, settings, cur_dir, stat=True):  # Log in to 'http://marumaru.in/'
    print(alert_info() + "Log in to 'http://marumaru.in'")
    if stat is True:
        if settings['maru_auto_login'] is True:
            print(alert_info() + 'Auto log in enabled.')
            maru_id = settings['maru_id']
            maru_pw = settings['maru_password']
        else:
            maru_id = input('ID: ')
            if settings['use_safe_password_input'] is True:
                maru_pw = getpass.getpass('Password: ')
            else:
                maru_pw = input('Password: ')
    else:
        maru_id = input('ID: ')
        if settings['use_safe_password_input'] is True:
            maru_pw = getpass.getpass('Password: ')
        else:
            maru_pw = input('Password: ')
    print(alert_info() + 'Logging in...')
    driver.get(url)
    try:
        driver.find_element_by_name('id').send_keys(maru_id)
        driver.find_element_by_name('pw').send_keys(maru_pw)
        driver.find_element_by_class_name('submit').click()
    except:
        print(alert_error() + 'PhantomJS error. Please restart the program.')
        return exit()

    if get_html(driver).select('div[class=login] a')[0].text == '나의계정':
        print(alert_info() + 'Successfully logged in.')
    elif get_html(driver).select('div[class=login] a')[0].text == '회원가입':
        print(alert_error() + 'Log in failed.')
        maru_login(driver, url, settings, cur_dir, stat=False)

    if settings['last_login'] == '':
        properties_writer('last_login', maru_id, cur_dir)
        return 'first_login', maru_id
    elif settings['last_login'] == maru_id:
        return 'same_user', maru_id
    else:
        properties_writer('last_login', maru_id, cur_dir)
        return 'different_user', maru_id


def load_bookmark(driver):  # Load bookmark
    print(alert_info() + 'Loading bookmarks...')
    driver.get('http://marumaru.in/switchs/foot/bookmark/load.php')
    bookmark_list = get_html(driver).select('body')[0].text
    return list(json.loads(bookmark_list).keys())


def update_list_creator(driver):  # Get manga update list from 'http://marumaru.in/b/mangaup'
    update_raw = get_html(driver).select('#boardList table tbody tr[cid] div[cid]')
    update_link_raw = get_html(driver).select('#boardList table tbody tr[cid] a')
    update_titles = []
    for i in range(len(update_raw)):
        update_titles.append(re.search('[\t]{4}(.*)[\t]{4}', update_raw[i].text).group(1))
    update_dates_links = []
    for j in range(len(update_raw)):
        date_raw = re.search('[\t]{5}(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2})', update_raw[j].text).group(1)
        date = re.search('(\d{4})\.(\d{2})\.(\d{2}) (\d{2}):(\d{2})', date_raw)
        date_converted = time.mktime((int(date.group(1)), int(date.group(2)), int(date.group(3)), int(date.group(4)), int(date.group(5)), 0, 0, 0, 0))
        link = 'http://marumaru.in' + update_link_raw[j].get('href')
        update_dates_links.append((date_converted, link))
    return dict(zip(update_titles, update_dates_links))


def last_update_reader(bookmark, lastlogin, cur_dir):  # Get last update date log
    try:
        last_update = open(cur_dir + '\\lastupdate_{}.json'.format(lastlogin[1]), 'r', encoding='utf8')
        file_data = last_update.read()
        last_update.close()
        data = json.loads(file_data)
        temp_date = []
        for i in range(len(bookmark)):
            temp_date.append(0)
        new_data = dict(zip(bookmark, temp_date))
        for key in data.keys():
            try:
                new_data[key] = data[key]
            except KeyError:
                del new_data[key]
        last_update = codecs.open(cur_dir + '\\lastupdate_{}.json'.format(lastlogin[1]), 'w', 'utf-8')
        last_update.write(str(json.dumps(new_data, ensure_ascii=False, sort_keys=True, indent=4)))
        last_update.close()
        return new_data
    except FileNotFoundError:
        print(alert_info() + "Missing 'lastupdate_{}.json', Creating new file...".format(lastlogin[1]))
        temp_date = []
        for i in range(len(bookmark)):
            temp_date.append(0)
        data = dict(zip(bookmark, temp_date))
        last_update = codecs.open(cur_dir + '\\lastupdate_{}.json'.format(lastlogin[1]), 'w', 'utf-8')
        last_update.write(str(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=4)))
        last_update.close()
        return data


def last_update_writer(update_list, lastlogin, cur_dir):  # Create last update date log
    last_update = codecs.open(cur_dir + '\\lastupdate_{}.json'.format(lastlogin[1]), 'w', 'utf-8')
    last_update.write(str(update_list))
    last_update.close()


def email_login(settings, stat=True):  # Get SMTP server log in info
    print(alert_info() + 'Log in to SMTP server')
    if stat is True:
        if settings['email_auto_login'] is True:
            print(alert_info() + 'Auto log in enabled.')
            email = settings['email_full_address']
            email_pw = settings['email_password']
        else:
            email = input('Enter email address: ')
            if settings['use_safe_password_input'] is True:
                email_pw = getpass.getpass('Enter email password: ')
            else:
                email_pw = input('Enter email password: ')
    else:
        email = input('Enter email address: ')
        if settings['use_safe_password_input'] is True:
            email_pw = getpass.getpass('Enter email password: ')
        else:
            email_pw = input('Enter email password: ')
    return email, email_pw


def email_sender(email, update_list, settings):  # Send email notification
    smtp_info = {
        'gmail.com': ('smtp.gmail.com', 587),
        'naver.com': ('smtp.naver.com', 587),
        'hanmail.net': ('smtp.hanmail.net', 465),
        'nate.com': ('smtp.mail.nate.com', 465),
        'hotmail.com': ('smtp-mail.outlook.com', 587),
        'outlook.com': ('smtp-mail.outlook.com', 587),
        'yahoo.com': ('smtp.mail.yahoo.com', 587),
    }
    host = email[0].split('@')[1]
    try:
        smtp_server, port = smtp_info[host]
    except:
        print(alert_error() + "Invalid host. '{}'".format(host))
        print(alert_error() + 'Please check your email address, then restart the program.')
        return exit()

    if port == 465:
        smtp = smtplib.SMTP_SSL(smtp_server, port)
        rcode1, _ = smtp.ehlo()
        rcode2 = 220
    elif port == 587:
        smtp = smtplib.SMTP(smtp_server, port)
        rcode1, _ = smtp.ehlo()
        rcode2, _ = smtp.starttls()
    else:
        print(alert_error() + 'Error sending notification: Port {} not supported.'.format(port))
        print(alert_error() + 'Please check your email address, then restart the program.')
        return exit()

    if rcode1 != 250:
        smtp.quit()
        print(alert_error() + 'Error sending notification: Connection ehlo() failed.')
        return email_sender(email, update_list, settings)
    if rcode2 != 220:
        smtp.quit()
        print(alert_error() + 'Error sending notification: Starttls() failed.')
        return email_sender(email, update_list, settings)

    try:
        rcode3, _ = smtp.login(email[0], email[1])
        if rcode3 != 235:
            smtp.quit()
            print(alert_error() + 'Error sending notification: Login failed.')
            new_email = email_login(settings, stat=False)
            return email_sender(new_email, update_list, settings)
    except:
        smtp.quit()
        print(alert_error() + 'Error sending notification: Login failed.')
        print(alert_error() + 'Please check your email address and password, then restart the program.')
        return exit()

    if len(update_list) == 1:
        subject = "'{}' - update notification".format(update_list[0][0])
    else:
        subject = "'{}' and {} more.. - update notification".format(update_list[0][0], len(update_list) - 1)
    message = ''
    for t in update_list:
        message += '''There is a new update for '{}'!
Link -> {}

'''.format(re.search('(.*) \d*-?\d*[화권]?', t[0]).group(1), t[1])

    msg = MIMEText(message.encode('utf-8'), _subtype='plain', _charset='utf-8')
    msg['Subject'] = Header(subject.encode('utf-8'), 'utf-8')
    msg['From'] = email[0]
    msg['To'] = email[0]

    smtp.sendmail(email[0], email[0], msg.as_string())
    smtp.quit()


def update_checker(driver, url, email, settings, lastlogin, cur_dir):  # Check new updates
    bookmark = load_bookmark(driver)
    print(alert_info() + 'Bookmark loaded.')
    print(alert_info() + 'Checking updates...')
    driver.get(url)
    update_list = update_list_creator(driver)
    new_update_list = last_update_reader(bookmark, lastlogin, cur_dir)
    message_update_list = []
    for title_raw in update_list.keys():
        title = re.search('(.*) \d*-?\d*[화권]?', title_raw).group(1)
        if title in bookmark:
            if update_list[title_raw][0] != new_update_list[title]:
                new_update_list[title] = update_list[title_raw][0]
                print(alert_info() + "New update found! '{}'".format(title_raw))
                message_update_list.append((title_raw, update_list[title_raw][1]))
            else:
                print(alert_info() + 'No update found for {}'.format(title))
    last_update_writer(json.dumps(new_update_list, ensure_ascii=False, sort_keys=True, indent=4), lastlogin, cur_dir)
    if len(message_update_list) > 0:
        print(alert_info() + "Sending notification to '{}'...".format(email[0]))
        email_sender(email, message_update_list, settings)


if __name__ == '__main__':
    main()


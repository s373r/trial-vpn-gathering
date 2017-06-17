# -*- coding: utf-8 -*-

__author__ = "s373r"

import os
import platform
import subprocess
import time
from datetime import datetime
from pathlib import Path

import unittest
import requests
import wget
import urllib
from zipfile import ZipFile

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

virtualenv_root_path = None
config_dir_relative_path = 'etc/safervpn'


def get_config_dir():
    global virtualenv_root_path, config_dir_relative_path
    return virtualenv_root_path / config_dir_relative_path


class WaitingDriver(webdriver.Chrome):
    def __init__(self, *args, **kwargs):
        super(WaitingDriver, self).__init__(*args, **kwargs)

        self._wait_timeout = 30

        self.implicitly_wait(self._wait_timeout)
        self.set_page_load_timeout(self._wait_timeout)

        self.delete_all_cookies()

    def _wait_element(self, by, value, wait_timeout):
        if wait_timeout is None:
            wait_timeout = self._wait_timeout
        return WebDriverWait(self, wait_timeout).until(ec.visibility_of_element_located((by, value)))

    def wait_element_by_class(self, value, wait_timeout=None):
        return self._wait_element(By.CLASS_NAME, value, wait_timeout)

    def wait_element_by_id(self, value, wait_timeout=None):
        return self._wait_element(By.ID, value, wait_timeout)

    def wait_element_by_partial_link_text(self, value, wait_timeout=None):
        return self._wait_element(By.PARTIAL_LINK_TEXT, value, wait_timeout)

    def wait_element_by_xpath(self, value, wait_timeout=None):
        return self._wait_element(By.XPATH, value, wait_timeout)


class Test01VirtualenvCheck(unittest.TestCase):
    def test(self):
        if 'VIRTUAL_ENV' not in os.environ:
            self.fail('activate virtualenv first')

        global virtualenv_root_path
        virtualenv_root_path = Path(os.environ['VIRTUAL_ENV'])
        if not virtualenv_root_path.is_dir():
            self.fail('the VIRTUAL_ENV variable isn\'t dir')


class Test02DownloadLatestChromeDriver(unittest.TestCase):
    def test(self):
        global virtualenv_root_path
        path_to_bin = virtualenv_root_path / 'bin'
        path_to_driver = path_to_bin / 'chromedriver'
        if path_to_driver.exists():
            self.skipTest('driver exists')

        self.assertEqual(platform.system(), 'Linux')

        if platform.machine() == 'i386':
            chrome_driver_bits = '32'
        elif platform.machine() == 'x86_64':
            chrome_driver_bits = '64'
        else:
            self.fail('unsupported architecture: ' + platform.machine())

        version_request = requests.get('https://chromedriver.storage.googleapis.com/LATEST_RELEASE')
        self.assertEqual(version_request.status_code, 200)
        latest_version = version_request.text.strip()

        driver_archive_filename = 'chromedriver_linux' + chrome_driver_bits + '.zip'
        driver_url = 'https://chromedriver.storage.googleapis.com/' + \
                     latest_version + '/' + driver_archive_filename

        if os.path.exists(driver_archive_filename):
            os.remove(driver_archive_filename)
        wget.download(driver_url, driver_archive_filename)

        zipped_driver = ZipFile(driver_archive_filename)
        zipped_driver.extractall(str(path_to_bin))
        self.assertTrue(path_to_driver.exists())

        subprocess.call(['chmod', '+x', str(path_to_driver)])


class Test03SaferVPNGathering(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(Test03SaferVPNGathering, self).__init__(*args, **kwargs)

        self._generated_email = ''
        self._password = 'qwerty123456'
        self._credentials = None

    def _is_actual_credentials(self):
        if not self._credentials.exists():
            return

        credentials_creation_mtime = os.path.getmtime(str(self._credentials))
        time_from_the_creation = datetime.now() - datetime.fromtimestamp(credentials_creation_mtime)
        return time_from_the_creation.days == 0

    def _write_credentials_to_file(self):
        with open(str(self._credentials), 'w') as credentials_file:
            for line in [self._generated_email, self._password]:
                credentials_file.writelines([line, '\n'])

    def setUp(self):
        config_dir = get_config_dir()
        # todo delete this checking on the Python3 migration, because 'exist_ok' will be provided
        if not config_dir.exists():
            config_dir.mkdir(parents=True)

        self._credentials = config_dir / 'credentials.txt'
        if self._is_actual_credentials():
            self.skipTest('actual trial credentials')

        self.driver_dropmailme = WaitingDriver()
        self.driver_safervpn = WaitingDriver()

        for driver, url in [(self.driver_dropmailme, 'https://dropmail.me/'),
                            (self.driver_safervpn, 'https://www.safervpn.com/en/vpn-free-trial')]:
            driver.implicitly_wait(30)
            driver.set_page_load_timeout(10)
            driver.delete_all_cookies()
            try:
                driver.get(url)
            except TimeoutException:
                pass

    def test(self):
        driver_dropmailme = self.driver_dropmailme
        driver_safervpn = self.driver_safervpn

        time.sleep(1)

        generated_email_element = driver_dropmailme.wait_element_by_class('email', 30)
        self._generated_email = generated_email_element.text

        email_input_element = driver_safervpn.wait_element_by_id('email')
        email_input_element.send_keys(self._generated_email)

        password_input_element = driver_safervpn.wait_element_by_id('password')
        password_input_element.send_keys(self._password)
        try:
            password_input_element.send_keys(Keys.RETURN)
        except TimeoutException:
            pass

        thanks_header_element = driver_safervpn.wait_element_by_xpath('//*[@id="signup"]/section[1]/div/div/div/h1')
        self.assertEqual(thanks_header_element.text, 'Thanks for signing up!')
        driver_safervpn.quit()

        activate_link_element = driver_dropmailme.wait_element_by_partial_link_text('members/activate', 30)
        activate_link_element.click()

        driver_dropmailme.switch_to.window(driver_dropmailme.window_handles[-1])

        welcome_header_element = driver_dropmailme.wait_element_by_xpath('//*[@id="welcome-popup"]/h2', 30)
        self.assertEqual(welcome_header_element.text, 'Welcome to SaferVPN!')

        close_popup_element = driver_dropmailme.wait_element_by_xpath('//*[@id="welcome-popup"]/button')
        close_popup_element.click()

        confirm_message_element = driver_dropmailme.wait_element_by_xpath('/html/body/div[1]/div[2]/strong')
        self.assertEqual(confirm_message_element.text, 'Your free trial account has been successfuly activated')

        self._write_credentials_to_file()

    def tearDown(self):
        for driver in [self.driver_dropmailme, self.driver_safervpn]:
            driver.quit()


class Test04DownloadConfigurationFiles(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(Test04DownloadConfigurationFiles, self).__init__(*args, **kwargs)

        ca_url = 'https://www.safervpn.com/files/openvpnconfigs/safervpn.com.ca.crt'
        ca_filename = os.path.basename(ca_url)

        self._files = dict()
        self._files[ca_filename] = ca_url

        url_prefix = 'https://www.safervpn.com/dlovpn?f=udp%2F'
        countries = [
            'Australia',
            'Brazil',
            'Germany',
            'Hong Kong',
            'Japan',
            'Poland',
            'Russia',
            'Switzerland',
            'US East',
            'US West'
        ]
        ovpn_config_extension = '.ovpn'
        for country in countries:
            ovpn_config_filename = country + ovpn_config_extension
            ovpn_config_url = url_prefix + urllib.quote(ovpn_config_filename)
            self._files[ovpn_config_filename] = ovpn_config_url

    def test(self):
        config_dir = get_config_dir()
        skip_count = 0
        # todo add skip like in Test02DownloadLatestChromeDriver
        for filename, url in self._files.iteritems():
            file_path = config_dir / filename
            if file_path.exists():
                skip_count += 1
                continue
            wget.download(url, str(file_path))

        if skip_count == len(self._files):
            self.skipTest('all config files are existed')

if __name__ == '__main__':
    unittest.main(verbosity=2, failfast=True)

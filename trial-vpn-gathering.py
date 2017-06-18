# -*- coding: utf-8 -*-

__author__ = "s373r"

import os
import platform
import subprocess
import time
import sys
import uuid
from datetime import datetime
from string import Template
from pathlib import Path

import unittest
import requests
import wget
from zipfile import ZipFile

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


class Global:
    def __init__(self):
        self._virtualenv_root_path = None
        self._generated_email = None
        self._password = 'qwerty123456'

    @property
    def generated_email(self):
        return self._generated_email

    @property
    def virtualenv_root_dir(self):
        return self._virtualenv_root_path

    @property
    def password(self):
        return self._password

    def get_config_dir(self):
        return self.virtualenv_root_path / 'etc' / 'safervpn'


g = Global()


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

        virtualenv_root_path = Path(os.environ['VIRTUAL_ENV'])
        if not virtualenv_root_path.is_dir():
            self.fail('the VIRTUAL_ENV variable isn\'t dir')
        g.virtualenv_root_path = virtualenv_root_path


class Test02DownloadLatestChromeDriver(unittest.TestCase):
    def test(self):
        path_to_bin = g.virtualenv_root_path / 'bin'
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

        self._credentials = None

    def _is_actual_credentials(self):
        if not self._credentials.exists():
            return

        credentials_creation_mtime = os.path.getmtime(str(self._credentials))
        time_from_the_creation = datetime.now() - datetime.fromtimestamp(credentials_creation_mtime)
        return time_from_the_creation.days == 0

    def setUp(self):
        config_dir = g.get_config_dir()
        # todo delete this checking on the Python3 migration, because 'exist_ok' will be provided
        if not config_dir.exists():
            config_dir.mkdir(parents=True)

        self._credentials = config_dir / 'credentials.txt'
        if self._is_actual_credentials():
            with open(str(self._credentials), 'r') as credentials_file:
                credentials = credentials_file.readlines()
                g.generated_email = credentials[0]
                g.password = credentials[1]
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
        g.generated_email = generated_email_element.text

        email_input_element = driver_safervpn.wait_element_by_id('email')
        email_input_element.send_keys(g.generated_email)

        password_input_element = driver_safervpn.wait_element_by_id('password')
        password_input_element.send_keys(g.password)
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

        with open(str(self._credentials), 'w') as credentials_file:
            for line in [g.generated_email, g.password]:
                credentials_file.writelines([line, '\n'])

    def tearDown(self):
        for driver in [self.driver_dropmailme, self.driver_safervpn]:
            driver.quit()


class Test04DownloadCA(unittest.TestCase):
    def test(self):
        file_name = 'safervpn.com.ca.crt'
        ca_file_dir = g.virtualenv_root_path / 'etc' / 'openvpn'
        # todo delete this checking on the Python3 migration, because 'exist_ok' will be provided
        if not ca_file_dir.exists():
            ca_file_dir.mkdir(parents=True)

        ca_file_path = ca_file_dir / file_name
        # todo add skip like in Test02DownloadLatestChromeDriver
        if ca_file_path.exists():
            self.skipTest('{} is existed'.format(file_name))

        ca_url = 'https://www.safervpn.com/files/openvpnconfigs/safervpn.com.ca.crt'

        wget.download(ca_url, str(ca_file_path))


class Test05CreateConnectionFiles(unittest.TestCase):
    def setUp(self):
        # todo add real gathering from https://www.safervpn.com/support/articles/213994925-SaferVPN-server-list
        self.countries = {
            'Australia':   'au1.safervpn.com:1194',
            'Brazil':      'br1.safervpn.com:1194',
            'Germany':     'de1.safervpn.com:1194',
            'Hong Kong':   'hk1.safervpn.com:1194',
            'Japan':       'jp1.safervpn.com:1194',
            'Poland':      'pl1.safervpn.com:1194',
            'Russia':      'ru1.safervpn.com:1194',
            'Switzerland': 'ch1.safervpn.com:1194',
            'US East':     'us1.safervpn.com:1194',
            'US West':     'us2.safervpn.com:1194'
        }

    def test(self):
        connections_dir = g.virtualenv_root_path / 'etc' / 'NetworkManager' / 'system-connections'
        # todo delete this checking on the Python3 migration, because 'exist_ok' will be provided
        if not connections_dir.exists():
            connections_dir.mkdir(parents=True)

        current_file = Path(sys.argv[0])
        template_file_path = current_file.parent / 'data' / 'connection-template.txt'

        with open(str(template_file_path), 'r') as template_file:
            connection_template = Template(template_file.read())
            template_params = {
                'username': g.generated_email.strip(),
                'password': g.password.strip(),
            }

            for country_name, remote in self.countries.iteritems():
                country_connection_file_path = connections_dir / 'trial-{}'.format(country_name)

                template_params['id'] = country_name
                template_params['connection_uuid'] = str(uuid.uuid4())
                template_params['remote'] = remote

                with open(str(country_connection_file_path), 'w') as country_connection_file:
                    country_connection_file.write(connection_template.safe_substitute(template_params))

if __name__ == '__main__':
    unittest.main(verbosity=2, failfast=True)

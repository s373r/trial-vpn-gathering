# -*- coding: utf-8 -*-

__author__ = "s373r"

import os
import platform
import subprocess
import time

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


class DownloadLatestChromeDriver(unittest.TestCase):

    def test(self):
        if 'VIRTUAL_ENV' not in os.environ:
            self.fail('activate virtualenv first')

        path_to_bin = os.environ['VIRTUAL_ENV'] + '/bin'
        path_to_driver = path_to_bin + '/chromedriver'
        if os.path.exists(path_to_driver):
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

        filename = 'chromedriver_linux' + chrome_driver_bits + '.zip'
        driver_url = 'https://chromedriver.storage.googleapis.com/' + \
                     latest_version + '/' + filename

        if os.path.exists(filename):
            os.remove(filename)
        wget.download(driver_url, filename)

        zipped_driver = ZipFile(filename)
        zipped_driver.extractall(path_to_bin)
        self.assertTrue(os.path.exists(filename))
        if os.path.exists(filename):
            os.remove(filename)

        subprocess.call(['chmod', '+x', path_to_driver])


class SaferVPNGathering(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(SaferVPNGathering, self).__init__(*args, **kwargs)

        self._generated_email = None
        self._password = 'qwerty123456'

    def setUp(self):
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

        with open('credentials.txt', 'w') as file:
            for line in [self._generated_email, self._password]:
                file.writelines([line, '\n'])

    def tearDown(self):
        for driver in [self.driver_dropmailme, self.driver_safervpn]:
            driver.quit()


if __name__ == '__main__':
    unittest.main(verbosity=2, failfast=True)

from datetime import date, datetime
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.test import TestCase
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time

from rse.models import *
from rse.tests.test_random_data import random_project_and_allocation_data
from django.conf import settings

from django.contrib.auth import (
    SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY,
)

from django.contrib.sessions.backends.db import SessionStore

class TemplateTests(LiveServerTestCase):
    """
    Tests using Selenium to check for HTML and JS errors
    These are not proper view tests as they do not check the view logic but could be extended to do so!
    """
    
    def setUp(self):
        # setup selenium
        chrome_options = Options()  
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])   # suppress loggin message

        # set logging capabilities to capture js errors
        d = DesiredCapabilities.CHROME
        d['goog:loggingPrefs'] = { 'browser':'ALL' }

        # start the driver
        self.selenium = webdriver.Chrome(chrome_options=chrome_options, desired_capabilities=d)
        
        # create test data
        random_project_and_allocation_data()

        # create an admin user
        user = User.objects.create_superuser(username='paul', email='admin@rseadmin.com', password='test', first_name="Paul", last_name="Richmond")
        

        
    def tearDown(self):
        # Bug with ConnectionResetError on Windows 10 non of the following Stack Overflow suggestions help!
        #self.selenium.implicitly_wait(10)
        #self.selenium.refresh()
        #time.sleep(30)
        self.selenium.quit()
        # Errors from the above call seem to only occur on Windows but do not prevent the tests from running!

        super(TemplateTests, self).tearDown()
        

    def check_for_js_errors(self):
        for entry in self.selenium.get_log('browser'):
            # Any severe js errors should cause test to fail
            self.assertNotEqual(entry['level'], 'SEVERE')
            #logger.warning(f"SEVERE LOG ERROR: {entry['message']}")
            
    def test_homepage_login(self):
        """
        Tests the homepage to check for login redirect
        """
        self.selenium.get(f"{self.live_server_url}{reverse_lazy('index')}")
        expected = "RSE Group Administration Tool Login Required"
        self.assertEqual(self.selenium.title, expected)

        # check for javascript errors in log
        self.check_for_js_errors()

    def test_homepage_admin(self):
        """
        Tests the homepage to check for admin homepage (with login)
        """
        
        # test url
        url = f"{self.live_server_url}{reverse_lazy('index')}"

        # set authentication cookie (for admin user)
        self.client.login(username='paul', password='test')
        cookie = self.client.cookies['sessionid']
        self.selenium.get(url)
        self.selenium.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()
        self.selenium.get(url)

        # check for javascript errors in log
        self.check_for_js_errors()

        # expected title
        expected = "RSE Group Administration Homepage"
        self.assertEqual(self.selenium.title, expected)
        

    def test_homepage_rse(self):
        """
        Tests the homepage to check for admin homepage (with login)
        """
        
        # test url
        url = f"{self.live_server_url}{reverse_lazy('index')}"

        # set authentication cookie (for rse user)
        self.client.login(username='user2', password='12345')
        cookie = self.client.cookies['sessionid']
        self.selenium.get(url)
        self.selenium.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()
        self.selenium.get(url)

        # check for javascript errors in log
        self.check_for_js_errors()

        # expected title
        expected = "RSE Group Administration Kermit Morse Homepage"
        self.assertEqual(self.selenium.title, expected)            


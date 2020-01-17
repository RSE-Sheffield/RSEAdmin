from datetime import date, datetime
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.test import TestCase
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.firefox.options import Options
import time
from rse.models import *
from rse.tests.test_random_data import random_project_and_allocation_data
from django.conf import settings

from django.contrib.auth import (
    SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY,
)

from django.contrib.sessions.backends.db import SessionStore

class SeleniumTemplateTest(LiveServerTestCase):
    """
    Tests using Selenium to check for HTML and Log errors
    These are not proper view tests as they do not check the view logic but could be extended to do so!
    They do however test for the correct title response and as such will catch any view or permission errors
    """

    PAGE_TITLE_LOGIN = "RSE Group Administration Tool: Login Required"

    def __init__(self, *args, **kwargs):
        """ Override init to provide a flag for blank database initialisation """

        self.blank_db = kwargs.pop('blank_db', False)

        # call the super
        super(SeleniumTemplateTest, self).__init__(*args, **kwargs)

    
    def setUp(self):
        """
        Setup the chrome driver for tests
        """
        super(SeleniumTemplateTest, self).setUp()
        

        #generic options
        driver_options = Options()  
        driver_options.add_argument("--headless")

        # Setup chrome driver (currently replaced with gecko firefox driver)
        # driver_options.add_argument("--disable-gpu")
        # driver_options.add_experimental_option('excludeSwitches', ['enable-logging'])   # suppress loggin message
        # d = DesiredCapabilities.CHROME
        # d['goog:loggingPrefs'] = { 'browser':'ALL' }
        # # start the chrome driver
        # self.selenium = webdriver.Chrome(chrome_options=driver_options, desired_capabilities=d)


        # setup firefox driver
        d = DesiredCapabilities.FIREFOX
        d['loggingPrefs'] = { 'browser':'ALL' }
        self.selenium = webdriver.Firefox(firefox_options=driver_options, desired_capabilities=d)

        # create test data 
        if not self.blank_db:
            random_project_and_allocation_data()
        else:
            # need a single RSE user to view pages
            u = User.objects.create_user(username='user2', email='rse@rseadmin.com', password='12345', first_name="RSE", last_name="Person")
            rse = RSE(user=u)
            rse.employed_until = date(2025, 1, 1)
            rse.save()

        # create an admin user
        self.admin_user = User.objects.create_superuser(username='paul', email='admin@rseadmin.com', password='test', first_name="Paul", last_name="Richmond")



        
    def tearDown(self):
        """
        Quit the chrome driver.
        There is a windows bug which gives a timeout!
        """

        # Bug with ConnectionResetError on Windows 10 non of the following Stack Overflow suggestions help!
        #self.selenium.implicitly_wait(10)
        #self.selenium.refresh()
        #time.sleep(30)
        self.selenium.quit()
        # Errors from the above call seem to only occur on Windows but do not prevent the tests from running!
        super(SeleniumTemplateTest, self).tearDown()
        
       

    def check_for_log_errors(self):
        """ 
        Check the browser driver logs for any js errors 
        The method commented out below is only available in chrome but chrome has a whole bunch of other issues....
        See: https://github.com/mozilla/geckodriver/issues/284
        Possible solution is https://github.com/hurracom/WebConsoleTap
        For now no log errors are checked
        """
        #for entry in self.selenium.get_log('browser'):
            # Any severe js errors should cause test to fail
            # self.assertNotEqual(entry['level'], 'SEVERE')
            # if entry['level'] == 'SEVERE':
            #    logger.warning(f"SEVERE LOG ERROR: {entry['message']}")

    def get_url_as_admin(self, url: str, username: str = "paul", password: str = "test"):
        """
        Calls the selenium get method and sets the state of the driver but by using an authenticated admin user (from test database)
        """
        # set authentication cookie (for admin user)
        self.client.login(username=username, password=password)
        cookie = self.client.cookies['sessionid']
        self.selenium.get(url)
        self.selenium.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()
        self.selenium.get(url)

    def get_url_as_rse(self, url: str, username: str = "user2", password: str = "12345"):
        """
        Calls the selenium get method and sets the state of the driver but by using an authenticated rse user (from test database)
        """
        # set authentication cookie (for rse user)
        self.client.login(username=username, password=password)
        cookie = self.client.cookies['sessionid']
        self.selenium.get(url)
        self.selenium.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()
        self.selenium.get(url)

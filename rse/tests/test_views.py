from datetime import date, datetime
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from rse.models import *
from rse.tests.test_random_data import *


class TemplateTests(TestCase):
    """
    Tests using Selenium to check for HTML and JS errors
    These are not proper view tests as they do not check the view logic but could be extended to do so!
    """
    
    def setUp(self):
        random_project_and_allocation_data()
        self.selenium = webdriver.Chrome()

    def tearDown(self):
        self.selenium.quit()
        super(TemplateTests, self).tearDown()
        
            
    def test_homepage_login(self):
        """
        Tests the homepage to check for login redirect
        """

        self.selenium.get(f"http://127.0.0.1:8000{reverse_lazy('index')}")
        expected = "RSE Group Administration Tool Login Required"
        self.assertEqual(self.selenium.title, expected)
        

            


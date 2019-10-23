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
        random_project_and_allocation_data()

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

########################
### Index (homepage) ###
########################

class IndexTemplateTests(SeleniumTemplateTest):


    def test_homepage_login(self):
        """
        Tests the homepage to check for login redirect
        """
        self.selenium.get(f"{self.live_server_url}{reverse_lazy('index')}")
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)

        # check for javascript errors in log
        self.check_for_log_errors()

    def test_homepage(self):
        """ Tests the homepage to check for admin homepage (with login) """
        
        # test url
        url = f"{self.live_server_url}{reverse_lazy('index')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: Admin Homepage"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view
        self.get_url_as_rse(url)
        expected = "RSE Group Administration Tool: RSE User Homepage"
        self.assertEqual(self.selenium.title, expected)   
        self.check_for_log_errors()         


#######################
### Authentication ####
#######################
class AuthenticationTemplateTests(SeleniumTemplateTest):
    
    def setUp(self):
            """
            Add a few usefull database objects for easy access
            """
            super(AuthenticationTemplateTests, self).setUp()

            # store some usefull user ids
            self.admin_user_id = self.admin_user.id
            self.first_rse_id = RSE.objects.all()[0].id
            self.first_rse_user_id = RSE.objects.all()[0].user.id

    def test_login(self):
        """ Tests the login page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('login')}"
        # test page (no authentication)
        self.selenium.get(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()

    # logout has no template

    def test_change_password(self):
        """ Tests the change_password page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('change_password')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: Change Password"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view
        self.get_url_as_rse(url)
        expected = "RSE Group Administration Tool: Change Password"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_user_new(self):
        """ Tests the user_new page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('user_new')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: New User"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()


    def test_user_new_rse(self):
        """ Tests the user_new_rse page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('user_new_rse')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: New RSE User"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()

    def test_user_edit_rse(self):
        """ Tests the user_edit_rse page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('user_edit_rse', kwargs={'rse_id': self.first_rse_id})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: Edit RSE User"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()

    def test_user_new_admin(self):
        """ Tests the user_new_admin page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('user_new_admin')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: New Admin User"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()

    def test_user_edit_admin(self):
        """ Tests the user_edit_admin page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('user_edit_admin', kwargs={'user_id': self.admin_user_id})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: Edit Admin User"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()

    def test_user_change_password(self):
        """ Tests the user_change_password page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('user_change_password', kwargs={'user_id': self.first_rse_user_id})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: Change A Users Password"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)   
        self.check_for_log_errors()  

    def test_users(self):
        """ Tests the users page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('users')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: View all Users"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()   



################################
### Projects and Allocations ###
################################

class ProjectTemplateTests(SeleniumTemplateTest):
    
    def setUp(self):
            """
            Add a few usefull database objects for easy access
            """
            super(ProjectTemplateTests, self).setUp()

            self.first_service_project = ServiceProject.objects.all()[0]
            self.first_allocated_project = AllocatedProject.objects.all()[0]
            self.first_project = Project.objects.all()[0]

    def test_projects(self):
        """ Tests the projects page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('projects')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: View Projects"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = "RSE Group Administration Tool: View Projects"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()   

    def test_project_new(self):
        """ Tests the project_new page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('project_new')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: New Project"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = "RSE Group Administration Tool: New Project"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()  

    def test_project_new_allocated(self):
        """ Tests the project_new_allocated page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('project_new_allocated')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: New Allocated Project"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = "RSE Group Administration Tool: New Allocated Project"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors() 


    def test_project_new_service(self):
        """ Tests the project_new_service page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('project_new_service')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: New Service Project"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = "RSE Group Administration Tool: New Service Project"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors() 

    def test_project(self):
        """ Tests the project page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('project', kwargs={'project_id': self.first_project.id})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: Project {self.first_project.id} Summary"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = f"RSE Group Administration Tool: Project {self.first_project.id} Summary"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors() 
        


    def test_project_edit(self):
        """ Tests the project_edit page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('project_edit', kwargs={'project_id': self.first_service_project.id})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: Edit Service Project"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = "RSE Group Administration Tool: Edit Service Project"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors() 

        # test url
        url = f"{self.live_server_url}{reverse_lazy('project_edit', kwargs={'project_id': self.first_allocated_project.id})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: Edit Allocated Project"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = "RSE Group Administration Tool: Edit Allocated Project"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors() 

    def test_project_allocations(self):
        """ Tests the project_allocations page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('project_allocations', kwargs={'project_id': self.first_project.id})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: View Project {self.first_project.id} Allocations"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors() 

    def test_project_allocations_edit(self):
        """ Tests the project_allocations_edit page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('project_allocations_edit', kwargs={'project_id': self.first_project.id})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: Edit Project {self.first_project.id} Allocations"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()


###############
### Clients ###
###############

class ClientTemplateTests(SeleniumTemplateTest):
    
    def setUp(self):
            """
            Add a few usefull database objects for easy access
            """
            super(ClientTemplateTests, self).setUp()

            self.first_client = Client.objects.all()[0]

    def test_clients(self):
        """ Tests the clients page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('clients')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: View Clients"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = "RSE Group Administration Tool: View Clients"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_client(self):
        """ Tests the client page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('client', kwargs={'client_id': self.first_client.id})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: View Client {self.first_client.id} Summary"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = f"RSE Group Administration Tool: View Client {self.first_client.id} Summary"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_client_new(self):
        """ Tests the client_new page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('client_new')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: New Client"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = f"RSE Group Administration Tool: New Client"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_client_edit(self):
        """ Tests the client_edit page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('client_edit', kwargs={'client_id': self.first_client.id})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: Edit Client"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = f"RSE Group Administration Tool: Edit Client"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()


############
### RSEs ###
############

class RSETemplateTests(SeleniumTemplateTest):
    
    def setUp(self):
            """
            Add a few usefull database objects for easy access
            """
            super(RSETemplateTests, self).setUp()

            self.first_rse = RSE.objects.all()[0]

    def test_rse(self):
        """ Tests the rse page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('rse', kwargs={'rse_username': self.first_rse.user.username})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: {self.first_rse}"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = f"RSE Group Administration Tool: {self.first_rse}"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_rses(self):
        """ Tests the rses page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('rses')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: View RSEs"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = f"RSE Group Administration Tool: View RSEs"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_rseid(self):
        """ Tests the rseid page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('rseid', kwargs={'rse_id': self.first_rse.id})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: {self.first_rse}"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = f"RSE Group Administration Tool: {self.first_rse}"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_commitment(self):
        """ Tests the commitment page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('commitment')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: Team Commitment"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = f"RSE Group Administration Tool: Team Commitment"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_rse_salary(self):
        """ Tests the rse_salary page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('rse_salary', kwargs={'rse_username': self.first_rse.user.username})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: {self.first_rse} Salary"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_rse_salary(self):
        """ Tests the rse_salary page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('rse_salary', kwargs={'rse_username': self.first_rse.user.username})}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: {self.first_rse} Salary"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    # no test for ajax_salary_band_by_year


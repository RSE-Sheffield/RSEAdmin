from django.urls import reverse_lazy
from rse.models import *
from rse.tests.selenium_template_test import *
from .constant import *

from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By

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
        
        # Test filter inactive users
        el_with_inactive_username = self.selenium.find_elements(By.XPATH, f"//*[contains(text(), '{INACTIVE_USERNAME}')]") 
        self.assertEqual(len(el_with_inactive_username), 0)
        
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

            if ServiceProject.objects.all():
                self.first_service_project = ServiceProject.objects.all()[0]
            if DirectlyIncurredProject.objects.all():
                self.first_allocated_project = DirectlyIncurredProject.objects.all()[0]
            if Project.objects.all():
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
        
        # test admin view dropdown option
        # https://selenium-python.readthedocs.io/api.html?highlight=select#module-selenium.webdriver.support.select
        dropdown = Select(self.selenium.find_element(By.ID, 'id_type'))
        dropdown.select_by_visible_text('Service')
        dropdown.select_by_visible_text('Directly Incurred')
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = "RSE Group Administration Tool: New Project"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()  
        dropdown = Select(self.selenium.find_element(By.ID, 'id_type'))
        dropdown.select_by_visible_text('Service')
        dropdown.select_by_visible_text('Directly Incurred')

    def test_project_new_directly_incurred(self):
        """ Tests the project_new_directly_incurred page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('project_new_directly_incurred')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: New Directly Incurred Project"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = "RSE Group Administration Tool: New Directly Incurred Project"
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
        if hasattr(self, 'first_project'):
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
        if hasattr(self, 'first_service_project'):
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
        if hasattr(self, 'first_directly_incurred_project'):
            url = f"{self.live_server_url}{reverse_lazy('project_edit', kwargs={'project_id': self.first_directly_incurred_project.id})}"

            # test admin view
            self.get_url_as_admin(url)
            expected = "RSE Group Administration Tool: Edit Directly Incurred Project"
            self.assertEqual(self.selenium.title, expected)
            self.check_for_log_errors()
            
            # test rse view (login should be required)
            self.get_url_as_rse(url)
            expected = "RSE Group Administration Tool: Edit Directly Incurred Project"
            self.assertEqual(self.selenium.title, expected)  
            self.check_for_log_errors() 

    def test_project_allocations(self):
        """ Tests the project_allocations page """

        # test url
        if hasattr(self, 'first_project'):
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
        if hasattr(self, 'first_project'):
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

            if Client.objects.all():
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
        if hasattr(self, 'first_client'):
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
        if hasattr(self, 'first_client'):
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

            if RSE.objects.all():
                self.first_rse = RSE.objects.all()[0]

    def test_rse(self):
        """ Tests the rse page """

        # test url
        if hasattr(self, 'first_rse'):
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
        if hasattr(self, 'first_rse'):
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
        if hasattr(self, 'first_rse'):
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

#################################
### Salary and Grade Changes ####
#################################

class SalaryTemplateTests(SeleniumTemplateTest):
    
    def setUp(self):
            """
            Add a few usefull database objects for easy access
            """
            super(SalaryTemplateTests, self).setUp()

            if FinancialYear.objects.all():
                self.first_financial_year = FinancialYear.objects.all()[0]
            if SalaryBand.objects.all():
                self.first_salary_band = SalaryBand.objects.all()[0]

    def test_financialyears(self):
        """ Tests the financialyears page """

        # test url
        if hasattr(self, 'first_financial_year'):
            url = f"{self.live_server_url}{reverse_lazy('financialyears')}?year={self.first_financial_year}"

            # test admin view
            self.get_url_as_admin(url)
            expected = f"RSE Group Administration Tool: View {self.first_financial_year} Financial Year"
            self.assertEqual(self.selenium.title, expected)
            self.check_for_log_errors()
            
            # test rse view (login should be required)
            self.get_url_as_rse(url)
            expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
            self.assertEqual(self.selenium.title, expected)  
            self.check_for_log_errors()

    def test_financialyear_edit(self):
        """ Tests the financialyear_edit page """

        # test url
        if hasattr(self, 'first_financial_year'):
            url = f"{self.live_server_url}{reverse_lazy('financialyear_edit', kwargs={'year_id': self.first_financial_year.year})}"

            # test admin view
            self.get_url_as_admin(url)
            expected = f"RSE Group Administration Tool: Edit {self.first_financial_year} Financial Year"
            self.assertEqual(self.selenium.title, expected)
            self.check_for_log_errors()
            
            # test rse view (login should be required)
            self.get_url_as_rse(url)
            expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
            self.assertEqual(self.selenium.title, expected)  
            self.check_for_log_errors()

    def test_financialyear_new(self):
        """ Tests the financialyear_new page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('financialyear_new')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: New Financial Year"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_salaryband_edit(self):
        """ Tests the salaryband_edit page """

        # test url
        if hasattr(self, 'first_salary_band'):
            url = f"{self.live_server_url}{reverse_lazy('salaryband_edit', kwargs={'sb_id': self.first_salary_band.id})}"

            # test admin view
            self.get_url_as_admin(url)
            expected = f"RSE Group Administration Tool: Edit Salary Band"
            self.assertEqual(self.selenium.title, expected)
            self.check_for_log_errors()
            
            # test rse view (login should be required)
            self.get_url_as_rse(url)
            expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
            self.assertEqual(self.selenium.title, expected)  
            self.check_for_log_errors()

##################
### Reporting ####
##################

class ReportingTemplateTests(SeleniumTemplateTest):
    
    def setUp(self):
            """
            Add a few usefull database objects for easy access
            """
            super(ReportingTemplateTests, self).setUp()

            if Project.objects.all():
                self.first_project = Project.objects.all()[0]
            if RSE.objects.all():
                self.first_rse = RSE.objects.all()[0]

    def test_allocations_recent(self):
        """ Tests the allocations recent page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('allocations_recent')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: View Recent Allocation Changes"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()
    
    def test_costdistributions(self):
        """ Tests the costdistributions page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('costdistributions')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: Team Cost Distributions Today"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_costdistribution(self):
        """ Tests the costdistribution page """

        # test url
        if hasattr(self, 'first_rse'):
            url = f"{self.live_server_url}{reverse_lazy('costdistribution', kwargs={'rse_username': self.first_rse.user.username})}"

            # test admin view
            self.get_url_as_admin(url)
            expected = f"RSE Group Administration Tool: {self.first_rse} Cost Distribution"
            self.assertEqual(self.selenium.title, expected)
            self.check_for_log_errors()
            
            # test rse view (login should be required)
            self.get_url_as_rse(url)
            expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
            self.assertEqual(self.selenium.title, expected)  
            self.check_for_log_errors()

    def test_rses_staffcosts(self):
        """ Tests the rses_staffcosts page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('rses_staffcosts')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: RSE Team Staff Costs and Liability"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_rse_staffcost(self):
        """ Tests the rse_staffcost page """

        # test url
        if hasattr(self, 'first_rse'):
            url = f"{self.live_server_url}{reverse_lazy('rse_staffcost', kwargs={'rse_username': self.first_rse.user.username})}"

            # test admin view
            self.get_url_as_admin(url)
            expected = f"RSE Group Administration Tool: {self.first_rse} RSE Staff Cost and Liability"
            self.assertEqual(self.selenium.title, expected)
            self.check_for_log_errors()
            
            # test rse view (login should be required)
            self.get_url_as_rse(url)
            expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
            self.assertEqual(self.selenium.title, expected)  
            self.check_for_log_errors()

    def test_serviceoutstanding(self):
        """ Tests the serviceoutstanding page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('serviceoutstanding')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: Service Projects Invoice Status"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_serviceincome(self):
        """ Tests the serviceincome page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('serviceincome')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: Service Income"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_projects_income_summary(self):
        """ Tests the projects_income_summary page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('projects_income_summary')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: Projects Staff Cost and Overhead"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_project_staffcosts(self):
        """ Tests the project_staffcosts page """

        # test url
        if hasattr(self, 'first_project'):
            url = f"{self.live_server_url}{reverse_lazy('project_staffcosts', kwargs={'project_id': self.first_project.id})}"

            # test admin view
            self.get_url_as_admin(url)
            expected = f"RSE Group Administration Tool: Project {self.first_project.id} Staff Costs Breakdown"
            self.assertEqual(self.selenium.title, expected)
            self.check_for_log_errors()
            
            # test rse view (login should be required)
            self.get_url_as_rse(url)
            expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
            self.assertEqual(self.selenium.title, expected)  
            self.check_for_log_errors()

    # no test for AJAX project_remaining_days

    def test_projects_internal_summary(self):
        """ Tests the projects_internal_summary page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('projects_internal_summary')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: Internal Projects Staff Cost"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_financial_summary(self):
        """ Tests the financial_summary page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('financial_summary')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = f"RSE Group Administration Tool: Financial Summary"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view (login should be required)
        self.get_url_as_rse(url)
        expected = SeleniumTemplateTest.PAGE_TITLE_LOGIN
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()


############################################
# Empty database tests of all of the above #
############################################


class IndexTemplateTestsBlankDB(IndexTemplateTests):

    """ Class extends the normal set of template tests but sets a 'blank_db' parameter to test the templates with an empty database """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank_db', True)
        super(IndexTemplateTestsBlankDB, self).__init__(*args, **kwargs)


class AuthenticationTemplateTestsBlankDB(AuthenticationTemplateTests):

    """ Class extends the normal set of template tests but sets a 'blank_db' parameter to test the templates with an empty database """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank_db', True)
        super(AuthenticationTemplateTestsBlankDB, self).__init__(*args, **kwargs)

class ProjectTemplateTestsBlankDB(ProjectTemplateTests):

    """ Class extends the normal set of template tests but sets a 'blank_db' parameter to test the templates with an empty database """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank_db', True)
        super(ProjectTemplateTestsBlankDB, self).__init__(*args, **kwargs)

class ClientTemplateTestsBlankDB(ClientTemplateTests):

    """ Class extends the normal set of template tests but sets a 'blank_db' parameter to test the templates with an empty database """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank_db', True)
        super(ClientTemplateTestsBlankDB, self).__init__(*args, **kwargs)

class RSETemplateTestsBlankDB(RSETemplateTests):

    """ Class extends the normal set of template tests but sets a 'blank_db' parameter to test the templates with an empty database """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank_db', True)
        super(RSETemplateTestsBlankDB, self).__init__(*args, **kwargs)

class SalaryTemplateTestsBlankDB(SalaryTemplateTests):

    """ Class extends the normal set of template tests but sets a 'blank_db' parameter to test the templates with an empty database """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank_db', True)
        super(SalaryTemplateTestsBlankDB, self).__init__(*args, **kwargs)

class ReportingTemplateTestsBlankDB(ReportingTemplateTests):

    """ Class extends the normal set of template tests but sets a 'blank_db' parameter to test the templates with an empty database """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank_db', True)
        super(ReportingTemplateTestsBlankDB, self).__init__(*args, **kwargs)
from django.urls import reverse_lazy
from timetracking.models import *
from rse.tests.selenium_template_test import *

#######################
### Authentication ####
#######################
class TimeTrackingTemplateTests(SeleniumTemplateTest):
    
    def setUp(self):
            """
            Add a few usefull database objects for easy access
            """
            super(TimeTrackingTemplateTests, self).setUp()

            # store some usefull user ids
            self.admin_user_id = self.admin_user.id
            self.first_rse_id = RSE.objects.all()[0].id
            self.first_rse_user_id = RSE.objects.all()[0].user.id

            if Project.objects.all():
                self.first_project = Project.objects.all()[0]


    def test_timesheets(self):
        """ Tests the timesheets page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('timesheet')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: Edit Time Sheet"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view
        self.get_url_as_rse(url)
        expected = "RSE Group Administration Tool: Edit Time Sheet"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_time_projects(self):
        """ Tests the time_projects page """

        # test url
        url = f"{self.live_server_url}{reverse_lazy('time_projects')}"

        # test admin view
        self.get_url_as_admin(url)
        expected = "RSE Group Administration Tool: View Projects for Time Tracking"
        self.assertEqual(self.selenium.title, expected)
        self.check_for_log_errors()
        
        # test rse view
        self.get_url_as_rse(url)
        expected = "RSE Group Administration Tool: View Projects for Time Tracking"
        self.assertEqual(self.selenium.title, expected)  
        self.check_for_log_errors()

    def test_time_project(self):
        """ Tests the time_project page """

        if hasattr(self, 'first_project'):
            # test url
            url = f"{self.live_server_url}{reverse_lazy('time_project', kwargs={'project_id': self.first_project.id})}"

            # test admin view
            self.get_url_as_admin(url)
            expected = "RSE Group Administration Tool: View Project Time Sheet"
            self.assertEqual(self.selenium.title, expected)
            self.check_for_log_errors()
            
            # test rse view
            self.get_url_as_rse(url)
            expected = "RSE Group Administration Tool: View Project Time Sheet"
            self.assertEqual(self.selenium.title, expected)  
            self.check_for_log_errors()


############################################
# Empty database tests of all of the above #
############################################

class TimeTrackingTemplateTestsBlankDB(TimeTrackingTemplateTests):

    """ Class extends the normal set of template tests but sets a 'blank_db' parameter to test the templates with an empty database """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank_db', True)
        super(TimeTrackingTemplateTestsBlankDB, self).__init__(*args, **kwargs)

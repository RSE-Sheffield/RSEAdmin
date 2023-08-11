from datetime import date, datetime
from django.utils import timezone

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.test import TestCase

from rse.models import *
import random
from .constant import *


###########################################
# Helper functions for creating test data #
###########################################

def random_user_and_rse_data():
    """
    Function to create some random RSEs
    """
    # Create some random users and RSEs
    names = [("Tennie", "Kilroy"), 
             ("Keila", "Furlow"), 
             ("Kermit", "Morse"), 
             ("Vi", "Sautter"), 
             ("Gennie", "Crays"),
             ("Inger", "Eisenbarth"),
             ("Jeffry", "Fitzsimmons"),
             ("Cathern", "Dicarlo"),
             ("Chase", "Kovar"),
             ("Bong", "Ma")]

    # Create some random users (RSEs) 
    for i in range(10):
        u = User.objects.create_user(username=f"user{i}", password='12345', first_name=names[i][0], last_name=names[i][1])
        rse = RSE(user=u)
        rse.employed_until = date(2025, 1, 1)
        rse.save()
        
    # Create an inactive user (not currently employed)
    u = User.objects.create_user(
            username=INACTIVE_USERNAME, 
            password='12345', 
            first_name='Inactive', 
            last_name='Test', 
            is_active=False
        )
    rse = RSE(user=u)
    rse.employed_until = date(2020, 1, 1)
    rse.save()

    
def random_salary_and_banding_data():
    """
    Function to create data in test database for salary and banding
    """
    
    # create test user and rse
    random_user_and_rse_data()
    
    # Create some financial years
    y2017 = FinancialYear(year=2017)
    y2017.save()
    y2018 = FinancialYear(year=2018)
    y2018.save()
    y2019 = FinancialYear(year=2019)
    y2019.save()
    y2020 = FinancialYear(year=2020)
    y2020.save()

    # Create an incremental range (1, 2, 3) and non incremental range (4, 5) for years 2017 - 2020
    # Each year comes with grade 1 with 5 grade points.
    for year in range(2017, 2021):
        curr_year = FinancialYear(year=year)
        curr_year.save()
        
        if year == 2017:
            sb11_2017 = curr_year
        
        for grade_point in range(1, 6):
            curr_gp = SalaryBand(
                grade=1, 
                grade_point=grade_point, 
                salary=(1000 * grade_point + (year - 2017)), 
                year=curr_year, 
                increments=True if grade_point in [1, 2, 3] else False
            )
            curr_gp.save()

    # Create salary grade changes
    for r in RSE.objects.all():
        sgc1 = SalaryGradeChange(rse=r, salary_band=sb11_2017, date=sb11_2017.year.start_date())
        sgc1.save()

def random_project_and_allocation_data():
    """
    Create random client, project and allocations in test database
    """
    
    # create test salary bands from normal test data
    random_salary_and_banding_data()
    
    # get expected salary band from database
    sb15_2017 = SalaryBand.objects.get(grade=1, grade_point=5, year=2017)
    # get user from database
    user = User.objects.get(username='user0')

    # create some test projects
    for i in range(5):
        c = Client(name=f"Client {i}")
        c.department = random.choice(["COM", "ACSE", "MAT", "PSY"])
        c.save()        
        
    
    
    # Create some random projects for test database
    for x in range(20):
        proj_costing_id = random.randint(1,99999)
        start=date(random.randint(2018, 2020), random.randint(1, 12), 1)    #random month in 2017 to 2020
        # if start month is dec then end year cant start in same year
        if start.month == 12:
            end_year=random.randint(start.year+1, 2022)
        else:
            end_year=random.randint(start.year, 2022)
        # if end year is the same as start year then end month must be greater than start month
        if end_year == start.year:
            end_month = random.randint(start.month+1, 12)
        else:
            end_month = random.randint(1, 12)
        end=date(end_year, end_month, 1)
        status = random.choice(Project.status_choice_keys())

        #internal project
        internal = True if random.random()>0.5 else False

        #random choice between allocated or service project
        if random.random()>0.5:
            # allocated
            percentage = random.randrange(MIN_PROJECT_PERCENTAGE, MAX_PROJECT_PERCENTAGE, PERCENTAGE_STEP) # 5% to 50% with 5% step
            p_temp = DirectlyIncurredProject(
                percentage=percentage,
                overheads=250.00,
                salary_band=sb15_2017,
                # base class values
                creator=user,
                created=timezone.now(),
                proj_costing_id=proj_costing_id,
                name=f"test_project_{x}",
                description="none",
                client=c,
                internal=internal,
                start=start,
                end=end,
                status=status)
        else:
            # service
            max_trac_days = int((end-start).days * (220.0/365.0))   # trac days are 220 of the year
            days = random.randint(1, max_trac_days) #between 1 day and max_trac_days
            p_temp = ServiceProject(
                    days=days,
                    rate=275,
                    # base class values
                    creator=user,
                    created=timezone.now(),
                    proj_costing_id=proj_costing_id,
                    name=f"test_project_{x}",
                    description="none",
                    client=c,
                    internal=internal,
                    start=start,
                    end=end,
                    status=status)
         
        
        p_temp.save()
    
    # Create some random allocations to fill projects
    for p in Project.objects.all():
        allocated = 0
        # fill allocations on project until fully allocated
        while allocated < p.fte:
            r = random.choice(RSE.objects.all())
            if p.fte-allocated == MIN_PROJECT_PERCENTAGE:
                percentage = MIN_PROJECT_PERCENTAGE
            else:
                percentage = random.randrange(MIN_PROJECT_PERCENTAGE, p.fte-allocated, PERCENTAGE_STEP) # 5% step
                # Create the allocation
            allocation = RSEAllocation(rse=r, 
                project=p, 
                percentage=percentage,
                start=p.start,
                end=(p.start+timedelta(days=p.duration))
            )
            allocation.save()
            allocated += percentage
    
    
        
    

##############
# Test Cases #
##############

class ProjectAllocationTests(TestCase):
    """
    Test case for testing projects and allocations
    """
    
    def setUp(self):
        random_project_and_allocation_data()
        
            
    def test_random_projects(self):
        """
        Tests the randomly generated projects to ensure that they are valid projects
        """
        
        # Test directly incurred projects (randomly generated fields)
        for p in Project.objects.all():
        
            # test choices
            self.assertIn(p.status, Project.status_choice_keys())
        
            if isinstance(p, DirectlyIncurredProject):
                # percentage should be between min% and max%
                self.assertLessEqual(p.percentage, MAX_PROJECT_PERCENTAGE) 
                self.assertGreaterEqual(p.percentage, MIN_PROJECT_PERCENTAGE)
                
                # start must be before end
                self.assertLess(p.start, p.end)
            elif isinstance(p, ServiceProject):
                # service days should be greater than 1 and less than trac days
                self.assertGreaterEqual(p.days, 1)
                max_trac_days = int((p.end-p.start).days*(220.0/360.0))  # trac days are 220 per year so convert project duration to trac days
                self.assertLessEqual(p.days, max_trac_days)

            
    def test_random_allocations(self):   
        """ Test projects to ensure they are fully allocated """ 
        
        for p in Project.objects.all():
            # Ensure projects are 100 committed
            self.assertAlmostEqual(p.percent_allocated, 100.0, places=2)
            
      
    def test_allocation_dates(self):
        """
        Tests the randomly generated projects to ensure that they are valid projects
        """
        
        # Test directly incurred projects (randomly generated fields)
        for p in Project.objects.all():
        
            for a in RSEAllocation.objects.filter(project=p):
                # start date of allocation should be within project period
                self.assertLess(a.start, p.end)
                self.assertGreaterEqual(a.start, p.start)
                # end date of allocation should be within project period
                self.assertLessEqual(a.end, p.end)
                self.assertGreater(a.end, p.start)
      
            
    def test_accumulated_project_costs(self):
        """
        Tests the project costs to ensure this matches the allocation costs
        Can fail if staff cost functions have discrepancies.
        Assumes that project starting salary is same as each rses starting salary.
        """
        
        # Test directly incurred projects (randomly generated fields)
        for p in Project.objects.all():

            project_cost = p.staff_cost(consider_internal=True).staff_cost
        
            accumulated_allocation_cost = 0
            for a in RSEAllocation.objects.filter(project=p):
                accumulated_allocation_cost += a.staff_cost().staff_cost
                
            # check project cost verses accumulated allocation cost
            self.assertEqual(project_cost, accumulated_allocation_cost)

            

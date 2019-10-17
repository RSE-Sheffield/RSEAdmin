from datetime import date, datetime
from django.utils import timezone

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.test import TestCase

from rse.models import *
import random

###########################################
# Helper functions for creating test data #
###########################################

def setup_user_and_rse_data():
    """
    Function to create data a user and RSE saved in database and in dict of TestCase
    """
    
    # create a single rse with grade change in 2017 and 2019
    # save rse and user in class dict
    user = User.objects.create_user(username='testuser', password='12345')
    rse = RSE(user=user)
    rse.employed_from = date(2017, 1, 1)
    rse.employed_until = date(2025, 1, 1)
    rse.save()


def setup_salary_and_banding_data():
    """
    Function to create data in test database for salary and banding
    """
    
    # create test user and rse
    setup_user_and_rse_data()
    
    # get user from database
    user = User.objects.get(username='testuser')
    # get rse from database
    rse = RSE.objects.get(user=user)
    
    # Create some financial years
    y2017 = FinancialYear(year=2017)
    y2017.save()
    y2018 = FinancialYear(year=2018)
    y2018.save()
    y2019 = FinancialYear(year=2019)
    y2019.save()

    # Create an incremental range for 2017 year
    sb11_2017 = SalaryBand(grade=1, grade_point=1, salary=(1000), year=y2017, increments=True)
    sb11_2017.save()
    sb12_2017 = SalaryBand(grade=1, grade_point=2, salary=(2000), year=y2017, increments=True)
    sb12_2017.save()
    sb13_2017 = SalaryBand(grade=1, grade_point=3, salary=(3000), year=y2017, increments=True)
    sb13_2017.save()
    # Create non incremental range
    sb14_2017 = SalaryBand(grade=1, grade_point=4, salary=(4000), year=y2017, increments=False)
    sb14_2017.save()
    sb15_2017 = SalaryBand(grade=1, grade_point=5, salary=(5000), year=y2017, increments=False)
    sb15_2017.save()

    # Create an incremental range for 2018 year
    sb11_2018 = SalaryBand(grade=1, grade_point=1, salary=(1001), year=y2018, increments=True)
    sb11_2018.save()
    sb12_2018 = SalaryBand(grade=1, grade_point=2, salary=(2001), year=y2018, increments=True)
    sb12_2018.save()
    sb13_2018 = SalaryBand(grade=1, grade_point=3, salary=(3001), year=y2018, increments=True)
    sb13_2018.save()
    # Create non incremental range
    sb14_2018 = SalaryBand(grade=1, grade_point=4, salary=(4001), year=y2018, increments=False)
    sb14_2018.save()
    sb15_2018 = SalaryBand(grade=1, grade_point=5, salary=(5001), year=y2018, increments=False)
    sb15_2018.save()

    # Create an incremental range for 2019 year
    sb11_2019 = SalaryBand(grade=1, grade_point=1, salary=(1002), year=y2019, increments=True)
    sb11_2019.save()
    sb12_2019 = SalaryBand(grade=1, grade_point=2, salary=(2002), year=y2019, increments=True)
    sb12_2019.save()
    sb13_2019 = SalaryBand(grade=1, grade_point=3, salary=(3002), year=y2019, increments=True)
    sb13_2019.save()
    # Create non incremental range
    sb14_2019 = SalaryBand(grade=1, grade_point=4, salary=(4002), year=y2019, increments=False)
    sb14_2019.save()
    sb15_2019 = SalaryBand(grade=1, grade_point=5, salary=(5002), year=y2019, increments=False)
    sb15_2019.save()

    # Create salary grade changes (requires that an RSE has been created in database)
    sgc1 = SalaryGradeChange(rse=rse, salary_band=sb11_2017)
    sgc1.save()
    sgc2 = SalaryGradeChange(rse=rse, salary_band=sb13_2018)
    sgc2.save()
    

def setup_project_and_allocation_data():
    """
    Create a client, projects and allocation in test database
    """
    
    # create test salary bands
    setup_salary_and_banding_data()
    
    # get expected salary band from database
    sb15_2017 = SalaryBand.objects.get(grade=1, grade_point=5, year=2017)
    # get user from database
    user = User.objects.get(username='testuser')
    # get rse from database
    rse = RSE.objects.get(user=user)

    # create some test projects
    c = Client(name="test_client")
    c.department = "COM"
    c.save()        
        
    # Create an allocated project
    p = AllocatedProject(
        percentage=50,
        overheads=250.00,
        salary_band=sb15_2017,
        # base class values
        creator=user,
        created=timezone.now(),
        proj_costing_id="12345",
        name="test_project_1",
        description="none",
        client=c,
        start=date(2017, 8, 1),
        end=date(2019, 1, 1),
        status='F')
    p.save()
    
    
    # Create an allocated project
    p2 = ServiceProject(
        days=30,
        rate=275,
        # base class values
        creator=user,
        created=timezone.now(),
        proj_costing_id="12345",
        name="test_project_1",
        description="none",
        client=c,
        start=date(2017, 8, 1),
        end=date(2019, 1, 1),
        status='F')
    p2.save()
    
    # Create an allocation for the AllocatedProject (spanning full 2017 financial year)
    a = RSEAllocation(rse=rse, 
        project=p,
        percentage=50,
        start=date(2017, 8, 1),
        end=date(2018, 7, 31))
    a.save()
    
    # Create an allocation for the AllocatedProject (spanning full 2017 financial year) at 50% FTE
    a2 = RSEAllocation(rse=rse, 
        project=p, 
        percentage=50,
        start=date(2017, 8, 1),
        end=date(2018, 9, 1))
    a2.save()
    
    # Create an allocation for the ServiceProject at 50% FTE for one month (August 2017)
    a3 = RSEAllocation(rse=rse, 
        project=p2, 
        percentage=50,
        start=date(2017, 8, 1),
        end=date(2017, 9, 1))
    a3.save()
    
    

##############
# Test Cases #
##############

class SalaryCalculationTests(TestCase):

    def setUp(self):
        """
        Create test database using just salary and banding data
        """
        setup_salary_and_banding_data()
        
        # get test user and rse from database
        self.user = User.objects.get(username='testuser')
        # get rse from database
        self.rse = RSE.objects.get(user=self.user)


    def test_salary_finacial_year_span(self):
        """
        Simple tests to check the to see if dates span the financial year.
        """
        # Obvious true
        self.assertTrue(SalaryBand.spans_financial_year(date(2017, 1, 1), date(2018, 1, 1)))
        
        # True by a long way
        self.assertTrue(SalaryBand.spans_financial_year(date(2017, 1, 1), date(2020, 8, 1)))
        
        # One day before true
        self.assertFalse(SalaryBand.spans_financial_year(date(2017, 1, 1), date(2017, 7, 31)))
        
        # True spans financial year by only one day
        self.assertTrue(SalaryBand.spans_financial_year(date(2017, 7, 31), date(2017, 8, 1)))
        
        # True one day into financial year
        self.assertTrue(SalaryBand.spans_financial_year(date(2017, 1, 1), date(2017, 8, 1)))
        
        # False it is the same day
        self.assertFalse(SalaryBand.spans_financial_year(date(2017, 8, 1), date(2017, 8, 1)))

    def test_salary_academic_year_span(self):
        """
        Simple tests to check the to see if dates span the calendar year.
        """
        # Obvious true
        self.assertTrue(SalaryBand.spans_calendar_year(date(2017, 1, 1), date(2018, 1, 1)))
        
        # False (spans only financial year)
        self.assertFalse(SalaryBand.spans_calendar_year(date(2017, 1, 1), date(2017, 8, 1)))


    def test_salary_increment(self):
        """
        Check the incremented salary band for a salary band which will increment 1st January (normal grade point range)

        The correct behaviour is that the salary band should be incremented using the same financial years data. i.e. G1.1 from 2017 should be incremented to G1.2 2017.
        """
        # Get initial test data from DB
        sb11 = SalaryBand.objects.filter(grade=1, grade_point=1, year__year=2017)[0]
        
        # Sanity check for salary of first 2017 salary band at grade 1.1
        self.assertEqual(sb11.salary, 1000)
        sb12 = sb11.salary_band_after_increment()
        
        # salary grade point should increment
        self.assertEqual(sb12.grade, 1)
        self.assertEqual(sb12.grade_point, 2)
        self.assertEqual(sb12.year.year, 2017)

    def test_salary_nonincrement(self):
        """
        Check that a non incrementing salary band remains on the same grade point. Should not change the financial year.

        The correct behaviour is that the salary band should be exactly the same. i.e. G1.4 from 2017 should be remain the same.
        """
        # Get initial test data from DB
        sb14_2017 = SalaryBand.objects.filter(grade=1, grade_point=4, year__year=2017)[0]
        sb14_2017b = sb14_2017.salary_band_after_increment()
        
        # salary grade point should remain the same but use 2018 data
        self.assertEqual(sb14_2017b.grade, 1)
        self.assertEqual(sb14_2017b.grade_point, 4)
        self.assertEqual(sb14_2017b.year.year, 2017)
        
    def test_salary_increment_financial_year(self):
        """
        Check a salary band increment for next financial year for a salary band with following years financial data available in database.

        The correct behaviour is that the salary band grade and point should remain the same but the year should increase. i.e. G1.1 from 2017 should be incremented to G1.1 2018.
        """
        # Get initial test data from DB
        sb11_2017 = SalaryBand.objects.filter(grade=1, grade_point=1, year__year=2017)[0]
        sb11_2018 = sb11_2017.salary_band_next_financial_year()
        
        # salary grade point should increment
        self.assertEqual(sb11_2018.grade, 1)
        self.assertEqual(sb11_2018.grade_point, 1)
        self.assertEqual(sb11_2018.year.year, 2018)
        
    def test_salary_increment_financial_year_estimated(self):
        """
        Check a salary band increment for next financial year for a salary band which does not have  the following years financial data available in database.

        The correct behaviour is that the salary band year, grade and point should remain the same  i.e. G1.1 from 2019 should be returned as the last valid years data for this grade and point
        """
        # Get initial test data from DB
        sb11_2019 = SalaryBand.objects.filter(grade=1, grade_point=1, year__year=2019)[0]
        sb11_2019b = sb11_2019.salary_band_next_financial_year()
        
        # salary grade point should increment
        self.assertEqual(sb11_2019b.grade, 1)
        self.assertEqual(sb11_2019b.grade_point, 1)
        self.assertEqual(sb11_2019b.year.year, 2019)

    def test_get_last_grade_change(self):
        """
        Check that salary grade changes are detected.
        
        The correct behaviour of the lastSalaryGradeChange method is that it should provide the most recent salary grade change up to the provided date. Where there is no additional salary grade change within range the original grade change should be returned.
        """
        # get initial test data from DB
        sgc2017 = SalaryGradeChange.objects.filter(rse=self.rse)[0]
        sgc2018 = SalaryGradeChange.objects.filter(rse=self.rse)[1]
        
        # check that the 2017 salary grade change is detected (date provided is before 1st August 2018 change)
        sgc_test = sgc2017.rse.lastSalaryGradeChange(date(2018, 1, 1))
        self.assertEqual(sgc2017, sgc_test)
        
        # check that the 2018 salary grade change is detected (date provided is after 1st August 2018)
        sgc_test = sgc2017.rse.lastSalaryGradeChange(date(2018, 10, 10))
        self.assertEqual(sgc2018, sgc_test)
        
        # check that there are no further grade changes detected (date is well after last change at 1st August 2018)
        sgc_test = sgc2017.rse.lastSalaryGradeChange(date(2021, 10, 10))
        self.assertEqual(sgc2018, sgc_test)

    def test_salary_projection(self):
        """
        Test salary band projections given a new date
        
        Correct behaviour is that from any specified salary band change a future salary band can be projected. This will either be both;
        1) Incremented on 1st January if existing salary band is incremental (if not it will remain on the salary band)
        2) Adjusted by inflation (by using next finial years salary band data) if the new dates spans a financial year
        Where financial year data is not provided the salary band will be estimated given the current data.
        """
        # Get initial test data from DB
        # first grade change is for 2017 on salary band 1.1 with salary of 1000
        # second grade change is for 2018 on salary band 1.3 with salary of 1000
        sgc = SalaryGradeChange.objects.filter(rse=self.rse)[0]  
        sgc2 = SalaryGradeChange.objects.filter(rse=self.rse)[1] 
        
        # Check initial salary for grade point 1.1
        # If this is wrong then data in test db is not as expected and all other tests will fail
        self.assertEqual(sgc.salary_band.grade, 1)
        self.assertEqual(sgc.salary_band.grade_point, 1)
        self.assertEqual(sgc.salary_band.year.year, 2017)
               
        # Check salary for rse in same year and same financial year
        # Should return same salary band G1.1 2017 (no change)
        sb = sgc.salary_band_at_future_date(date(2017, 12, 12))
        self.assertEqual(sb.grade, 1)
        self.assertEqual(sb.grade_point, 1)
        self.assertEqual(sb.year.year, 2017)
        
        # Check salary for rse in next calendar year but same financial year
        # Should increment the grade point using 2017 financial year data. I.e. G1.2 2017
        sb = sgc.salary_band_at_future_date(date(2018, 1, 6))
        self.assertEqual(sb.grade, 1)
        self.assertEqual(sb.grade_point, 2)
        self.assertEqual(sb.year.year, 2017)
        
        # Check salary for rse at last date in current financial year (same as previous test but last date in range)
        # Should increment grade point not the financial year. I.e. G1.2 2017
        sb = sgc.salary_band_at_future_date(date(2018, 7, 31))
        self.assertEqual(sb.grade, 1)
        self.assertEqual(sb.grade_point, 2)
        self.assertEqual(sb.year.year, 2017)
        
        # Check salary for rse where there is a more recent salary grade change in database
        # Should use the more recent salary grade change data. I.e. G1.3 2018
        sb = sgc.salary_band_at_future_date(date(2018, 8, 1))
        self.assertEqual(sb.grade, 1)
        self.assertEqual(sb.grade_point, 3)
        self.assertEqual(sb.year.year, 2018)
        
        # Check salary for rse at a date two years in future
        # Should use the update salary grade change from previous test then apply financial and grade point increments. I.e. G1.4 2019
        sb = sgc.salary_band_at_future_date(date(2019, 8, 1))
        self.assertEqual(sb.grade, 1)
        self.assertEqual(sb.grade_point, 4)
        self.assertEqual(sb.year.year, 2019)
        
        # Check salary for rse at a date many years in future (where data will be estimated)
        # Should use the update salary grade change from previous test then apply a single financial and grade point increments
        # No further increments should be applied as grade 1.4 does not auto increment and there is no more recent financial data in database
        sb = sgc.salary_band_at_future_date(date(2050, 10, 10))
        self.assertEqual(sb.grade, 1)
        self.assertEqual(sb.grade_point, 4)
        self.assertEqual(sb.year.year, 2019)
    
    def test_date_in_financial_year(self):
        """
        Tests to see if a date is in the finical year represented by this salary band
        """
        
        # Get first (2017) financial year
        fy = FinancialYear.objects.all()[0]
        
        # Test date at start of financial year (1st August 2017)
        self.assertTrue(fy.date_in_financial_year(date(2017, 8, 1)))
        
        # Test date at end of financial year (31st July 2018)
        self.assertTrue(fy.date_in_financial_year(date(2018, 7, 31)))
        
        # Test date before start of financial year (31st July 2017)
        self.assertFalse(fy.date_in_financial_year(date(2017, 7, 31)))
        
        # Test after end of financial year (1st August 2018)
        self.assertFalse(fy.date_in_financial_year(date(2018, 8, 1)))
        
    
    def test_staff_costs(self):
        """
        Test the true cost of staff accounting for grade changes and inflation
        """
        
        # Get initial test data from DB
        # first grade change is for 2017 on salary band 1.1 with salary of 1000
        sgc = SalaryGradeChange.objects.filter(rse=self.rse)[0]
        sb = sgc.salary_band
        sby = sb.year
        
        # Test cost of 2017 1.1 for period without any increments
        # Expected behaviour is value of salary for duration of August 2017. I.e. 1000 * 31/365
        self.assertAlmostEqual(sb.staff_cost(sby.start_date(), date(2017, 9, 1)).staff_cost, 84.93, places=2)
        
        # Test cost of 2017 1.1 for period without any increments at 50% FTE
        # Expected behaviour is value of salary for duration of August 2017. I.e. 1000 * 31/365 *0.5
        self.assertAlmostEqual(sb.staff_cost(sby.start_date(), date(2017, 9, 1), percentage=50.0).staff_cost, 42.47, places=2)
        
        # Test cost of 2017 1.1 for period with grade point increment
        # Expected behaviour is value of salary for year duration with increment in January 
        # I.e. 1000 (2017 G1.1) * 153/365 (days in 2017 FY)
        #      2000 (2017 G1.2) * 212/365(days in 2017 FY after January increment)
        self.assertAlmostEqual(sb.staff_cost(sby.start_date(), date(2018, 8, 1)).staff_cost, 1580.82, places=2)
        
        # Test cost of 2017 1.1 for period with financial year adjustment
        # Expected behaviour is value of salary for 2017 G7.1 July and 2018 G7.1 August 2018
        # I.e. 1000 (2017 G1.1) * 31/365 (days in August 2018 FY)
        #      1001 (2018 G1.1) * 31/365 (days in July 2017 FY)
        self.assertAlmostEqual(sb.staff_cost(date(2018, 7, 1), date(2018, 9, 1)).staff_cost, 169.95, places=2)

class ProjectAllocationTests(TestCase):
    """
    Test case for testing projects and allocations
    """
    
    def setUp(self):
        setup_project_and_allocation_data()
        
        
    def test_polymorphism(self):
        """
        Tests for MTI polymorphism
        """
        
        # Get an allocated project and test that the polymorphic plugin returns the correct type
        # Should return correctly typed concrete implementations of abstract Project type
        p = Project.objects.all()[0]
        self.assertIsInstance(p, AllocatedProject)
        
        # Get an service project and test that the polymorphic plugin returns the correct type
        # Should return correctly typed concrete implementations of abstract Project type
        p = Project.objects.all()[1]
        self.assertIsInstance(p, ServiceProject)
    
    def test_project_duration(self):
        """
        Tests polymorphic function duration which differs depending on project type
        """
        
        # Get an allocated project and test that duration function returns the correct number of days
        # Should return the project duration in days. I.e. 518 days
        #   153 days in 2017 FY
        #   212 days in 2017 FY (after grade point increment in Jan)
        #   153 day in 2018 FY (in new FY after August)
        p = Project.objects.all()[0]
        self.assertEqual(p.duration, 518)
        
        # Get a service project and test that duration function returns the service adjusted for TRAC
        # Should return the project duration in days (30 days plus 19 days adjustment for TRAC)
        p = Project.objects.all()[1]
        self.assertEqual(p.duration, 49)
        
    def test_project_value(self):
        """
        Tests polymorphic function value which differs depending on project type
        """
        
        # Get an allocated project and test that the value is determined from project salary band used for staff costing
        # Should return a value based of the following calculation
        # 50% of 
        #      5000 (2017 G1.5) * 153/365 (days in 2017 FY) +
        #      5000 (2017 G1.5) * 212/365(days in 2017 FY NO January increment) +
        #      5001 (2018 G1.5) * 153/365(days in 2018 FY after January increment)
        p = Project.objects.all()[0]
        self.assertIsInstance(p, AllocatedProject)
        self.assertAlmostEqual(p.staff_budget(), 3548.15, places=2)
        
        # Get a service project and test the value is calculated from the day rate
        # Should return a value of 30 days x £275
        p = Project.objects.all()[1]
        self.assertAlmostEqual(p.value(), 8250.00, places=2)
        
   

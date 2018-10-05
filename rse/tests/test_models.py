from django.test import TestCase
from rse.models import *
from datetime import date, datetime


class SalaryCalcultionTests(TestCase):

    def setUp(self):
        # create some financial years
        y2017 = FinancialYear(year=2017, inflation=0)
        y2017.save()
        y2018 = FinancialYear(year=2018, inflation=0)
        y2018.save()
        y2019 = FinancialYear(year=2019, inflation=0)
        y2019.save()
        
        #create an incremental range for 2017 year
        sb11_2017 =  SalaryBand(grade = 1, grade_point = 1, salary=(1000), year=y2017, increments = True)
        sb11_2017.save()
        sb12_2017 =  SalaryBand(grade = 1, grade_point = 2, salary=(2000), year=y2017, increments = True)
        sb12_2017.save()
        sb13_2017 =  SalaryBand(grade = 1, grade_point = 3, salary=(3000), year=y2017, increments = True)
        sb13_2017.save()
        #create non incremental range
        sb14_2017 =  SalaryBand(grade = 1, grade_point = 4, salary=(4000), year=y2017, increments = False)
        sb14_2017.save()
        sb15_2017 =  SalaryBand(grade = 1, grade_point = 5, salary=(5000), year=y2017, increments = False)
        sb15_2017.save()
        
        #create an incremental range for 2018 year
        sb11_2018 =  SalaryBand(grade = 1, grade_point = 1, salary=(1001), year=y2018, increments = True)
        sb11_2018.save()
        sb12_2018 =  SalaryBand(grade = 1, grade_point = 2, salary=(2001), year=y2018, increments = True)
        sb12_2018.save()
        sb13_2018 =  SalaryBand(grade = 1, grade_point = 3, salary=(3001), year=y2018, increments = True)
        sb13_2018.save()
        #create non incremental range
        sb14_2018 =  SalaryBand(grade = 1, grade_point = 4, salary=(4001), year=y2018, increments = False)
        sb14_2018.save()
        sb15_2018 =  SalaryBand(grade = 1, grade_point = 5, salary=(5001), year=y2018, increments = False)
        sb15_2018.save()
        
        #create an incremental range for 2019 year
        sb11_2019 =  SalaryBand(grade = 1, grade_point = 1, salary=(1002), year=y2019, increments = True)
        sb11_2019.save()
        sb12_2019 =  SalaryBand(grade = 1, grade_point = 2, salary=(2002), year=y2019, increments = True)
        sb12_2019.save()
        sb13_2019 =  SalaryBand(grade = 1, grade_point = 3, salary=(3002), year=y2019, increments = True)
        sb13_2019.save()
        #create non incremental range
        sb14_2019 =  SalaryBand(grade = 1, grade_point = 4, salary=(4002), year=y2019, increments = False)
        sb14_2019.save()
        sb15_2019 =  SalaryBand(grade = 1, grade_point = 5, salary=(5002), year=y2019, increments = False)
        sb15_2019.save()
        
        # create a single rse with grade change in 2017 and 2019
        # save rse and user in class dict
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.rse = RSE(user=self.user)
        self.rse.save()
        sgc1 = SalaryGradeChange(rse=self.rse, salary_band=sb11_2017)
        sgc1.save()
        sgc2 = SalaryGradeChange(rse=self.rse, salary_band=sb15_2019)
        sgc2.save()
        
        # create some test projects
        c = Client(name="test_client")
        c.save()
        p = Project(creator = self.user, \
                    created=datetime.now(), \
                    funder_id="12345", \
                    name="test_project", \
                    description="none", \
                    client=c, \
                    start=date(2010, 1, 1), \
                    end=date(2050, 1, 1), \
                    percentage=50, \
                    status='F')
        p.save()
        a = RSEAllocation(rse=self.rse, project=p, percentage=50, \
                          start=date(2017, 8, 1), 
                          end=date(2018, 7, 31))
        a.save()
        a2 = RSEAllocation(rse=self.rse, project=p, percentage=50, \
                          start=date(2017, 8, 1), 
                          end=date(2019, 7, 31))
        a2.save()

    def test_salary_year_span(self):
        """
        Just a bunch of simple tests to check the financial used to see if dates span the financial year.
        """
        # Obvious true
        self.assertEqual(SalaryBand.spansFinancialYear(date(2017, 1, 1), date(2018, 1, 1)), True)
        # True by a long way
        self.assertEqual(SalaryBand.spansFinancialYear(date(2017, 1, 1), date(2020, 8, 1)), True)
        # One day before true
        self.assertEqual(SalaryBand.spansFinancialYear(date(2017, 1, 1), date(2017, 7, 31)), False)
        # True by only one day
        self.assertEqual(SalaryBand.spansFinancialYear(date(2017, 1, 1), date(2017, 8, 1)), True)
        
    
    def test_salary_increment_final_year(self):
        """ 
        Test will check the incremented salary band for a salary band with no data for the next year.
        The correct behaviour is that the salary band should be estimated by providing the next increment from the current year.
        I.e. G1.1 from 2019 should be incremented to G1.2 2019
        """
        sb11 = SalaryBand.objects.filter(grade=1, grade_point=1, year__year=2019)[0]
        # Sanity check for salary of first 2019 salary band at grade 1.1
        self.assertEqual(sb11.salary, 1002)
        sb12 = sb11.salaryBandAfterIncrement()
        # salary grade point should be based of 2019 data as no 2020 data exists
        self.assertEqual(sb12.salary, 2002)
      
    def test_salary_increment_first_year(self):
        """ 
        Test will check the incremented salary band for a salary band with data available for the next financial year.
        The correct behaviour is that the salary band should be incremented using the next financial years data.
        I.e. G1.1 from 2017 should be incremented to G1.2 2018
        """
        sb11 = SalaryBand.objects.filter(grade=1, grade_point=1, year__year=2017)[0]
        # Sanity check for salary of first 2017 salary band at grade 1.1
        self.assertEqual(sb11.salary, 1000)
        sb12 = sb11.salaryBandAfterIncrement()
        # salary grade point should be based of 2018 data
        self.assertEqual(sb12.salary, 2001)
        
    def test_salary_increment(self):
        """ 
        Test will check the that a non incrementing salary band remains on the same grade point but uses the next financial years data.
        The correct behaviour is that the salary band should be not be incremented but the next years financial data should be used.
        I.e. G1.4 from 2017 should be incremented to G1.4 2018
        """
        sb14_2017 = SalaryBand.objects.filter(grade=1, grade_point=4, year__year=2017)[0]
        # Sanity check for salary of first 2017 salary band at grade 1.4
        self.assertEqual(sb14_2017.salary, 4000)
        sb14_2018 = sb14_2017.salaryBandAfterIncrement()
        # salary grade point should remain the same but use 2018 data
        self.assertEqual(sb14_2018.salary, 4001)
              
    def test_get_last_grade_change(self):
        sgc = SalaryGradeChange.objects.filter(rse=self.rse)[0]
        # check that the 2017 salary grade change is detected
        sgc2 = sgc.rse.lastSalaryGradeChange(date(2019, 1, 1))
        self.assertEqual(sgc, sgc2)
        # check that the 2019 salary grade change is detected
        sgc2 = sgc.rse.lastSalaryGradeChange(date(2019, 10, 10))
        self.assertNotEqual(sgc, sgc2)
        # check that there are no further grade changes detected
        sgc3 = sgc2.rse.lastSalaryGradeChange(date(2021, 10, 10))
        self.assertEqual(sgc2, sgc3)
    
    def test_salary_projection(self):
        sgc = SalaryGradeChange.objects.filter(rse=self.rse)[0] # first grade change is for 2017
        # check salary for grade point 1.1 
        self.assertEqual(sgc.salary_band.salary, 1000)
        # check salary for rse in same year and same financial year
        sb = sgc.salaryBandAtFutureDate(date(2017,12,12))
        self.assertEqual(sb.salary, 1000)
        # check salary for rse in next year but same financial year
        sb = sgc.salaryBandAtFutureDate(date(2018,6,1))
        self.assertEqual(sb.salary, 1000)
        # check salary for rse at first date in next financial year (should be normal increment using 2018 data)
        sb = sgc.salaryBandAtFutureDate(date(2018,8,1))
        self.assertEqual(sb.salary, 2001)
        # check salary for rse at date in next financial year (should be normal increment using 2018 data)
        sb = sgc.salaryBandAtFutureDate(date(2018,12,12))
        self.assertEqual(sb.salary, 2001)
        # check salary for rse at a date two years in future (should be retrieved from salary band change to g1.5)
        sb = sgc.salaryBandAtFutureDate(date(2019,10,10))
        self.assertEqual(sb.salary, 5002)
        # check salary for rse at a date many years in future (should be retrieved from salary band change to g1.5) which does not increment
        sb = sgc.salaryBandAtFutureDate(date(2050,10,10))
        self.assertEqual(sb.salary, 5002)
        
    def test_query_salary_band(self):
        #should error as no salary band data changes exist before 1st August 2017
        #self.assertEqual(self.rse.futureSalaryBand(date(2017, 1, 1)).salary, 1000)
        #should return a salary band of g1.1 2017
        self.assertEqual(self.rse.futureSalaryBand(date(2017, 12, 12)).salary, 1000)
        #should return a salary band of g1.1 2017
        self.assertEqual(self.rse.futureSalaryBand(date(2018, 1, 1)).salary, 1000)
        #should return a salary band of g1.2 2018
        self.assertEqual(self.rse.futureSalaryBand(date(2018, 9, 1)).salary, 2001)
        
    def test_allocation_costs(self):
        # test cost of 50% allocation for full 2017 year (expects 1000*0.5)
        a = RSEAllocation.objects.all()[0]
        self.assertEqual(a.staffCost(), 500)
        # test cost of 50% allocation for full 2017 and 2018 year (expects 1000*.5 + 2001*0.5)
        a = RSEAllocation.objects.all()[1]
        self.assertEqual(a.staffCost(), 1500.5)
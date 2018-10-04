from django.test import TestCase
from rse.models import *


class SalaryCalcultionTests(TestCase):

    def setUp(self):
        y = FinancialYear(year=2018, inflation=0)
        y.save()
        
        sbs = {}
        #create an incremental range
        for gp in range(5):
            sbs[gp] = SalaryBand(grade = 1, \
                            grade_point = gp, \
                            salary=(gp+1*1000), \
                            year=y, \
                            increments = True)
            sbs[gp].save()
        #create non incremental range
        for gp in range(3):
            sbs[gp+5] = SalaryBand(grade = 1, \
                            grade_point = 5+gp, \
                            salary=(gp+6*1000), \
                            year=y, \
                            increments = False)
            sbs[gp+5].save()
        
        # create a salary increment
        self.user = User.objects.create_user(username='testuser', password='12345')
        rse = RSE(user=self.user)
        rse.save()
        sgc = SalaryGradeChange(rse=rse, salary_band=sbs[0])
        sgc.save()

    def test_salary_projection(self):
        sgc = SalaryGradeChange.objects.all()[0]
        # check salary for grade point 1.1 
        self.assertEqual(sgc.salary_band.salary, 1000)
        # check salary for grade point 1.1 in current year
        sb = sgc.salaryBandAtFutureDate()
        self.assertEqual(sgc.salary_band.salary, 6000)
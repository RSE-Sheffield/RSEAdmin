from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import timedelta, datetime, date
from django.db.models import Max
from math import ceil, floor

#depreciated: TODO clear migrations adn delete
class PercentageField(models.FloatField):
    #widget = models.TextInput(attrs={"class": "percentInput"})

    def to_python(self, value):
        val = super(PercentageField, self).to_python(value)
        if val.isnumeric():
            return val/100
        return val

    def prepare_value(self, value):
        val = super(PercentageField, self).prepare_value(value)
        if val.isnumeric() and not isinstance(val, str):
            return str((float(val)*100))
        return val
        
        
        
        

class FinancialYear(models.Model):
    year = models.IntegerField(primary_key=True, default=2018) # Must relate to a financial year
    inflation = models.FloatField()
    
    def __str__(self):
        return str(self.year)

class SalaryBand(models.Model):
    grade = models.IntegerField(default=1)
    grade_point = models.IntegerField(default=1)
    salary = models.DecimalField(max_digits=8, decimal_places=2)
    year = models.ForeignKey(FinancialYear, on_delete=models.DO_NOTHING)
    increments = models.BooleanField(default=True) # Increments if in normal range
    
    def __str__(self):
        return str(self.grade) + '.' + str(self.grade_point) + ' (' + str(self.year) + '): ' + '£' + str(self.salary)
        
    # Get the next salary band if it increments
    def salaryBandAfterIncrement(self):
        # Handle increment
        g = self.grade
        gp = self.grade_point
        if (self.increments):
           gp+=1
        # Find next
        y = self.year.year+1
        sbs = SalaryBand.objects.filter(grade=g, grade_point=gp, year__year=y) # order by year?
        if sbs: # should be unique
            return sbs[0]
        else: # There is no more salary band data (probably not released yet)
            # TODO: Warning: estimated salary band off currently available data
            # if no increment then just return the same salary band
            if not self.increments:
                return self
            # if there is an increment then get next salary band from current year
            sbs = SalaryBand.objects.filter(grade=g, grade_point=gp, year=self.year)
            if sbs: # should be unique
                return sbs[0]
            else:
                raise ObjectDoesNotExist('Incomplete salary data in database. Could not find a valid increment for current salary band.')
                
    @staticmethod
    def spansFinancialYear(start, end):
        # next financial year end from start date
        if start.month>=8:
            n_fy_end = date(start.year+1, 7, 31)
        else:
            n_fy_end = date(start.year, 7, 31)
            
        return end > n_fy_end
    
    def startDate(self):
        """
        The start date of the financial year
        """
        return date(self.year.year, 8, 1)
        
    def endDate(self):
        return self.startDate() + timedelta(days=364)
        
    
class Client(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    

class RSE(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    current_employment = models.BooleanField(default=True)
    
    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name
    
    # Gets the last salary grade change before the specified date (i.e. the last appropriate grade change) or now
    def lastSalaryGradeChange(self, date=datetime.now()):
        sgcs = SalaryGradeChange.objects.filter(rse=self).order_by('-salary_band__year')
        for sgc in sgcs:
            if sgc.salary_band.startDate() <= date:
                return sgc
        # unable to find any data
        raise ValueError('No Salary Data exists before specified date period for this RSE') 
            
    def futureSalaryBand(self, date):
        # gets the last valid salary grade change event 
        # predicts salary data for provided date by incrementing 
        # this may be based on real grade changes in the future or estimated from current financial year increments
        return self.lastSalaryGradeChange(date).salaryBandAtFutureDate(date)
    
    def salaryCost(self, days, salary, percentage=100.0):
        return (days/365.0)*float(salary)*(float(percentage)/100.0) 

    def staffCost(self, start, end, percentage=100.0):
        # Add one to end as end day is inclusive or cost calculation (e.g. start date from 9:00 end date until 5pm)
        end = end + timedelta(days=1)

        # Calculate cost per year by splitting into financial year periods to obtain correct salary info
        cost = 0  
        s = start   
        while SalaryBand.spansFinancialYear(s, end):
            sb = self.futureSalaryBand(s)               # salary band at date s
            ye = sb.endDate() + timedelta(days=1)           # financial year end for date s (for cost calculations this needs to include this day)
            d = ye - s                                      # duration in days 
            cost += self.salaryCost(d.days, sb.salary, percentage)      # increment by salary cost for this period (for allocation percentage)
            # increment to next financial year
            s = ye
        
        # final (partial) year calculation
        d = end - s                                 # duration in days
        sb = self.futureSalaryBand(s)           # get latest salary for this period
        cost += self.salaryCost(d.days, sb.salary, percentage)  # increment by salary cost for this period

        return cost
        
        
class SalaryGradeChange(models.Model):
    rse = models.ForeignKey(RSE, on_delete=models.DO_NOTHING)
    salary_band = models.ForeignKey(SalaryBand, on_delete=models.DO_NOTHING)
    # assume grade change only occurs on 1st August
    
    # Gets the incremented salary given some point in the future
    def salaryBandAtFutureDate(self, date):

        # check for obvious stupid
        if date < self.salary_band.startDate():
            raise ValueError('Future salary can not be calculated from dates in the past')
        
        # easy case if date is in the same financial year
        if not SalaryBand.spansFinancialYear(self.salary_band.startDate(), date):
            return self.salary_band
            
        # check if there is a salary grade change at a later date
        sgc = self.rse.lastSalaryGradeChange(date)
        if not sgc.id == self.id:
            # there is a more recent salary grade change so use it
            return sgc.salaryBandAtFutureDate(date)
        
        # loop financial years to increment salary where appropriate
        sb = self.salary_band
        increments = floor((date - sb.startDate()).days/365.0)
        for _ in range(increments):
            sb = sb.salaryBandAfterIncrement()
            
        return sb
    
    
    def __str__(self):
        return self.rse.user.first_name + ' ' + self.rse.user.last_name + ': Grade ' \
        + str(self.salary_band.grade) + '.' + str(self.salary_band.grade_point) \
        + '(' + str(self.salary_band.year) + ')' 
  
    
class Project(models.Model):
    creator = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    created = models.DateTimeField()
    
    funder_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    client = models.ForeignKey(Client, on_delete=models.DO_NOTHING)
    academic_contact = models.CharField(max_length=100)
    
    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)
    percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    overheads = models.BooleanField(default=True)
    STATUS_CHOICES = (
        ('P', 'Preperation'),
        ('R', 'Review'),
        ('F', 'Funded'),
        ('X', 'Rejected'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    
    def __str__(self):
        return self.name
        
    @property
    def duration(self):
        return (self.end - self.start).days
        
    
class RSEAllocation(models.Model):
    rse = models.ForeignKey(RSE, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    start = models.DateField()
    end = models.DateField()
    
    def __str__(self):
        return str(self.rse.user) + ' on ' + str(self.project) + ' at ' + str(self.percentage) + '%'
        
    @property
    def duration(self):
        return (self.end - self.start).days
        
        
    def staffCost(self, start=None, end=None):
        # if no time period then use defaults for project
        # limit specified time period to allocation
        if start is None or start < self.start:
            start = self.start
        if end is None or end > self.end:
            end = self.end
            
        return self.rse.staffCost(start, end, self.percentage)
        
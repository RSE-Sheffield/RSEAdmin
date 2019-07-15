from datetime import date, datetime, timedelta
from django.utils import timezone
from math import floor
from typing import Optional

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from polymorphic.models import PolymorphicModel

class FinancialYear(models.Model):
    """
    Year represents a financial year starting in August of the year field (not an academic year of Sept to Sept).
    """
    year = models.IntegerField(primary_key=True, default=2018)  # Must relate to a financial year
    inflation = models.FloatField()

    def __str__(self) -> str:
        return str(self.year)


class SalaryBand(models.Model):
    """
    Salary band represents a grade point and salary for a university staff member.
    See https://www.sheffield.ac.uk/hr/thedeal/pay
    Start and end date of financial year is hard coded as 1st August
    """
    grade = models.IntegerField(default=1)
    grade_point = models.IntegerField(default=1)
    salary = models.DecimalField(max_digits=8, decimal_places=2)
    year = models.ForeignKey(FinancialYear, on_delete=models.DO_NOTHING)
    increments = models.BooleanField(default=True)                          # Increments if in normal range

    def __str__(self) -> str:
        return f"{self.grade}.{self.grade_point} ({self.year}): £{self.salary}"


    def salary_band_after_increment(self):
        """
        Provides the next salary band object after a single increment. 
        Grades which increments will use the next available grade point.  Grades which do not increment (exceptional range) will return the same salary band.
        """
        
        # check first to see if salary band can increment
        if self.increments:
            # Find next salary band with incremented year
            g = self.grade
            gp = self.grade_point + 1
            y = self.year.year
            sb = SalaryBand.objects.filter(grade=g, grade_point=gp, year__year=y)  # order by year?
            
            # Result of database query should be unique if next years data is available
            if sb:  
                return sb[0]
            raise ObjectDoesNotExist('Incomplete salary data in database. Could not find a valid increment for current salary band.')
            
        # salary band does not increment so return self
        else:
            return self
        

    def salary_band_next_financial_year(self):
        """
        Provides the salary and for the next financial year
        Normal behaviour is to use the next years financial data. If there is no next year financial data then the current years financial data is used. 
        Grade point should not change as this represents just the salary change in August which is the inflation adjustment.
        """
        # Query database to find a salary band for next years financial data
        g = self.grade
        gp = self.grade_point
        y = self.year.year + 1
        sbs = SalaryBand.objects.filter(grade=g, grade_point=gp, year__year=y)
        
        # Should be unique if next years data is available
        if sbs:  
            return sbs[0]
        # There is no more salary band data (probably not released yet)
        else:  
            # Return current salary band
            return self


    @staticmethod
    def spans_financial_year(start: date, end: date) -> bool:
        """
        Static method to determine if a date range spans a financial year. 
        Important for considering inflation adjustments.
        """
        # Catch error
        if start > end:
            raise ValueError('Start date after end date')
        
        # Next financial year end from start date
        if start.month >= 8:
            n_fy_end = date(start.year + 1, 7, 31)
        else:
            n_fy_end = date(start.year, 7, 31)

        return end > n_fy_end
        
    @staticmethod
    def spans_calendar_year(start: date, end: date) -> bool:
        """
        Static method to determine if a date range spans a calendar year. 
        Important for considering grade point increments.
        """
        # Catch error
        if start > end:
            raise ValueError('Start date after end date')
            
        return end.year > start.year
        
    @staticmethod
    def spans_salary_change(start: date, end: date) -> bool:
        """
        Static method to determine if a date range spans either a calendar or financial year. 
        """
        # Catch error
        if start > end:
            raise ValueError('Start date after end date')
            
        return SalaryBand.spans_calendar_year(start, end) or SalaryBand.spans_financial_year(start, end)

    def start_date(self) -> date:
        """Get start date of the financial year."""
        return date(self.year.year, 8, 1)

    def end_date(self) -> date:
        """Get end date of the financial year."""
        return self.start_date() + timedelta(days=364)


class Client(models.Model):
    """
    Client represents a client of RSE work. Usually a named academic of university staff member in a given department, professional service or research institute.
    """
    
    name = models.CharField(max_length=100)         # contact name (usually academic)
    department = models.CharField(max_length=100)   # university department      
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class RSE(models.Model):
    """
    RSE represents a RSE staff member within the RSE team
    """
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    employed_from = models.DateField()
    employed_until = models.DateField()
    
    @property
    def current_employment(_self):
        """
        Is the staff member currently employed
        """
        return self.employed_from < timezone.now() and self.employed_until > timezone.now()

    def __str__(self) -> str:
        return f"{self.user.first_name} {self.user.last_name}"

    def lastSalaryGradeChange(self, date: date = timezone.now()):
        """
        Gets the last salary grade change before the specified date (i.e. the last appropriate grade change)
        """
        sgcs = SalaryGradeChange.objects.filter(rse=self).order_by('-salary_band__year')
        for sgc in sgcs:
            if sgc.salary_band.start_date() <= date:
                return sgc
        # Unable to find any data
        raise ValueError('No Salary Data exists before specified date period for this RSE')

    def futureSalaryBand(self, date: date):
        """
        Gets the last valid salary grade change event.
        Predicts salary data for provided date by incrementing.
        This may be based on real grade changes in the future or estimated from current financial year increments (see `salary_band_after_increment` notes in `SalaryBand`)
        """
        return self.lastSalaryGradeChange(date).salary_band_at_future_date(date)

    @staticmethod
    def salaryCost(days, salary, percentage: float = 100.0) -> float:
        """
        Returns the salary cost for a number of days given a salary and FTE percentage
        """
        return (days / 365.0) * float(salary) * (float(percentage) / 100.0)

    def staff_cost(self, start, end, percentage: float = 100.0):
        """
        Calculates the staff cost of an RSE given a start and end date with percentage FTE.
        Cost is calculated by breaking a date range down into financial years ensuring increments and annual salary inflation is adjusted for.
        
        TODO: This is broken does not account for grade point changes
        """
    
        # Add one to end as end day is inclusive of cost calculation (e.g. start date from 9:00 end date until 5pm)
        end = end + timedelta(days=1)

        # Calculate cost per year by splitting into financial year periods to obtain correct salary info
        cost = 0.0
        s = start
        # BUG #24: Needs to also be broken down into real years for increments
        while SalaryBand.spans_financial_year(s, end):
            sb = self.futureSalaryBand(s)  # salary band at date s
            ye = sb.end_date() + timedelta(days=1)  # financial year end for date s (for cost calculations this needs to include this day)
            d = ye - s  # duration in days
            cost += self.salaryCost(d.days, sb.salary, percentage)  # increment by salary cost for this period (for allocation percentage)
            # increment to next financial year
            s = ye

        # final (partial) year calculation
        d = end - s                    # duration in days
        sb = self.futureSalaryBand(s)  # get latest salary for this period
        cost += self.salaryCost(d.days, sb.salary, percentage)  # increment by salary cost for this period

        return cost


class SalaryGradeChange(models.Model):
    """
    SalaryGradeChange represents a change (or initial setting) of an RSE salary band
    A SalaryGradeChange may be required where there is promotion or exceptional progression through grade bands.
    All salary grade changes are assumed to be from 1st August as this is the date in which finical year runs.
    This is different to annual increments which occur in January and are considered when calculating salary.
    """
    
    rse = models.ForeignKey(RSE, on_delete=models.DO_NOTHING)
    salary_band = models.ForeignKey(SalaryBand, on_delete=models.DO_NOTHING)

    # Gets the incremented salary given some point in the future
    def salary_band_at_future_date(self, future_date):
        """
        Returns a salary band at some date in the future.
        The SalaryGradeChange represents a starting point for the calculation of future grade points and as such can be used to apply increments
        """
        # Check for obvious stupid
        if future_date < self.salary_band.start_date():
            raise ValueError('Future salary can not be calculated from dates in the past')
            
        # Check if there is a salary grade change at a later date but before specified date
        sgc = self.rse.lastSalaryGradeChange(future_date)
        if not sgc.id == self.id:
            # there is a more recent salary grade change so use it
            return sgc.salary_band_at_future_date(future_date)


        # Get the salary band and start date of the salary grade change
        # Note salary band data may be estimated in future years so the date of increment must be tracked
        next_increment = sgc.salary_band.start_date() # start of financial year
        next_sb = sgc.salary_band
        
        # If the salary can change between the date range then advance increment or year
        while ( SalaryBand.spans_salary_change(next_increment, future_date)):
            # If date is before financial year then date range spans financial year
            if next_increment.month < 8 :
                next_increment = date(next_increment.year, 8, 1)
                next_sb = next_sb.salary_band_next_financial_year()
                
            # Doesn't span financial year so must span calendar year
            else:
                next_increment = date(next_increment.year + 1, 1, 1)
                next_sb = next_sb.salary_band_after_increment()
        
        return next_sb
       

    def __str__(self) -> str:
        return (f"{self.rse.user.first_name} {self.rse.user.last_name}: Grade "
                f"{self.salary_band.grade}.{self.salary_band.grade_point}"
                f"({self.salary_band.year})")


class Project(PolymorphicModel):
    """
    Project represents a project undertaken by RSE team.
    Projects are not abstract but should not be initialised without using either a AllocatedProject or ServiceProject (i.e. Multi-Table Inheritance). The Polymorphic django utility is used to make inheretance much cleaner.
    See docs: https://django-polymorphic.readthedocs.io/en/stable/quickstart.html
    """
    creator = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    created = models.DateTimeField()

    proj_costing_id = models.CharField(max_length=50, null=True)    # Internal URMS code
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    client = models.ForeignKey(Client, on_delete=models.DO_NOTHING)

    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)
    
    STATUS_CHOICES = (
        ('P', 'Preparation'),
        ('R', 'Review'),
        ('F', 'Funded'),
        ('X', 'Rejected'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    def duration(self) -> Optional[int]:
        """ Implemented by concrete classes """        
        pass
            
            
    def value(self) -> Optional[int]:
        """ Implemented by concrete classes """        
        pass
            
        
    def __str__(self):
        return self.name

    def clean(self):
        if self.status != 'P' and not self.proj_costing_id:
            raise ValidationError(_('Project proj_costing_id cannot be null if the grant has passed the preparation stage.'))
        if self.start and self.end and self.end < self.start:
            raise ValidationError(_('Project end cannot be earlier than project start.'))
            

class AllocatedProject(Project):
    """
    AllocatedProject is a cost recovery project used to allocate an RSE for a percentage of time given the projects start and end dates
    """
    percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])   # FTE percentage
    OVERHEAD_CHOICES = (
        ('N', 'None'),
        ('U', 'UKRI'),
        ('E', 'EU'),
    )
    overheads = models.CharField(max_length=1, choices=OVERHEAD_CHOICES, default='N')  # Overhead type

    def duration(self) -> int:
        """
        Duration is determined by start and end dates
        """
        dur = None
        if self.end and self.start:
            dur = (self.end - self.start).days
        return dur
    
    # TODO
    def value(self) -> float:
        """
        Value is determined by project duration based off standard RSE costing of G7.9
        """
        return 0
    
class ServiceProject(Project):
    """
    ServiceProject is a number of service days in which work should be undertaken. The projects dates set parameters for which the work can be undertaken but do not define the exact dates in which the work will be conducted. An allocation will convert the service days into an FTE equivalent so that time can be scheduled including holidays.
    """
    days = models.IntegerField(default=1)                           # duration in days
    rate = models.DecimalField(max_digits=8, decimal_places=2)      # service rate 
    
    def duration(self) -> int:
        """
        Duration is determined by number of service days adjusted for weekends and holidays
        This maps service days (of which there are 220 TRAC working days) to a FTE duration
        """
        return floor(self.days * (360.0/ 220.0))
        
    def value(self) -> float:
        """
        Value is determined by service days multiplied by rate
        """
        return days*rate

class RSEAllocation(models.Model):
    """
    Defines an allocation of an RSE to project with a given percentage of time.
    """
    rse = models.ForeignKey(RSE, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    percentage = models.FloatField(validators=[MinValueValidator(0),
                                               MaxValueValidator(100)])
    start = models.DateField()
    end = models.DateField()

    def __str__(self) -> str:
        return f"{self.rse} on {self.project} at {self.percentage}%"

    @property
    def duration(self):
        return (self.end - self.start).days

    def staff_cost(self, start=None, end=None):
        """
        Returns the cost of a member of staff over a duration (if provided) or for full allocation if not
        """
        # If no time period then use defaults for project
        # then limit specified time period to allocation
        if start is None or start < self.start:
            start = self.start
        if end is None or end > self.end:
            end = self.end

        return self.rse.staff_cost(start, end, self.percentage)

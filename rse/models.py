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
from django.db.models import Max, Min
import itertools as it


class FinancialYear(models.Model):
    """
    Year represents a financial year starting in August of the year field (not an academic year of Sept to Sept).
    """
    year = models.IntegerField(primary_key=True, default=2018)  # Must relate to a financial year
    inflation = models.FloatField()

    def start_date(self) -> date:
        """Get start date of the financial year."""
        return date(self.year, 8, 1)

    def end_date(self) -> date:
        """Get end date of the financial year."""
        return self.start_date() + timedelta(days=364)

    def date_in_financial_year(self, date: date) -> bool:
        """
        Functions checks is a date is in the finical year represented
        """
        return date >= self.start_date() and date <= self.end_date()
    

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
    year = models.ForeignKey(FinancialYear, on_delete=models.PROTECT)       # Don't allow a year to be removed if there are salary bands associated with it 
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

    @staticmethod
    def salaryCost(days, salary, percentage: float = 100.0) -> float:
        """
        Returns the salary cost for a number of days given a salary and FTE percentage
        """
        return (days / 365.0) * float(salary) * (float(percentage) / 100.0)
        
    def staff_cost(self, start: date, end: date, percentage: float = 100.0) -> float :
        """
        Gets the staff cost for this salary band by considering any future increments
        Start must be a date in the current financial year in which this salary band represents
        End (up to not including )can be any date after start and may require increments
        
        Function operates in same way as salary_band_at_future_date
        """
        
        # Check for obvious stupid
        if end < start:
            raise ValueError('End date is before start date')
            
        # Check that the start date is in the financial year of this salary band
        if not self.year.date_in_financial_year(start):
            raise ValueError('SalaryBand staff costs can only be calculated for dates starting in the specified financial year')
        
        
        # Now calculate the staff costs through iteration of chargeable periods (applying any increments)
        # Note salary band data may be estimated in future years so the date of increment must be tracked rather than just the salary band
        next_increment = start
        next_sb = self
        cost = 0
        
        # If the salary can change between the date range then advance increment or year
        while ( SalaryBand.spans_salary_change(next_increment, end)):
            # If date is before financial year then date range spans financial year
            if next_increment.month < 8 :
                # calculate next increment date and salary band
                temp_next_increment = date(next_increment.year, 8, 1)
                temp_next_sb = next_sb.salary_band_next_financial_year()

            # Doesn't span financial year so must span calendar year
            else:
                # increment cost between period
                temp_next_increment = date(next_increment.year + 1, 1, 1)
                temp_next_sb = next_sb.salary_band_after_increment()
                
            # update salary cost
            cost += SalaryBand.salaryCost((temp_next_increment - next_increment).days, next_sb.salary)
            # update chargeable period date and band
            next_increment = temp_next_increment
            next_sb = temp_next_sb
        
        # Final salary cost for period not spanning a salary change
        cost += SalaryBand.salaryCost((end - next_increment).days, next_sb.salary)
        
        return cost*percentage/100.0


class Client(models.Model):
    """
    Client represents a client of RSE work. Usually a named academic of university staff member in a given department, professional service or research institute.
    """
    
    name = models.CharField(max_length=100)         # contact name (usually academic)
    department = models.CharField(max_length=100)   # university department      
    description = models.TextField(blank=True)

    @property
    def total_projects(self) -> int:
        """ Returns the number of projects associated with this client """
        return Project.objects.filter(client=self).count()
    
    @property    
    def funded_projects(self) -> int:
        """ Returns the number of active projects associated with this client """
        return Project.objects.filter(client=self, status=Project.FUNDED).count()
    
    @property    
    def funded_projects_percent(self) -> float:
        """ Returns the number percentage of active projects associated with this client """
        if self.total_projects > 0:
            return self.funded_projects / self.total_projects * 100.0
        else:
            return 0

    def __str__(self) -> str:
        return self.name


class RSE(models.Model):
    """
    RSE represents a RSE staff member within the RSE team
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employed_from = models.DateField()
    employed_until = models.DateField()
    
    @property
    def current_employment(self):
        """
        Is the staff member currently employed
        """
        now = timezone.now().date()
        return self.employed_from < now and self.employed_until > now

    def __str__(self) -> str:
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def current_capacity(self) -> float:
        """ Returns the current capacity of an RSE as a percentage of FTE """
        now = timezone.now().date()
        return sum(a.percentage for a in RSEAllocation.objects.filter(rse=self, start__lte=now, end__gt=now))
        

    def lastSalaryGradeChange(self, date: date = timezone.now()):
        """
        Gets the last salary grade change before the specified date (i.e. the last appropriate grade change)
        """
        sgcs = SalaryGradeChange.objects.filter(rse=self).order_by('-salary_band__year')
        for sgc in sgcs:
            if sgc.salary_band.year.start_date() <= date:
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
        
    @property
    def colour_rbg(self) -> str:
        r = hash(self.user.first_name) % 255
        g = hash(self.user.last_name) % 255
        b = hash(self.user.first_name + self.user.last_name) %255
        return {"r": r, "g": g, "b": b}



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
        if future_date < self.salary_band.year.start_date():
            raise ValueError('Future salary can not be calculated from dates in the past')
            
        # Check if there is a salary grade change at a later date but before specified date
        sgc = self.rse.lastSalaryGradeChange(future_date)
        if not sgc.id == self.id:
            # there is a more recent salary grade change so use it
            return sgc.salary_band_at_future_date(future_date)


        # Get the salary band and start date of the salary grade change
        # Note salary band data may be estimated in future years so the date of increment must be tracked
        next_increment = sgc.salary_band.year.start_date() # start of financial year
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
    creator = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField()

    proj_costing_id = models.CharField(max_length=50, null=True)    # Internal URMS code
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    internal = models.BooleanField(default=False)                    # Internal or in kind projects


    start = models.DateField()
    end = models.DateField()
    
    PREPARATION = 'P'
    REVIEW = 'R'
    FUNDED = 'F'
    REJECTED = 'X'
    STATUS_CHOICES = (
        (PREPARATION, 'Preparation'),
        (REVIEW, 'Review'),
        (FUNDED, 'Funded'),
        (REJECTED, 'Rejected'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    @staticmethod
    def status_choice_keys():
        """ Returns the available choices for status field """
        return [Project.PREPARATION, Project.REVIEW, Project.FUNDED, Project.REJECTED]

    @property
    def duration(self) -> Optional[int]:
        """ Implemented by concrete classes """        
        pass
            
            
    def value(self) -> Optional[int]:
        """ Implemented by concrete classes """        
        pass
        
    @property
    def type_str(self) -> str:
        """ Implemented by concrete classes """        
        pass
        
    @property
    def is_service(self) -> bool:
        """ Implemented by concrete classes """        
        pass
        
    
    @property    
    def fte(self) -> int:
        """ Implemented by concrete classes """        
        pass
    
    @property      
    def project_days(self) -> float:
        """ Duration times by fte """
        return self.duration * self.fte / 100.0
    
    @property  
    def committed_days(self) -> float:
        """ Returns the committed effort in days from any allocation on this project """
        return sum(a.effort for a in RSEAllocation.objects.filter(project=self))
        
    @property
    def remaining_days(self) -> float:
        """ Return the number of unallocated (i.e. remaining) days for project """
        return self.project_days - self.committed_days
        
    @property
    def remaining_days_at_fte(self) -> float:
        """ Return the number of unallocated (i.e. remaining) days for project at the projects standard fte percentage"""
        return self.remaining_days / self.fte * 100
        
    @property            
    def percent_allocated(self) -> float:
        """ Gets all allocations for this project and sums FTE*days to calculate committed effort """
        return round(self.committed_days / self.project_days * 100, 2)
        
        
            
        
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
    Allocations may span beyond project start and end dates as RSE salary cost may be less than what was costed on project
    """
    percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])   # FTE percentage
    OVERHEAD_CHOICES = (
        ('N', 'None'),
        ('U', 'UKRI'),
        ('E', 'EU'),
    )
    overheads = models.CharField(max_length=1, choices=OVERHEAD_CHOICES, default='N')  # Overhead type
    salary_band = models.ForeignKey(SalaryBand, on_delete=models.PROTECT)  # Don't allow salary band deletion if there are allocations associated with it

    @property
    def duration(self) -> int:
        """
        Duration is determined by start and end dates
        """
        dur = None
        if self.end and self.start:
            dur = (self.end - self.start).days
        return dur
    
    def value(self) -> float:
        """
        Value is determined by project duration and salary cost of salary band used for costing
        """
        
        return self.salary_band.staff_cost(self.start, self.end, percentage=self.percentage)

    
    @property    
    def type_str(self) -> str:
        """
        Returns a plain string representation of the project type
        """
        return "Allocated"
        
    @property
    def is_service(self) -> bool:
        """ Implemented by concrete classes """        
        return False
    
    @property    
    def fte(self) -> int:
        """ Returns the FTE equivalent for this project """        
        return self.percentage
    
class ServiceProject(Project):
    """
    ServiceProject is a number of service days in which work should be undertaken. The projects dates set parameters for which the work can be undertaken but do not define the exact dates in which the work will be conducted. An allocation will convert the service days into an FTE equivalent so that time can be scheduled including holidays.
    """
    days = models.IntegerField(default=1)                           # duration in days
    rate = models.DecimalField(max_digits=8, decimal_places=2)      # service rate 
    
    @property
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
        return self.days*self.rate
      
    @property
    def type_str(self) -> str:
        """
        Returns a plain string representation of the project type
        """
        return "Service"
    
    @property
    def is_service(self) -> bool:
        """ Implemented by concrete classes """        
        return True
    
    @property    
    def fte(self) -> int:
        """ Returns the FTE equivalent (always 100% days) """        
        return 100


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
           
    @property    
    def effort(self) -> float:
        """
        Returns the number of days allocated on project (multiplied by fte)
        """
        return self.duration* self.percentage / 100.0

    @property
    def project_allocation_percentage(self) -> float:
        """ Returns the percentage of this allocation from project total """
        return self.effort / self.project.project_days *100.0

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
        
    @staticmethod
    def min_allocation_start() -> date:
        """ Returns the first start date for all allocations (i.e. the first allocation in the database) """
        return RSEAllocation.objects.aggregate(Min('start'))['start__min']
    
    @staticmethod
    def max_allocation_end() -> date:
        """ Returns the last end date for all allocations (i.e. the last allocation end in the database) """
        return RSEAllocation.objects.aggregate(Max('end'))['end__max']
    
    @staticmethod    
    def commitment_summary(allocations : 'RSEAllocation', from_date: date = None, until_date : date = None):
        
        # TODO: Return exclusive date in which RSE effort changes with list of allocations maintained
        # I.e. (date, FTE, (allocations))
        
        
        # Helpful lambda function for max where a value may be None
        # lambda function returns a if b is None or f(a,b) if b is not none
        f_bnone = lambda f, a, b: a if b is None else f(a, b)  
        
        # Generate a list of start and end dates and store the percentage FTE effort (negative for end dates)
        starts = [[f_bnone(max, item.start, from_date), item.percentage, item] for item in allocations]
        ends = [[f_bnone(min, item.end, until_date), -item.percentage, item] for item in allocations]

        # Combine start and end dates and sort
        events = sorted(starts + ends, key=lambda x: x[0])
        
        # iterate dates (d), percentages (p) and allocations (a) and accumulate allocations
        cumulative_allocations = []
        active_allocations = []
        for d, p, a in events:
            # add or remove allocation depending on percentage
            if p > 0 :
                active_allocations.append(a)
            if p < 0 :
                active_allocations.remove(a)
            # add list of allocations to to cumulative allocations
            cumulative_allocations.append(list(active_allocations))
            
        # Accumulate effort by unpacking events and then apply prefix sum to deltas (FTE accumulations)
        dates, deltas, allocs = zip(*events)
        effort = list(it.accumulate(deltas))
        
        # return list of (date, effort, [RSEAllocation])
        return list(zip(dates, effort, cumulative_allocations))
    


from datetime import date, timedelta
from django.utils import timezone
from math import floor
from typing import Optional, Dict
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.utils import OperationalError, ProgrammingError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from polymorphic.models import PolymorphicModel
from django.db.models import Max, Min, QuerySet
from typing import Iterator, Union, TypeVar, Generic
import itertools as it
from copy import deepcopy

# import the logging library for debugging
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Class for typed query set to be used in type hints
T = TypeVar("T")


class TypedQuerySet(Generic[T]):
    """
    Django type hints for query sets are not typed (not very usefull).
    The following class can eb used to provide type information (see: https://stackoverflow.com/a/54797356)
    """
    def __iter__(self) -> Iterator[Union[T, QuerySet]]:
        pass


class SalaryValue():
    """
    Class to represent a salary calculation.
    Has a salary aa dictionary for each to log how the salary/overhead was calculated (for each chargable period)
    """
    def __init__(self):
        self.staff_cost = 0
        self.cost_breakdown = []
        self.allocation_breakdown = {}

    def add_staff_cost(self, salary_band, from_date: date, until_date: date, percentage: float = 100.0):
        cost_in_period = SalaryBand.salaryCost(days=(until_date - from_date).days, salary=salary_band.salary, percentage=percentage)
        self.staff_cost += cost_in_period
        self.cost_breakdown.append({'from_date': from_date, 'until_date': until_date, 'percentage': percentage, 'salary_band': deepcopy(salary_band), 'staff_cost': cost_in_period})

    def add_salary_value_with_allocation(self, allocation, salary_value):
        self.staff_cost += salary_value.staff_cost
        self.allocation_breakdown[allocation] = salary_value.cost_breakdown
        self.cost_breakdown.extend(salary_value.cost_breakdown)

    @property
    def value(self) -> float:
        return self.staff_cost


# Start of the models

class FinancialYear(models.Model):
    """
    Year represents a financial year starting in August of the year field (not an academic year of Sept to Sept).
    """
    year = models.IntegerField(primary_key=True)  # Must relate to a financial year
    
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

    @property
    def short_str(self) -> str:
        return f"{self.grade}.{self.grade_point} ({self.year})"

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
        Normal behavior is to use the next years financial data. If there is no next year financial data then the current years financial data is used.
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
            # Assume 3% inflation (modify salary but DO NOT SAVE)
            self.salary = round(Decimal(float(self.salary) * 1.03), 2)
            self.estimated = True
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
            return False

        return SalaryBand.spans_calendar_year(start, end) or SalaryBand.spans_financial_year(start, end)

    @staticmethod
    def salaryCost(days, salary, percentage: float = 100.0) -> float:
        """
        Returns the salary cost for a number of days given a salary and FTE percentage
        """
        return (days / 365.0) * float(salary) * (float(percentage) / 100.0)

    def staff_cost(self, start: date, end: date, percentage: float = 100.0) -> SalaryValue:
        """
        Gets the staff cost for this salary band by considering any future increments
        Start must be a date in the current financial year in which this salary band represents
        End (up to not including )can be any date after start and may require increments
        
        Function operates in same way as salary_band_at_future_date

        TODO: Salary band can not calculate a staff cost as it will not account for salary grade changes
        """

        # Check for obvious stupid
        if end < start:
            raise ValueError('End date is before start date')

        # Now calculate the staff costs through iteration of chargeable periods (applying any increments)
        # Note salary band data may be estimated in future years so the date of increment must be tracked rather than just the salary band
        next_increment = start
        next_sb = self
        salary_value = SalaryValue()

        # If the salary can change between the date range then advance increment or year
        while (SalaryBand.spans_salary_change(next_increment, end)):

            # Calculate next increment date
            if next_increment.month < 8:   # If date is before financial year then date range spans financial year  
                temp_next_increment = date(next_increment.year, 8, 1)  # calculate next increment date and salary band
            else: # Doesn't span financial year so must span calendar year
                temp_next_increment = date(next_increment.year + 1, 1, 1)

            # Update salary cost
            salary_value.add_staff_cost(salary_band=next_sb, from_date=next_increment, until_date=temp_next_increment, percentage=percentage)

            # Calculate the next salary band
            # This cant be done before cost calculation salary_band_next_financial_year may modify the next_sb object
            if next_increment.month < 8:  # If date is before financial year then date range spans financial year
                next_sb = next_sb.salary_band_next_financial_year()
            else:  # Doesn't span financial year so must span calendar year
                next_sb = next_sb.salary_band_after_increment()

            # update chargeable period date and band
            next_increment = temp_next_increment

        # Final salary cost for period not spanning a salary change
        salary_value.add_staff_cost(salary_band=next_sb, from_date=next_increment, until_date=end, percentage=percentage)

        return salary_value

    def days_from_budget(self, start: date, budget: float, percent: float) -> int:
        """
        Get the number of days which this salary band can be charged given a budget and FTE
        TODO: Needs to account for salary grade changes which may occur within period
        """

        total_days = 0
        temp_budget = budget
        temp_start = start
        temp_salary_band = self

        # Loop through salary periods to calculate how many days the budget can afford
        # Apply increments and financial year changes
        while temp_budget > 0:
            # calculate date of next possible salary change (either by financial or calendar  year)
            if temp_start.month < 8:
                span_end = date(temp_start.year, 8, 1)
                next_sb = temp_salary_band.salary_band_next_financial_year()
            else:
                span_end = date(temp_start.year + 1, 1, 1)
                next_sb = temp_salary_band.salary_band_after_increment()

            # daily salary rate in span
            span_dr = float(temp_salary_band.salary) / 365.0
            span_days = (span_end - temp_start).days
            span_spend = span_dr * span_days * (percent / 100.0)

            # can budget be spent within this period
            if span_spend >= temp_budget:
                # calculate exactly how many days can be afforded within this period and end loop
                total_days += int(temp_budget / (span_dr * (percent / 100.0)))
                temp_budget = 0     # end loop
                break
            else:
                # accumulate days and deduct cost for this period and move to next
                total_days += span_days
                temp_budget -= span_spend
                temp_start = span_end
                temp_salary_band = next_sb

        return total_days


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

    class Meta:
        """ Order clients by name """
        ordering = ["name"]


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
        """ Returns the current capacity of an RSE as a percentage of FTE. Only includes funded projects. """
        now = timezone.now().date()
        return sum(a.percentage for a in RSEAllocation.objects.filter(rse=self, start__lte=now, end__gt=now, project__status='F'))

    def lastSalaryGradeChange(self, date: date = timezone.now()):
        """
        Gets the last salary grade change before the specified date (i.e. the last appropriate grade change)
        """
        sgcs = SalaryGradeChange.objects.filter(rse=self).order_by('-salary_band__year')
        for sgc in sgcs:
            if sgc.date <= date:
                return sgc
        # Unable to find any data
        raise ValueError('No Salary Data exists before specified date period for this RSE')

    def firstSalaryGradeChange(self):
        """
        Gets the last salary grade change before the specified date (i.e. the last appropriate grade change)
        """
        sgcs = SalaryGradeChange.objects.filter(rse=self).order_by('-salary_band__year')
        if len(sgcs) > 0:
            return sgcs[0]
        else:
            raise ValueError('No Salary Data exists for this RSE')

    def futureSalaryBand(self, date: date):
        """
        Gets the last valid salary grade change event.
        Predicts salary data for provided date by incrementing.
        This may be based on real grade changes in the future or estimated from current financial year increments (see `salary_band_after_increment` notes in `SalaryBand`)
        """
        return self.lastSalaryGradeChange(date).salary_band_at_future_date(date)

    def employed_in_financial_year(self, year: int):
        """
        Returns True is the rse employment starts in the given financial year
        """
        if self.employed_from.month >= 8:
            if self.employed_from.year == year:
                return True
            else:
                return False
        else:
            if self.employed_from.year == year+1:
                return True
            else:
                return False

    def staff_cost(self, from_date: date, until_date: date, percentage:float = 100):

        # Restrict from and until dates based off employment start and end
        if self.employed_from > from_date:
            from_date = self.employed_from
        if self.employed_until < until_date:
            until_date = self.employed_until

        # Get the last salary grade charge for the RSE at the start of the cost query
        sgc = self.lastSalaryGradeChange(from_date)

        # Get the salary band at the start date of the cost query (will skip increments if required)
        sb = sgc.salary_band_at_future_date(from_date)

        # TODO: skip increments if from date is start of employment

        # Now calculate the staff costs through iteration of chargeable periods (applying any increments)
        # Note salary band data may be estimated in future years so the date of increment must be tracked rather than just the salary band
        next_increment = from_date
        next_sb = sb
        salary_value = SalaryValue()

        # Salary can change due to increment or a salary grade change
        while SalaryBand.spans_salary_change(next_increment, until_date) or sgc.spans_salary_grade_change(next_increment, until_date):

            # Need to know if grade change occurs before increment
            temp_sgc = sgc.next_salary_grade_change(next_increment, until_date)
            # if there is another salary grade change and this occurs before any increment
            if temp_sgc and not SalaryBand.spans_salary_change(next_increment, temp_sgc.date):
                temp_next_increment = temp_sgc.date
                # calculate cost up to sgc
                salary_value.add_staff_cost(salary_band=next_sb, from_date=next_increment, until_date=temp_next_increment, percentage=percentage)
                # set the salary band and update the current salary grade change
                next_sb = temp_sgc.salary_band
                sgc = temp_sgc

            # Calculate next increment date
            elif next_increment.month < 8:   # If date is before financial year then date range spans financial year  
                temp_next_increment = date(next_increment.year, 8, 1)  # calculate next increment date and salary band
                # Update salary cost
                salary_value.add_staff_cost(salary_band=next_sb, from_date=next_increment, until_date=temp_next_increment, percentage=percentage)
                # Calculate the next salary band - this cant be done before cost calculation salary_band_next_financial_year may modify the next_sb object
                next_sb = next_sb.salary_band_next_financial_year()

            else: # Doesn't span financial year so must span calendar year
                temp_next_increment = date(next_increment.year + 1, 1, 1)
                # Update salary cost
                salary_value.add_staff_cost(salary_band=next_sb, from_date=next_increment, until_date=temp_next_increment, percentage=percentage)
                # only update the salary band if eliable for increment
                if sgc.eliagable_for_increment(temp_next_increment):
                    # Calculate the next salary band - this cant be done before cost calculation salary_band_next_financial_year may modify the next_sb object
                    next_sb = next_sb.salary_band_after_increment()
                

            # update chargeable period date and band
            next_increment = temp_next_increment

        # Final salary cost for period not spanning a salary change
        salary_value.add_staff_cost(salary_band=next_sb, from_date=next_increment, until_date=until_date, percentage=percentage)

        return salary_value

    @property
    def colour_rbg(self) -> Dict[str, int]:
        r = hash(self.user.first_name) % 255
        g = hash(self.user.last_name) % 255
        b = hash(self.user.first_name + self.user.last_name) % 255
        return {"r": r, "g": g, "b": b}


class SalaryGradeChange(models.Model):
    """
    SalaryGradeChange represents a change (or initial setting) of an RSE salary band
    A SalaryGradeChange may be required where there is promotion or exceptional progression through grade bands.
    All salary grade changes are assumed to be from 1st August as this is the date in which finical year runs.
    This is different to annual increments which occur in January and are considered when calculating salary.

    """
    rse = models.ForeignKey(RSE, on_delete=models.CASCADE)
    salary_band = models.ForeignKey(SalaryBand, on_delete=models.PROTECT)
    date = models.DateField()

    def is_starting_salary(self):
        """
        Returns True if this is the first salary grade change for a given RSE.
        If True this represents the starting salary.
        """
        # get any salary grade changes which may occur before this date
        sgcs = SalaryGradeChange.objects.filter(rse=self.rse, date__lt=self.date)

        if sgcs:
            return False
        else:
            return True

    def eliagable_for_increment(self, date:date):
        """
        Staff are only eliagable for increment if starting grade change occurs within first six months of the year
        """
        if self.is_starting_salary() and self.date.month > 7 and date.year <= self.date.year+1:
            return False
        else:
            return True


        

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
        next_increment = sgc.date  #  date of the salary grade change
        next_sb = sgc.salary_band
        # First increment should be skipped if this salary grade change is the first and represents employment in last six months of the year
        # Note: August adjustment is not skipped if employed in June
        skip_increment = False
        if sgc.is_starting_salary() and sgc.date.month >=7:
            skip_increment = True

        # If the salary can change between the date range then advance increment or year
        while (SalaryBand.spans_salary_change(next_increment, future_date)):
            # If date is before financial year then date range spans financial year
            if next_increment.month < 8:
                next_increment = date(next_increment.year, 8, 1)
                next_sb = next_sb.salary_band_next_financial_year()
            # Doesn't span financial year so must span calendar year
            else:
                next_increment = date(next_increment.year + 1, 1, 1)
                if skip_increment:
                    skip_increment = False 
                else:
                    next_sb = next_sb.salary_band_after_increment()

        return next_sb

    def spans_salary_grade_change(self, start: date, end: date) -> bool:
        """
        Calculates if a salary change change occurs between the dates
        """

        # get any possible salary grade change which occur within date range
        sgcs = SalaryGradeChange.objects.filter(rse=self.rse, date__gt=start, date__lte=end)

        if sgcs:
            return True
        else:
            return False

    def next_salary_grade_change(self, start: date, end: date) -> bool:
        """
        Returns the next salary grade change if there is one or None
        """
        # get any possible salary grade change which occur within date range
        sgcs = SalaryGradeChange.objects.filter(rse=self.rse, date__gt=start, date__lte=end).order_by('-date')
        if sgcs:
            return sgcs[0]
        else:
            return None


    def __str__(self) -> str:
        return (f"{self.rse.user.first_name} {self.rse.user.last_name}: Grade "
                f"{self.salary_band.grade}.{self.salary_band.grade_point}"
                f"({self.salary_band.year})")


class Project(PolymorphicModel):
    """
    Project represents a project undertaken by RSE team.
    Projects are not abstract but should not be initialised without using either a AllocatedProject or ServiceProject (i.e. Multi-Table Inheritance). The Polymorphic django utility is used to make inheritance much cleaner.
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
    STATUS_CHOICES_TEXT_KEYS = (
        ('Preparation', 'Preparation'),
        ('Review', 'Review'),
        ('Funded', 'Funded'),
        ('Rejected', 'Rejected'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    SCHEDULE_ACTIVE = "Active"
    SCHEDULE_COMPLETED = "Completed"
    SCHEDULE_SCHEDULED = "Scheduled"
    SCHEDULE_CHOICES_TEXT_KEYS = (
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Scheduled', 'Scheduled'),
    )

    @property
    def chargable(self):
        """ Indicates if the project is chargable in a cost distribution. I.e. Internal projects are not chargable and neither are non charged service projects. """
        pass

    @staticmethod
    def status_choice_keys():
        """ Returns the available choices for status field """
        return [Project.PREPARATION, Project.REVIEW, Project.FUNDED, Project.REJECTED]

    @property
    def duration(self) -> Optional[int]:
        """ Implemented by concrete classes """
        pass

    def value(self) -> Optional[int]:
        """ Implemented by concrete classes."""
        pass

    def staff_budget(self) -> float:
        """ Implemented by concrete classes."""
        pass

    def overhead_value(self, from_date: date = None, until_date: date = None, percentage: float = None) -> float:
        """ Implemented by concrete classes. """
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

    @property
    def get_schedule_display(self) -> str:
        now = timezone.now().date()
        if now < self.start:
            return Project.SCHEDULE_SCHEDULED
        elif now > self.end:
            return Project.SCHEDULE_COMPLETED
        else:
            return Project.SCHEDULE_ACTIVE

    def __str__(self):
        return self.name

    def clean(self):
        if self.status != 'P' and not self.proj_costing_id:
            raise ValidationError(_('Project proj_costing_id cannot be null if the grant has passed the preparation stage.'))
        if self.start and self.end and self.end < self.start:
            raise ValidationError(_('Project end cannot be earlier than project start.'))

    @staticmethod
    def min_start_date() -> date:
        """
        Returns the first start date for all allocations (i.e. the first allocation in the database)
        It is possible that the database does not exist when this function is called in which case function returns todays date.
        """
        try:
            min_date =  Project.objects.aggregate(Min('start'))['start__min']
            if min_date is None: # i.e. table exists but no dates
                min_date = timezone.now().date()
            return min_date
        except (OperationalError, ProgrammingError):
            return timezone.now().date()

    @staticmethod
    def max_end_date() -> date:
        """
        Returns the last end date for all allocations (i.e. the last allocation end in the database)
        It is possible that the database does not exist when this function is called in which case function returns todays date.
        """
        try:
            max_date = Project.objects.aggregate(Max('end'))['end__max']
            if max_date is None: # i.e. table exists but no dates
                max_date = timezone.now().date()
            return max_date
        except (OperationalError, ProgrammingError):
            return timezone.now().date()

    def staff_cost(self, from_date: date = None, until_date: date = None, rse: RSE = None, consider_internal: bool = False) -> SalaryValue:
        """
        Returns the accumulated staff costs (from allocations) over a duration (if provided) or for the full project if not
        """

        # don't consider internal projects
        if not consider_internal and self.internal:
            return SalaryValue()

        # If no time period then use defaults for project
        # then limit specified time period to allocation
        if from_date is None or from_date < self.start:
            from_date = self.start
        if until_date is None or until_date > self.end:
            until_date = self.end

        # Filter allocations by start and end date
        if rse:
            allocations = RSEAllocation.objects.filter(project=self, end__gt=from_date, start__lt=until_date, rse=rse)
        else:
            allocations = RSEAllocation.objects.filter(project=self, end__gt=from_date, start__lt=until_date)

        # Iterate allocations and calculate staff costs
        salary_cost = SalaryValue()
        for a in allocations:

            # calculate the staff cost of the RSE between the date range given the salary band at the start of the cost query
            sc = a.staff_cost(from_date, until_date)

            # append the salary costs logging costs by allocations5
            salary_cost.add_salary_value_with_allocation(allocation=a, salary_value=sc)

        return salary_cost

    @property
    def colour_rbg(self) -> Dict[str, int]:
        r = hash(self.name) % 255
        g = hash(self.start) % 255
        b = hash(self.end) % 255
        return {"r": r, "g": g, "b": b}


class AllocatedProject(Project):
    """
    AllocatedProject is a cost recovery project used to allocate an RSE for a percentage of time given the projects start and end dates
    Allocations may span beyond project start and end dates as RSE salary cost may be less than what was costed on project
    """
    percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])   # FTE percentage
    overheads = models.DecimalField(max_digits=8, decimal_places=2)        # Overheads are a pro rata amount per year
    salary_band = models.ForeignKey(SalaryBand, on_delete=models.PROTECT)  # Don't allow salary band deletion if there are allocations associated with it

    @property
    def chargable(self):
        """ Indicates if the project is chargable in a cost distribution. I.e. Internal projects are not chargable."""
        return not self.internal

    @property
    def duration(self) -> Optional[int]:
        """
        Duration is determined by start and end dates
        """
        dur = None
        if self.end and self.start:
            dur = (self.end - self.start).days
        return dur

    def value(self) -> float:
        """
        Value represent staff costs and overhead is determined by project duration and salary cost of salary band used for costing
        """

        salary_costs = self.salary_band.staff_cost(self.start, self.end, percentage=self.percentage)
        overheads = self.overhead_value()

        return salary_costs.staff_cost + overheads

    def staff_budget(self) -> float:
        """
        Function to calculate staff budget for an allocation project.
        Represents total of salary costs for duration of project
        """
        salary_costs = self.salary_band.staff_cost(self.start, self.end, percentage=self.percentage)

        return salary_costs.staff_cost

    def overhead_value(self, from_date: date = None, until_date: date = None, percentage: float = None) -> float:
        """
        Function calculates the value of any overheads generated.
        For allocated projects this is based on duration and a fixed overhead rate.
        Cap the from and end dates according to the project as certain queries may have dates based on financial years rather than project dates
        """

        # internal projects have no overheads
        if self.internal:
            return 0

        if from_date is None or from_date < self.start:
            from_date = self.start
        if until_date is None or until_date > self.end:
            until_date = self.end
        if percentage is None or percentage > 100.0:
            percentage = self.percentage

        # Use the static salary band function to convert days and rate into a value
        return SalaryBand.salaryCost(days=(until_date - from_date).days, salary=self.overheads, percentage=percentage)

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
    charged = models.BooleanField(default=True)                     # Should staff time be charged to serice account
    invoice_received = models.DateField(null=True, blank=True)

    @property
    def chargable(self):
        """ Indicates if the project is chargable in a cost distribution. I.e. Internal projects are not chargable and neither are non charged service projects. """
        return not self.internal and charged

    @staticmethod
    def days_to_fte_days(days: int) -> int:
        """
        Duration is determined by number of service days adjusted for weekends and holidays
        This maps service days (of which there are 220 TRAC working days) to a FTE duration
        """
        return floor(days * (365.0 / 220.0))
    
    @property
    def duration(self) -> int:
        """
        Use the avilable static method to convert days to FTE days
        """
        return ServiceProject.days_to_fte_days(self.days)

    def value(self) -> float:
        """
        Value is determined by service days multiplied by rate
        """
        return self.days * float(self.rate)

    def staff_budget(self) -> float:
        """
        Service projects don't have a staff budget as they have a number of service days.
        Returns the project value (which includes overheads) which could in theory be entirely used to fund staff time.
        """
        return self.value()

    def overhead_value(self, from_date: date = None, until_date: date = None, percentage: float = None):
        """
        Function calculates the value of any overheads generated.
        For service projects there is no overhead just a surplus depending on staff costs and invoice date. As such this function should not be used for service projects.
        """
        # Use the static salary band function to convert days and rate into a value
        return 0

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


class RSEAllocationManager(models.Manager):
    """
    RSEAllocation objects are transactional in that they are never actually deleted they are just flagged as deleted
    This custom manager allows all() to return on objects which have not been flagged as deleted 
    """
    def get_queryset(self):
        return super(RSEAllocationManager, self).get_queryset().filter(deleted_date__isnull=True)

    def all(self, deleted=False):
        if deleted:
            return super(RSEAllocationManager, self).get_queryset()
        else:
            # default is to return only non deleted items
            return self.get_queryset()

class RSEAllocation(models.Model):
    """
    Defines an allocation of an RSE to project with a given percentage of time.
    RSEAllocation objects are transactional in that they are never actually deleted they are just flagged as deleted.
    """
    rse = models.ForeignKey(RSE, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    percentage = models.FloatField(validators=[MinValueValidator(0),
                                               MaxValueValidator(100)])
    start = models.DateField()
    end = models.DateField()

    created_date = models.DateTimeField(default=timezone.now, editable=False)
    deleted_date = models.DateTimeField(null=True, blank=True)

    objects = RSEAllocationManager()

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
        return self.duration * self.percentage / 100.0

    @property
    def project_allocation_percentage(self) -> float:
        """ Returns the percentage of this allocation from project total """
        return self.effort / self.project.project_days * 100.0

    @property
    def current_progress(self) -> float:
        """ Returns the current progress of the allocation as a percentage """
        now = timezone.now().date()

        # not started
        if self.start > now:
            return 0.0
        # completed
        elif self.end < now:
            return 100.0

        # otherwise active
        total_days = (self.end - self.start).days
        current_days = (now - self.start).days

        return float(current_days) / float(total_days) * 100

    def staff_cost(self, start=None, end=None) -> SalaryValue:
        """
        Returns the cost of a member of staff over a duration (if provided) or for full allocation if not
        """
        # If no time period then use defaults for project
        # then limit specified time period to allocation
        if start is None or start < self.start:
            start = self.start
        if end is None or end > self.end:
            end = self.end

        # Get the last salary grade charge for the RSE at the start of the cost query
        sgc = self.rse.lastSalaryGradeChange(start)
        # Get the salary band at the start date of the cost query
        sb = sgc.salary_band_at_future_date(start)

        # calculate the staff cost of the RSE between the date range given the salary band at the start of the cost query
        salary_cost = sb.staff_cost(start, end, self.percentage)

        return salary_cost

    @staticmethod
    def min_allocation_start() -> date:
        """
        Returns the first start date for all allocations (i.e. the first allocation in the database)
        It is possible that the database does not exist when this function is called in which case function returns todays date.
        """
        try:
            return RSEAllocation.objects.aggregate(Min('start'))['start__min']
        except OperationalError:
            return timezone.now().date()

    @staticmethod
    def max_allocation_end() -> date:
        """
        Returns the last end date for all allocations (i.e. the last allocation end in the database)
        It is possible that the database does not exist when this function is called in which case function returns todays date.
        """
        try:
            return RSEAllocation.objects.aggregate(Max('end'))['end__max']
        except OperationalError:
            return timezone.now().date()

    @staticmethod
    def commitment_summary(allocations: 'RSEAllocation', from_date: date = None, until_date: date = None):

        # Helpful lambda function for max where a value may be None
        # lambda function returns a if b is None or f(a,b) if b is not none
        f_bnone = lambda f, a, b: a if b is None else f(a, b)

        # Generate a list of start and end dates and store the percentage FTE effort (negative for end dates)
        starts = [[f_bnone(max, item.start, from_date), item.percentage, item] for item in allocations]
        ends = [[f_bnone(min, item.end, until_date), -item.percentage, item] for item in allocations]

        # Combine start and end dates and sort
        events = sorted(starts + ends, key=lambda x: x[0])

        # lists of unique
        unique_cumulative_allocations = []
        unique_dates = []
        unique_effort = []

        # temporary cumulative variables
        active_allocations = []
        effort = 0

        # use itertools groupby to process by unique day
        for k, g in it.groupby(events, lambda x: x[0]):

            # iterate dates (d), percentages (p), effort (e), and allocations (a) and accumulate allocations
            for d, p, a in g:  # k will be the same a d
                # add or remove allocation depending on percentage
                if p > 0:
                    active_allocations.append(a)
                if p < 0:
                    active_allocations.remove(a)

                # accumulate effort
                effort += p

            # add date to unique
            unique_dates.append(d)
            unique_effort.append(effort)
            # add list of allocations to to unique cumulative allocations (make a copy)
            unique_cumulative_allocations.append(list(active_allocations))

        # Return list of unique (date, effort, [RSEAllocation])
        return list(zip(unique_dates, unique_effort, unique_cumulative_allocations))

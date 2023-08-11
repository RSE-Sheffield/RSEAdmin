from django import forms
from datetime import datetime, timedelta
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.validators import RegexValidator
from django.conf import settings

from .models import *


class DateRangeField(forms.Field):
    """
    Class is used to extend a text field by being able to parse the text and extract the date ranges
    init function used to store min and max date for future use without querying database
    If validation fails then min max date range is returned
    
    The date string should be one of the following formats:
    - "yyyy-MM-dd"
    - "dd/MM/yyyy"
    
    """

    def __init__(self, *args, **kwargs):
        if 'min_date' not in kwargs:
            raise TypeError("DateRangeField missing required argument: 'min_date'")
        if 'max_date' not in kwargs:
            raise TypeError("DateRangeField missing required argument: 'max_date'")
        self.min_date = kwargs.pop('min_date')
        self.max_date = kwargs.pop('max_date')
        super(DateRangeField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        # if not value then get min and max date
        if not value:
            return [self.min_date, self.max_date]

        # create a list of date items (one for start and one for until)
        fromuntil = value.split(' - ')
        
        if len(fromuntil) != 2:
            return [self.min_date, self.max_date]
        
        try:
            date_from = datetime.strptime(fromuntil[0], '%d/%m/%Y').date()
            date_until = datetime.strptime(fromuntil[1], '%d/%m/%Y').date()
        except ValueError:
            # try with different date format
            try:
                date_from = datetime.strptime(fromuntil[0], '%Y-%m-%d').date()
                date_until = datetime.strptime(fromuntil[1], '%Y-%m-%d').date()
            except ValueError:
                return [self.min_date, self.max_date]
        
        return [date_from, date_until]

    def validate(self, value):
        if len(value) != 2:
            forms.ValidationError('Date range is in wrong format')


class UsersFilterForm(forms.Form):
    """
    Class represents a filter form for filtering by Active and Staff status
    Values for options does not use database character keys as tables are filtered directly at client side (in the data table)
    """

    active_filter = forms.ChoiceField(
        choices=(('', 'All'), ('Yes', 'Yes'), ('No', 'No')),
        widget=forms.Select(attrs={'class': 'form-control'}))
    staff_filter = forms.ChoiceField(choices= (('', 'All'), ('Yes', 'Yes'), ('No', 'No')),
                                      widget=forms.Select(attrs={'class': 'form-control'}))


class FilterDateRangeForm(forms.Form):
    """
    Class represents a date range field using the javascript daterangepicker library.
    It is specific to the RSEAdmin tool as it enables min and max allocated dates to be queries.
    Property functions are used to be able to obtain date ranges without cluttering views.
    """

    min_date = Project.min_start_date()
    max_date = Project.max_end_date()

    # Use custom date range field
    filter_range = DateRangeField(label='Date Range',
                                  widget=forms.TextInput(attrs={'class': 'form-control pull-right'}),
                                  min_date=min_date, max_date=max_date)

    @property
    def from_date(self):
        return self.cleaned_data["filter_range"][0]

    @property
    def until_date(self):
        return self.cleaned_data["filter_range"][1]

    @property
    def years(self):
        return FinancialYear.objects.all().order_by('year')


class FilterDateForm(forms.Form):
    """
    Class represents a date field using the javascript daterangepicker library .
    It is specific to the RSEAdmin tool as it default date is set to settings.HOME_PAGE_DAYS_RECENT (default 30).
    """

    from_date = forms.DateField(widget=forms.DateInput(format=('%d/%m/%Y'),
                                attrs={'class': 'form-control'}),
                                input_formats=('%d/%m/%Y',))

    def __init__(self, *args, **kwargs):
        """ Set the initial date """
        super(FilterDateForm, self).__init__(*args, **kwargs)
        self.initial_date = datetime.now() - timedelta(days=settings.HOME_PAGE_DAYS_RECENT)
        self.fields['from_date'].initial = datetime.strftime(self.initial_date, '%d/%m/%Y')


class ProjectTypeForm(forms.Form):
    """
    Class represents a filter form for filtering by date range and service type used by many views which display multiple project views.
    Extends the filter range form by adding type and status fields
    """

    type = forms.ChoiceField(choices=(('S', 'Service'), ('D', 'Directly Incurred')),
                             widget=forms.Select(attrs={'class': 'form-control pull-right'}))


class FilterProjectForm(FilterDateRangeForm):
    """
    Filter form for filtering by date range and service type used by many views
    which display multiple project views.

    Extends the filter range form by adding type and status fields.
    """
    status = forms.ChoiceField(
        choices=(
            ('U', 'Funded, Review and in Preparation'),
            ('A', 'All'),
            ('L', 'Funded and Review')) +
            Project.STATUS_CHOICES,
        initial='F',
        widget=forms.Select(attrs={'class': 'form-control pull-right'})
    )
    
    rse_in_employment = forms.ChoiceField(
        choices=(('All', 'All'), ('Yes', 'Yes'), ('No', 'No')),
        widget=forms.Select(attrs={'class': 'form-control pull-right'})
    )
    # Type cant be filtered at database level as it is a property
    # type = forms.ChoiceField(choices = (('A', 'All'), ('F', 'Allocated'), ('S', 'Service')), widget=forms.Select(attrs={'class': 'form-control pull-right'}))


class ProjectsFilterForm(forms.Form):
    """
    Class represents a filter form for filtering by project type, funding status and schedule
    For use in the projects view which performs responsive datatable queries.
    Values for options doe not use database character keys as tables are filtered directly at client side (in the data table)
    """

    type_filter = forms.ChoiceField(choices=(('', 'All'), ('Directly Incurred', 'Directly Incurred Only'), ('Service', 'Service Only')),
                                    widget=forms.Select(attrs={'class': 'form-control'}))
    status_filter = forms.ChoiceField(choices= (('', 'All'),) + Project.STATUS_CHOICES_TEXT_KEYS,
                                      widget=forms.Select(attrs={'class': 'form-control'}))
    schedule_filter = forms.ChoiceField(choices=(('', 'All'),) + Project.SCHEDULE_CHOICES_TEXT_KEYS,
                                        widget=forms.Select(attrs={'class': 'form-control'}))


class ServiceOutstandingFilterForm(forms.Form):
    """
    Class represents a filter form for filtering by invoice status, funding status and schedule
    For use in the service invoice outstanding view which performs responsive datatable queries.
    Values for options doe not use database character keys as tables are filtered directly at client side (in the data table)
    """

    invoice_filter = forms.ChoiceField(choices=(('', 'All'), ('Outstanding', 'Outstanding'), ('Received', 'Received')),
                                       widget=forms.Select(attrs={'class': 'form-control'}))
    status_filter = forms.ChoiceField(choices=(('', 'All'),) + Project.STATUS_CHOICES_TEXT_KEYS,
                                      widget=forms.Select(attrs={'class': 'form-control'}))
    schedule_filter = forms.ChoiceField(choices=(('', 'All'),) + Project.SCHEDULE_CHOICES_TEXT_KEYS,
                                        widget=forms.Select(attrs={'class': 'form-control'}))


class ProjectAllocationForm(forms.ModelForm):
    """
    Form for adding and editing allocations within a project. Uses model form base type.
    Sets the start and end day of the allocation as follows
    - Start day is start of project
    - End day is start day plus remaining commitment to the project (by calculating sum of already committed hours) - This may be set by budget for allocated projects using responsive AJAX query.
    """

    # Fields are created manually to set the date input format
    start =  forms.DateField(widget=forms.DateInput(format=('%d/%m/%Y'),
                             attrs={'class': 'form-control'}),
                             input_formats=('%d/%m/%Y',))
    end = forms.DateField(widget=forms.DateInput(format=('%d/%m/%Y'),
                          attrs={'class': 'form-control'}),
                          input_formats=('%d/%m/%Y',))

    def __init__ (self, *args, **kwargs):
        """ Set the initial data """
        if 'project' not in kwargs:
            raise TypeError("ProjectAllocationForm missing required argument: 'project'")
        self.project = kwargs.pop('project', None)
        # call super
        super(ProjectAllocationForm, self).__init__(*args, **kwargs)

        # do stuff with project to set the initial data
        self.fields['percentage'].initial = self.project.fte
        self.fields['start'].initial = datetime.strftime(self.project.start, "%d/%m/%Y")
        # remaining days must be rounded to whole days
        if (self.project.remaining_days_at_fte > 0):
            self.fields['end'].initial = datetime.strftime(self.project.start + timedelta(days=round(self.project.remaining_days_at_fte)), "%d/%m/%Y")
        else:
            self.fields['end'].initial = datetime.strftime(self.project.start, "%d/%m/%Y")

    class Meta:
        model = RSEAllocation
        fields = ['rse', 'percentage', 'start', 'end']
        widgets = {
            'rse': forms.Select(attrs={'class': 'form-control'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'project': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super(ProjectAllocationForm, self).clean()
        errors = {}

        # Check that the RSE has valid Salary data from the start date (i.e. a salary grade change exists which can be used to calculate salary)
        if cleaned_data['start'] and cleaned_data['rse']:
            rse = cleaned_data['rse']
            try:
                rse.futureSalaryBand(date=cleaned_data['start'])
            except ValueError:
                errors['start'] = ("The selected RSE has no salary information within the same financial year as the proposed start date")

        # Check that the RSE is employed for the duration of the allocation
        if cleaned_data['start'] and cleaned_data['start'] and cleaned_data['rse']:
            rse = cleaned_data['rse']
            if not rse.employed_from:
                errors['start'] = ('RSE does not have a start date of employment (i.e. no salary grade change)')
            elif rse.employed_from > cleaned_data['start']:
                errors['start'] = ('Allocation start date is before RSE is employed')
            if rse.employed_until < cleaned_data['end']:
                errors['end'] = ('Allocation end date is after RSE is employed')

        # Validation checks that the dates are correct (no need to raise errors if fields are empty as they are required so superclass will have done this)
        if cleaned_data['start'] and cleaned_data['end']:
            if cleaned_data['start'] > cleaned_data['end']:
                errors['end'] = ('Allocation end date can not be before start date')


        # strict allocations checks
        if settings.STRICT_ALLOCATIONS:
            # Check that the dates are within the current project
            if cleaned_data['start'] < self.project.start:
                errors['start'] = ('Allocation start date can not be before the start date of the project')
            if cleaned_data['start'] > self.project.end:
                errors['start'] = ('Allocation start date can not be after the end date of the project')

            if cleaned_data['end'] > self.project.end:
                errors['end'] = ('Allocation end date can not be after the end date of the project')
            if cleaned_data['end'] < self.project.start:
                errors['end'] = ('Allocation end date can not be before the start date of the project')

        if errors:
            raise ValidationError(errors)


class DirectlyIncurredProjectForm(forms.ModelForm):
    """
    Class for creation and editing of a project
    """

    # Fields are created manually to set the date input format
    start = forms.DateField(widget=forms.DateInput(format = ('%d/%m/%Y'), attrs={'class' : 'form-control'}), input_formats=('%d/%m/%Y',))
    end = forms.DateField(widget=forms.DateInput(format = ('%d/%m/%Y'), attrs={'class' : 'form-control'}), input_formats=('%d/%m/%Y',))

    class Meta:
        model = DirectlyIncurredProject
        fields = ['proj_costing_id', 'name', 'description', 'client', 'internal', 'start', 'end', 'status', 'percentage', 'overheads', 'salary_band', 'created', 'creator']
        widgets = {
            'proj_costing_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'internal': forms.CheckboxInput(),
            'status': forms.Select(choices=Project.STATUS_CHOICES, attrs={'class': 'form-control pull-right'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'overheads': forms.NumberInput(attrs={'class': 'form-control'}),
            'salary_band': forms.Select(attrs={'class': 'form-control'}),
            'creator': forms.HiddenInput(),
            'created': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super(DirectlyIncurredProjectForm, self).clean()
        errors = {}

        # Validation checks that the dates are correct (no need to raise errors if fields are empty as they are required so superclass will have done this)
        if 'start' in cleaned_data and 'end' in cleaned_data:
            if cleaned_data['start'] > cleaned_data['end']:
                errors['end'] = ('Project end date can not be before start date')

        if errors:
            raise ValidationError(errors)

    def clean_start(self):
        """
        Cant change the start date if there are dependant allocations which start before the proposed date
        """
        cleaned_start = self.cleaned_data['start']

        # Cant change start and end date if there are existing allocations outside of the period
        if self.instance:
            # Check validation if using strict allocations
            if settings.STRICT_ALLOCATIONS:
                # check for allocations on project which end after the proposed start date
                should_be_empty = RSEAllocation.objects.filter(project=self.instance, start__lt=cleaned_start)
                if should_be_empty:
                    raise ValidationError('There are current allocations on this project which start before the proposed start date')

        return cleaned_start

    def clean_end(self):
        """
        Cant change the end date if there are dependant allocations which end after the proposed date
        """
        cleaned_end=self.cleaned_data['end']

        # Cant change start and end date if there are existing allocations outside of the period
        if self.instance:
            # Check validation if using strict allocations
            if settings.STRICT_ALLOCATIONS:
                # check for allocations on project which end after the proposed start date
                should_be_empty = RSEAllocation.objects.filter(project=self.instance, end__gt=cleaned_end)
                if should_be_empty:
                    raise ValidationError('There are current allocations on this project which end after the proposed end date')

        return cleaned_end


class ServiceProjectForm(forms.ModelForm):
    """
    Class for creation and editing of a project
    """

    # Fields are created manually to set the date input format
    start = forms.DateField(widget=forms.DateInput(format=('%d/%m/%Y'),
                            attrs={'class': 'form-control'}),
                            input_formats=('%d/%m/%Y',))
    end = forms.DateField(widget=forms.DateInput(format=('%d/%m/%Y'),
                          attrs={'class': 'form-control'}),
                          input_formats=('%d/%m/%Y',))
    invoice_received = forms.DateField(widget=forms.DateInput(format=('%d/%m/%Y'),
                                       attrs={'class': 'form-control'}),
                                       input_formats=('%d/%m/%Y',),
                                       required=False)

    class Meta:
        model = ServiceProject
        fields = ['proj_costing_id', 'name', 'description', 'client', 'internal', 'start', 'end', 'status', 'days', 'rate', 'charged', 'invoice_received', 'created', 'creator']
        widgets = {
            'proj_costing_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'internal': forms.CheckboxInput(),
            'status': forms.Select(choices=Project.STATUS_CHOICES, attrs={'class': 'form-control pull-right'}),
            'days': forms.NumberInput(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'charged': forms.CheckboxInput(),
            'creator': forms.HiddenInput(),
            'created': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super(ServiceProjectForm, self).clean()
        errors = {}

        # Validation checks that the dates are correct (no need to raise errors if fields are empty as they are required so superclass will have done this)
        if 'start' in cleaned_data and 'end' in cleaned_data:
            # end cant be beofre start
            if cleaned_data['start'] > cleaned_data['end']:
                errors['end'] = ('Project end date can not be before start date')

            # duration must be long enough to complete the project
            if cleaned_data['days']:
                fte_days = ServiceProject.days_to_fte_days(cleaned_data['days'])
                duration = (cleaned_data['end'] - cleaned_data['start']).days
                if fte_days > duration:
                    errors['end'] = (f"Project duration is not long enough for the {fte_days} fte days required to deliver {cleaned_data['days']} service days.")

        if errors:
            raise ValidationError(errors)

    def clean_start(self):
        """
        Cant change the start date if there are dependant allocations which start before the proposed date
        """
        cleaned_start = self.cleaned_data['start']

        # Cant change start and end date if there are existing allocations outside of the period
        if self.instance:
            # Check validation if using strict allocations
            if settings.STRICT_ALLOCATIONS:
                # check for allocations on project which end after the proposed start date
                should_be_empty = RSEAllocation.objects.filter(project=self.instance, start__lt=cleaned_start)
                if should_be_empty:
                    raise ValidationError('There are current allocations on this project which start before the proposed start date')

        return cleaned_start

    def clean_end(self):
        """
        Cant change the end date if there are dependant allocations which end after the proposed date
        """
        cleaned_end = self.cleaned_data['end']

        # Cant change start and end date if there are existing allocations outside of the period
        if self.instance:
            # Check validation if using strict allocations
            if settings.STRICT_ALLOCATIONS:
                # check for allocations on project which end after the proposed start date
                should_be_empty = RSEAllocation.objects.filter(project=self.instance, end__gt=cleaned_end)
                if should_be_empty:
                    raise ValidationError('There are current allocations on this project which end after the proposed end date')

        return cleaned_end
        
    def clean_rate(self):
        """
        Check the service rate is greater than 0
        """
        cleaned_rate=self.cleaned_data['rate']

        # Service rate must be greater than 0
        if cleaned_rate <= 0:
            raise ValidationError('The service rate must be greater than 0')

        return cleaned_rate
               
            
class ClientForm(forms.ModelForm):    

    """
    Class for creation and editing of a client
    """
    class Meta:
        model = Client
        fields = ['name', 'department', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'autoComplete'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }


class UserTypeForm(forms.Form):
    """
    Class represents a filter form for filtering by date range and service type used by many views which display multiple project views.
    Extends the filter range form by adding type and status fields
    """

    user_type = forms.ChoiceField(choices=(('A', 'Administrator'), ('R', 'RSE')),
                                  widget=forms.Select(attrs={'class': 'form-control pull-right'}))


class NewUserForm(UserCreationForm):
    """ Class for creating a new user """

    # Field to allow user to be an admin user
    is_admin = forms.BooleanField(initial=False, required=False)

    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        """ Override init to customise the UserCreationForm widget class appearance """

        # see if the user form should be admin
        self.force_admin = kwargs.pop('force_admin', None)

        super(NewUserForm, self).__init__(*args, **kwargs)

        # set html attributes of fields in parent form
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

        # if forced admin
        if self.force_admin:
            self.fields['is_admin'].widget = forms.HiddenInput()

        # set regex validator on username (to comply with URL restriction using username)
        # Why the following does not work is a complete mystery. URL regex has instead been updated to recognise @/./+/-/_ characters
        # self.fields['username'].validators = [RegexValidator(r'[\w]+', 'Only alphanumeric characters are allowed.')]

    def save(self, commit=True):
        """ Override save to make user a superuser """
        user = super(NewUserForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        # make an admin if checked
        if self.cleaned_data["is_admin"] or self.force_admin:
            user.is_superuser = True
        # commit
        if commit:
            user.save()
        return user


class EditUserForm(UserChangeForm):
    """ Class for creating a new user """

    # Field to allow user to be an admin user
    is_admin = forms.BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):
        """ Override init to customise the UserCreationForm widget class appearance """
        super(EditUserForm, self).__init__(*args, **kwargs)

        # if super user then set the is_admin initial value
        if self.instance.is_superuser:
            self.fields['is_admin'].initial = True

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        """ Override save to make user a superuser """
        user = super(EditUserForm, self).save(commit=False)
        # make an admin if checked
        if self.cleaned_data["is_admin"]:
            user.is_superuser = True
        # commit
        if commit:
            user.save()
        return user


class EditRSEUserForm(forms.ModelForm):
    """
    Form to edit an RSE users. This is used alongside the new user form so does not extend it.
    """

    employed_until = forms.DateField(widget=forms.DateInput(format=('%d/%m/%Y'),
                                     attrs={'class': 'form-control'}),
                                     input_formats=('%d/%m/%Y',))

    class Meta:
        model = RSE
        fields = ['employed_until']


class NewRSEUserForm(forms.ModelForm):
    """
    Form for new RSE users. This is used alongside the new user form so does not extend it.
    Same as EditRSEUserForm but with an initial salary band option which is filtered dynamically within javascript
    """

    employed_from = forms.DateField(widget=forms.DateInput(format=('%d/%m/%Y'),
                                    attrs={'class': 'form-control'}),
                                    input_formats=('%d/%m/%Y',))
    employed_until = forms.DateField(widget=forms.DateInput(format=('%d/%m/%Y'),
                                     attrs={'class': 'form-control'}),
                                     input_formats=('%d/%m/%Y',))
    salary_band = forms.ModelChoiceField(queryset=SalaryBand.objects.all(),
                                         empty_label=None,
                                         required=True,
                                         widget=forms.Select(attrs={'class': 'form-control pull-right'}))  # dynamically filtered (JS)

    class Meta:
        model = RSE
        fields = ['employed_until']

    def clean(self):
        """
        Check that the salary grade change is for the correct year of employment
        """
        cleaned_data = super(NewRSEUserForm, self).clean()
        errors = {}

        if cleaned_data['employed_from'] and cleaned_data['employed_until']:
            if cleaned_data['employed_from'] > cleaned_data['employed_until']:
                errors['year'] = ('Employed until date can not be later than employed from date!')

        if errors:
            raise ValidationError(errors)


class NewSalaryBandForm(forms.ModelForm):
    """
    Class represents a form for creating a new salary band with a given year
    """

    def __init__(self, *args, **kwargs):
        # if no instance then we expect a year to set as initial value
        if 'instance' not in kwargs:
            if 'year' not in kwargs:
                raise TypeError("NewSalaryBandForm requires either an 'instance' or a 'year'")
            year = kwargs.pop('year', None)
        else:
            year = kwargs['instance'].year
        super(NewSalaryBandForm, self).__init__(*args, **kwargs)
        self.fields['year'].initial = year

    class Meta:
        model = SalaryBand
        fields = ['grade', 'grade_point', 'year', 'salary', 'increments']
        widgets = {
            'grade': forms.NumberInput(attrs={'class': 'form-control'}),
            'grade_point': forms.NumberInput(attrs={'class': 'form-control'}),
            'year': forms.HiddenInput(),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'increments': forms.CheckboxInput(),
        }


class NewFinancialYearForm(forms.ModelForm):
    """
    Class represents a form for creating a new salary band with a given year
    """
    copy_from = forms.ModelChoiceField(queryset=FinancialYear.objects.all(), 
                                       empty_label="",
                                       required=False,
                                       widget=forms.Select(attrs={'class': 'form-control pull-right'}))

    class Meta:
        model = FinancialYear
        fields = ['year']
        widgets = {
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        """ Override to copy salary band data from previous finanical year """
        financial_year = super(NewFinancialYearForm, self).save(commit=False)

        if commit:
            # save the year
            financial_year.save()

            # copy salary band data
            if self.cleaned_data["copy_from"]:
                copy_year = self.cleaned_data["copy_from"]
                sbs = SalaryBand.objects.filter(year=copy_year)
                for sb in sbs:
                    sb.pk = None  # remove pk to save as new item in database
                    sb.year = financial_year
                    sb.save()

        return financial_year


class SalaryGradeChangeForm(forms.ModelForm):
    """
    Class represents a form for a salary grade change for an RSE
    """

    date = forms.DateField(widget=forms.DateInput(format=('%d/%m/%Y'),
                           attrs={'class': 'form-control'}),
                           input_formats=('%d/%m/%Y',))

    def __init__(self, *args, **kwargs):
        """ Set the initial data """
        if 'rse' not in kwargs:
            raise TypeError("SalaryGradeChangeForm missing required argument: 'rse'")
        rse = kwargs.pop('rse', None)

        # call super
        super(SalaryGradeChangeForm, self).__init__(*args, **kwargs)

        # set RSE (as it is a hidden field)
        self.fields['rse'].initial = rse

        # not required as query set will be dynamically loaded via ajax
        # self.fields['salary_band'].queryset = SalaryBand.objects.all()

    def clean(self):
        cleaned_data = super(SalaryGradeChangeForm, self).clean()
        errors = {}

        if cleaned_data['rse'] and cleaned_data['date']:
            employed_until = cleaned_data['rse'].employed_until
            d = cleaned_data['date']

            # Check that there is not already a salary grade change for the specified year
            financial_year = d.year
            if d.month < 8:
                financial_year -= 1
            if SalaryGradeChange.objects.filter(rse=cleaned_data['rse'], salary_band__year=financial_year):
                errors['date'] = ('A salary grade change for the specified year already exists for the RSE!')

            # Check that the salary grade change is not after the RSE is employed
            if d > employed_until:
                errors['date'] = ('Proposed salary grade change is after the rse is employed')

        if errors:
            raise ValidationError(errors)

    class Meta:
        model = SalaryGradeChange
        fields = ['rse', 'salary_band', 'date']
        widgets = {
            'rse': forms.HiddenInput(),
            'salary_band': forms.Select(attrs={'class': 'form-control pull-right'})  # choices set dynamically
        }

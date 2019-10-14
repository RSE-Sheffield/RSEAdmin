from django import forms
from datetime import datetime, timedelta
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import *


class DateRangeField(forms.Field):
    """
    Class is used to extend a text field by being able to parse the text and extract the date ranges 
    init function used to store min and max date for future use without querying database
    If validation fails then min max date range is returned
    """
    
    def __init__(self, *args,**kwargs):
        if not 'min_date' in kwargs:
            raise TypeError("DateRangeField missing required argument: 'min_date'")
        if not 'max_date' in kwargs:
            raise TypeError("DateRangeField missing required argument: 'max_date'")
        self.min_date = kwargs.pop('min_date')
        self.max_date = kwargs.pop('max_date')
        super(DateRangeField, self).__init__(*args,**kwargs)

    def to_python(self, value):
        # if not value then get min and max date
        if not value:
            return [self.min_date,self.max_date]
		
        # create a list of date items (one for start and one for until)
        fromuntil = value.split(' - ')
        if len(fromuntil) != 2:
            return [self.min_date,self.max_date]
        try:
            date_from = datetime.strptime(fromuntil[0], '%d/%m/%Y').date()
            date_until = datetime.strptime(fromuntil[1], '%d/%m/%Y').date()
        except ValueError:
            return [self.min_date,self.max_date]
        return [date_from, date_until]

    def validate(self, value):
        if len(value) != 2:
            forms.ValidationError('Date range is in wrong format')
            
            
            
class FilterDateRangeForm(forms.Form):
    """
    Class represents a date range field using the javascript daterangepicker library 
    It is specific to the RSEAdmin tool as it enables min and max allocated dates to be queries
    Property functions are used to be able to obtain date ranges without cluttering views
    """

    min_date = Project.min_start_date()
    max_date = Project.max_end_date()
    
    # Use custom date range field
    filter_range = DateRangeField(label='Date Range', widget=forms.TextInput(attrs={'class' : 'form-control pull-right'}) , min_date=min_date, max_date=max_date)


    @property
    def from_date(self):
        return self.cleaned_data["filter_range"][0]
        
    @property
    def until_date(self):
        return self.cleaned_data["filter_range"][1]
        
    @property 
    def years(self):
        return FinancialYear.objects.all()
        
        
        
        
class ProjectTypeForm(forms.Form):
    """
    Class represents a filter form for filtering by date range and service type used by many views which display multiple project views.
    Extends the filter range form by adding type and status fields
    """

    type = forms.ChoiceField(choices = (('S', 'Service'),('A', 'Allocated')), widget=forms.Select(attrs={'class' : 'form-control pull-right'}))
    
        
class FilterProjectForm(FilterDateRangeForm):
    """
    Class represents a filter form for filtering by date range and service type used by many views which display multiple project views.
    Extends the filter range form by adding type and status fields
    """

    status = forms.ChoiceField(choices = (('A', 'All'), ('L', 'Funded and Review'), ('U', 'Funded, Review and in Preperation')) + Project.STATUS_CHOICES, widget=forms.Select(attrs={'class' : 'form-control pull-right'}))
    # Type cant be filtered at database level as it is a property
    #type = forms.ChoiceField(choices = (('A', 'All'), ('F', 'Allocated'), ('S', 'Service')), widget=forms.Select(attrs={'class' : 'form-control pull-right'}))
      
    
class ProjectAllocationForm(forms.ModelForm):
    """
    Form for adding and editing allocations within a project. Uses model form base type.
    Sets the start and end day of the allocation as follows
    - Start day is start of project
    - End day is start day plus remaining commitment to the project (by calculating sum of already committed hours) - This may be set by budget for allocated projects using responsive AJAX query.
    """
    
    # Fields are created manually to set the date input format
    start =  forms.DateField(widget=forms.DateInput(format = ('%d/%m/%Y'), attrs={'class' : 'form-control'}), input_formats=('%d/%m/%Y',))
    end = forms.DateField(widget=forms.DateInput(format = ('%d/%m/%Y'), attrs={'class' : 'form-control'}), input_formats=('%d/%m/%Y',))
    
    def __init__ (self, *args, **kwargs):
        """ Set the initial data """
        if not 'project' in kwargs:
            raise TypeError("ProjectAllocationForm missing required argument: 'project'")
        self.project = self.user = kwargs.pop('project', None)
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
        fields = ['rse', 'percentage','start', 'end']
        widgets = {
            'rse': forms.Select(attrs={'class' : 'form-control'}),
            'percentage': forms.NumberInput(attrs={'class' : 'form-control'}),
            'project': forms.HiddenInput(),
        }
        
   
    
    def clean(self):
        cleaned_data=super(ProjectAllocationForm, self).clean()
        errors = {}
        
        # Validation checks that the dates are correct (no need to raise errors if fields are empty as they are required so superclass will have done this)
        if cleaned_data['start'] and cleaned_data['end']:
            if cleaned_data['start'] > cleaned_data['end'] :
                errors['end'] = ('Allocation end date can not be before start date')

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
     
class AllocatedProjectForm(forms.ModelForm):    
    """
    Class for creation and editing of a project
    """
    
    # Fields are created manually to set the date input format
    start =  forms.DateField(widget=forms.DateInput(format = ('%d/%m/%Y'), attrs={'class' : 'form-control'}), input_formats=('%d/%m/%Y',))
    end = forms.DateField(widget=forms.DateInput(format = ('%d/%m/%Y'), attrs={'class' : 'form-control'}), input_formats=('%d/%m/%Y',))
    
    class Meta:
        model = AllocatedProject
        fields = ['proj_costing_id', 'name', 'description', 'client', 'internal', 'start', 'end', 'status', 'percentage', 'overheads', 'salary_band', 'created', 'creator']
        widgets = {
            'proj_costing_id': forms.TextInput(attrs={'class' : 'form-control'}),
            'name': forms.TextInput(attrs={'class' : 'form-control'}),
            'description': forms.Textarea(attrs={'class' : 'form-control'}),
            'client': forms.Select(attrs={'class' : 'form-control'}),
            'internal': forms.CheckboxInput(),
            'status': forms.Select(choices = Project.STATUS_CHOICES, attrs={'class' : 'form-control pull-right'}),
            'percentage': forms.NumberInput(attrs={'class' : 'form-control'}),
            'overheads':  forms.NumberInput(attrs={'class' : 'form-control'}),
            'salary_band': forms.Select(attrs={'class' : 'form-control'}),
            'creator': forms.HiddenInput(),
            'created': forms.HiddenInput(),
        }
        
    def clean(self):
        cleaned_data=super(AllocatedProjectForm, self).clean()
        errors = {}
        
        # Validation checks that the dates are correct (no need to raise errors if fields are empty as they are required so superclass will have done this)
        if 'start' in cleaned_data and 'end' in cleaned_data:
            if cleaned_data['start'] > cleaned_data['end'] :
                errors['end'] = ('Project end date can not be before start date')
        
        if errors:
            raise ValidationError(errors)


    def clean_start(self):
        """
        Cant change the start date if there are dependant allocations which start before the proposed date
        """
        cleaned_start=self.cleaned_data['start']

        # Cant change start and end date if there are existing allocations outside of the period
        if self.instance:
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
    start =  forms.DateField(widget=forms.DateInput(format = ('%d/%m/%Y'), attrs={'class' : 'form-control'}), input_formats=('%d/%m/%Y',))
    end = forms.DateField(widget=forms.DateInput(format = ('%d/%m/%Y'), attrs={'class' : 'form-control'}), input_formats=('%d/%m/%Y',))
    invoice_received = forms.DateField(widget=forms.DateInput(format = ('%d/%m/%Y'), attrs={'class' : 'form-control'}), input_formats=('%d/%m/%Y',), required=False)
    
    class Meta:
        model = ServiceProject
        fields = ['proj_costing_id', 'name', 'description', 'client', 'internal', 'start', 'end', 'status', 'days', 'rate', 'charged', 'invoice_received', 'created', 'creator']
        widgets = {
            'proj_costing_id': forms.TextInput(attrs={'class' : 'form-control'}),
            'name': forms.TextInput(attrs={'class' : 'form-control'}),
            'description': forms.Textarea(attrs={'class' : 'form-control'}),
            'client': forms.Select(attrs={'class' : 'form-control'}),
            'internal': forms.CheckboxInput(),
            'status': forms.Select(choices = Project.STATUS_CHOICES, attrs={'class' : 'form-control pull-right'}),
            'days': forms.NumberInput(attrs={'class' : 'form-control'}),
            'rate': forms.NumberInput(attrs={'class' : 'form-control'}),
            'charged': forms.CheckboxInput(),
            'creator': forms.HiddenInput(),
            'created': forms.HiddenInput(),
        }
        
    def clean(self):
        cleaned_data=super(ServiceProjectForm, self).clean()
        errors = {}
        
        # Validation checks that the dates are correct (no need to raise errors if fields are empty as they are required so superclass will have done this)
        if 'start' in cleaned_data and 'end' in cleaned_data:
            if cleaned_data['start'] > cleaned_data['end'] :
                errors['end'] = ('Project end date can not be before start date')
        
        if errors:
            raise ValidationError(errors)

    def clean_start(self):
        """
        Cant change the start date if there are dependant allocations which start before the proposed date
        """
        cleaned_start=self.cleaned_data['start']

        # Cant change start and end date if there are existing allocations outside of the period
        if self.instance:
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
            # check for allocations on project which end after the proposed start date
            should_be_empty = RSEAllocation.objects.filter(project=self.instance, end__gt=cleaned_end)
            if should_be_empty:
                raise ValidationError('There are current allocations on this project which end after the proposed end date')

        return cleaned_end
        
                
            
class ClientForm(forms.ModelForm):    
    """
    Class for creation and editing of a client
    """
    class Meta:
        model = Client
        fields = ['name', 'department', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class' : 'form-control'}),
            'department': forms.TextInput(attrs={'class' : 'form-control'}),
            'description': forms.Textarea(attrs={'class' : 'form-control'}),    
        }
        

class UserTypeForm(forms.Form):
    """
    Class represents a filter form for filtering by date range and service type used by many views which display multiple project views.
    Extends the filter range form by adding type and status fields
    """

    user_type = forms.ChoiceField(choices = (('A', 'Administrator'),('R', 'RSE')), widget=forms.Select(attrs={'class' : 'form-control pull-right'}))
    

  
class NewUserForm(UserCreationForm):    
    """ Class for creating a new user """
    
    # Field to allow user to be an admin user
    is_admin = forms.BooleanField(initial=False, required=False)

    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class' : 'form-control'}),
            'last_name': forms.TextInput(attrs={'class' : 'form-control'}),
            'email': forms.EmailInput(attrs={'class' : 'form-control'}),
        }
 
    def __init__(self, *args, **kwargs):
        """ Override init to customise the UserCreationForm widget class appearance """
        super(NewUserForm, self).__init__(*args, **kwargs)
        
        # set html attributes of fields in parent form
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None
    
 
    def save(self, commit=True):
        """ Override save to make user a superuser """
        user = super(NewUserForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        # make an admin if checked
        if self.cleaned_data["is_admin"]:
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
            'username': forms.TextInput(attrs={'class' : 'form-control'}),
            'first_name': forms.TextInput(attrs={'class' : 'form-control'}),
            'last_name': forms.TextInput(attrs={'class' : 'form-control'}),
            'email': forms.EmailInput(attrs={'class' : 'form-control'}),
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
    
    employed_from =  forms.DateField(widget=forms.DateInput(format = ('%d/%m/%Y'), attrs={'class' : 'form-control'}), input_formats=('%d/%m/%Y',))
    employed_until =  forms.DateField(widget=forms.DateInput(format = ('%d/%m/%Y'), attrs={'class' : 'form-control'}), input_formats=('%d/%m/%Y',))


    class Meta:
        model = RSE
        fields = ['employed_from', 'employed_until']


class NewRSEUserForm(forms.ModelForm):    
    """
    Form for new RSE users. This is used alongside the new user form so does not extend it.
    Same as EditRSEUserForm but with an initial salary band option which is filtered dynamically within javascript
    """
    
    employed_from =  forms.DateField(widget=forms.DateInput(format = ('%d/%m/%Y'), attrs={'class' : 'form-control'}), input_formats=('%d/%m/%Y',))
    employed_until =  forms.DateField(widget=forms.DateInput(format = ('%d/%m/%Y'), attrs={'class' : 'form-control'}), input_formats=('%d/%m/%Y',))
    year = forms.ModelChoiceField(queryset = FinancialYear.objects.all(), empty_label=None, required=False, widget=forms.Select(attrs={'class' : 'form-control pull-right'}))           # triggers dynamic filter in JS
    salary_band = forms.ModelChoiceField(queryset = SalaryBand.objects.all(), empty_label=None, required=True, widget=forms.Select(attrs={'class' : 'form-control pull-right'})) # dynamically filtered (JS)
 
    class Meta:
        model = RSE
        fields = ['employed_from', 'employed_until']

    def save(self, commit=True):
        """ Override save to make user a superuser """
        rse = super(NewRSEUserForm, self).save(commit=False)
        # commit
        if commit:
            rse.save()
            # create an initial salary grade change
            if self.cleaned_data["salary_band"]:
                sgc = SalaryGradeChange(rse=rse, salary_band=self.cleaned_data["salary_band"])
                sgc.save()
        return rse
        
class NewSalaryBandForm(forms.ModelForm):
    """
    Class represents a form for creating a new salary band with a given year
    """
    
    def __init__(self, *args, **kwargs):
        # if no instance then we expect a year to set as initial value
        if not 'instance' in kwargs:
            if not 'year' in kwargs:
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
            'grade': forms.NumberInput(attrs={'class' : 'form-control'}),
            'grade_point': forms.NumberInput(attrs={'class' : 'form-control'}),
            'year': forms.HiddenInput(),
            'salary': forms.NumberInput(attrs={'class' : 'form-control'}),
            'increments': forms.CheckboxInput(),
        }


class NewFinancialYearForm(forms.ModelForm):
    """
    Class represents a form for creating a new salary band with a given year
    """
    copy_from = forms.ModelChoiceField(queryset = FinancialYear.objects.all(), empty_label="", required=False, widget=forms.Select(attrs={'class' : 'form-control pull-right'}))

    class Meta:
        model = FinancialYear
        fields = ['year']
        widgets = {
            'year': forms.NumberInput(attrs={'class' : 'form-control'}),
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
                    sb.pk = None # remove pk to save as new item in database
                    sb.year = financial_year
                    sb.save()

        return financial_year

class SalaryGradeChangeForm(forms.ModelForm):
    """
    Class represents a form for a salary grade change for an RSE
    """

    year = forms.ModelChoiceField(queryset = FinancialYear.objects.all(), empty_label=None, required=True, widget=forms.Select(attrs={'class' : 'form-control pull-right'}))
    
    def __init__ (self, *args, **kwargs):
        """ Set the initial data """
        if not 'rse' in kwargs:
            raise TypeError("SalaryGradeChangeForm missing required argument: 'rse'")
        rse = kwargs.pop('rse', None)

        # call super 
        super(SalaryGradeChangeForm, self).__init__(*args, **kwargs)

        # set RSE (as it is a hidden field)
        self.fields['rse'].initial = rse

        # not required as query set will be dynamically loaded via ajax
        #self.fields['salary_band'].queryset = SalaryBand.objects.all()

    
    class Meta:
        model = SalaryGradeChange
        fields = ['rse', 'salary_band']
        widgets = {
            'rse': forms.HiddenInput(),
            'salary_band': forms.Select(attrs={'class' : 'form-control pull-right'}) # choices set dynamically
            
        }

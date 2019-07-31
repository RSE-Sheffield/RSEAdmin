from django import forms
from datetime import datetime, timedelta

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
        if not 'min_date' in kwargs:
            raise TypeError("DateRangeField missing required argument: 'min_date'")
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

    min_date = RSEAllocation.min_allocation_start()
    max_date = RSEAllocation.max_allocation_end()
    
    
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
        
        
        
        
class FilterProjectForm(FilterDateRangeForm):
    """
    Class represents a filter form for filtering by date range and service type used by many views which display multiple project views.
    Extends the filter range form by adding type and status fields
    """

    status = forms.ChoiceField(choices = (('A', 'All'),) + Project.STATUS_CHOICES, widget=forms.Select(attrs={'class' : 'form-control pull-right'}))
    # Type cant be filtered at database level as it is a property
    #type = forms.ChoiceField(choices = (('A', 'All'), ('F', 'Allocated'), ('S', 'Service')), widget=forms.Select(attrs={'class' : 'form-control pull-right'}))
    
    
class ProjectAllocationForm(forms.ModelForm):
    """
    Form for adding and editing allocations within a project. Uses model form base type.
    """
    
    def __init__ (self, *args, **kwargs):
        """ Set the initial data """
        if not 'project' in kwargs:
            raise TypeError("ProjectAllocationForm missing required argument: 'project'")
        project = self.user = kwargs.pop('project', None)
        super(ProjectAllocationForm, self).__init__(*args, **kwargs)
        self.fields['percentage'].initial = project.fte
        self.fields['start'].initial = datetime.strftime(project.start, "%d/%m/%Y")
        self.fields['end'].initial = datetime.strftime(project.start + timedelta(days=project.remaining_days_at_fte), "%d/%m/%Y")

    
    class Meta:
        model = RSEAllocation
        fields = ['rse', 'percentage','start', 'end']
        widgets = {
            'rse': forms.Select(attrs={'class' : 'form-control'}),
            'percentage': forms.NumberInput(attrs={'class' : 'form-control'}),
            'start': forms.DateInput(attrs={'class' : 'form-control'}),
            'end': forms.DateInput(attrs={'class' : 'form-control'}),
            'project': forms.HiddenInput(),
        }
        
   
    
    def clean(self):
        cleaned_data=super(ProjectAllocationForm, self).clean()
        errors = {}
         # TODO Validation does not work
        if cleaned_data['start'] < cleaned_data['end'] :
            errors['end'] = ('Allocation end date can not be before start date')
        if not errors:
            raise ValidationError(errors)
    
    
    
    
    
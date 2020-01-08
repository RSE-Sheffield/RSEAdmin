from django import forms
from datetime import datetime, timedelta
from django.core.validators import RegexValidator

from .models import *



class TimesheetForm(forms.ModelForm):
    """
    Form for capturing TimeSheetEntry data and performing some basic validation.
    The form has no widgets as form data is submit from javascript
    """
 
    date = forms.DateField(input_formats=(r'%Y-%m-%d',))

    class Meta:
        model = TimeSheetEntry
        fields = '__all__'
        
    def clean(self):
        cleaned_data=super(TimesheetForm, self).clean()
        errors = {}

        # Check that the end time is not before the start time
        if 'end_time' in cleaned_data and 'start_time' in cleaned_data and cleaned_data['end_time'] is not None:
            if cleaned_data['end_time'] <= cleaned_data['start_time']:
                errors['end_time'] = ("The end time can not be before the start time")

        # time sheet entry can not be outside project period (but may be outside allocation)
        if 'project' in cleaned_data and cleaned_data['project'] is not None and \
            'rse' in cleaned_data and cleaned_data['rse'] is not None and \
            'date' in cleaned_data and cleaned_data['date'] is not None :
            p = cleaned_data['project']
            rse = cleaned_data['rse']
            date = cleaned_data['date']
            
            # check dates
            if p.start > date:
                    errors['date'] = f"The time sheet entry date is before the start of the project ({p.start})"
            if p.end < date:
                    errors['date'] = f"The time sheet entry date is after the end of the project ({p.end})"

        if errors:
            raise ValidationError(errors)

class ProjectTimeViewOptionsForm(forms.Form):

    rse = forms.ChoiceField(widget=forms.Select(attrs={'class' : 'form-control'}))
    granularity = forms.ChoiceField(choices = (('day', 'Day'), ('week', 'Week'), ('month', 'Month')), widget=forms.Select(attrs={'class' : 'form-control'}))
    
    def __init__(self, *args,**kwargs):
        if not 'project' in kwargs:
            raise TypeError("ProjectTimeViewOptionsForm missing required argument: 'project'")
        self.project = kwargs.pop('project')
        self.rses = RSE.objects.all()
        super(ProjectTimeViewOptionsForm, self).__init__(*args,**kwargs)

        # populate RSE options
        self.fields['rse'].choices =  [('', 'All')]+[(rse.id, rse) for rse in self.rses]

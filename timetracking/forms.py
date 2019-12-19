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

        if errors:
            raise ValidationError(errors)
  
from django import forms
from django.core.validators import validate_email
from datetime import datetime, timedelta
from .models import *


class DateRangeField(forms.Field):
	def to_python(self, value):
		# if not value return empty list
		if not value:
			return []
		
		# create a list of datetime items (one for start and one for until)
		fromuntil = value.split(' - ')
		if len(fromuntil) != 2:
			return []
		try:
			date_from = datetime.strptime(fromuntil[0], '%d/%m/%Y')
			date_until = datetime.strptime(fromuntil[1], '%d/%m/%Y')
		except ValueError:
			return []
		return [date_from, date_until]

	def validate(self, value):
		if len(value) != 2:
			forms.ValidationError('Date range is in wrong format')
            
class DateRangeFilterForm(forms.Form):
    filter_year =  DateRangeField(label='Date Range', 
										widget=forms.TextInput(attrs={'class' : 'form-control pull-right'}) )
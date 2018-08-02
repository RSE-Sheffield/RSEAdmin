from django.db import models
from django.contrib.auth.models import User


class PercentageField(models.FloatField):
    #widget = models.TextInput(attrs={"class": "percentInput"})

    def to_python(self, value):
        val = super(PercentageField, self).to_python(value)
        if is_number(val):
            return val/100
        return val

    def prepare_value(self, value):
        val = super(PercentageField, self).prepare_value(value)
        if is_number(val) and not isinstance(val, str):
            return str((float(val)*100))
        return val

class SalaryBand(models.Model):
    grade = models.IntegerField(default=1)
    grade_point = models.IntegerField(default=1)
    
class Client(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    

class RSE(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    salary_band = models.ForeignKey(SalaryBand, on_delete=models.DO_NOTHING)
    current_employment = models.BooleanField(default=True)
    
class Project(models.Model):
    creator = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    created = models.DateTimeField()
    
    funder_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    client = models.ForeignKey(Client, on_delete=models.DO_NOTHING)
    academic_contact = models.CharField(max_length=100)
    
    start = models.DateTimeField()
    end = models.DateTimeField()
    percentage = PercentageField()
    
    overheads = models.BooleanField(default=True)
    STATUS_CHOICES = (
        ('P', 'Preperation'),
        ('R', 'Review'),
        ('F', 'Funded'),
        ('X', 'Rejected'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    
class RSEAllocation(models.Model):
    rse = models.ForeignKey(RSE, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    percentage = PercentageField()
    start = models.DateTimeField()
    end = models.DateTimeField()
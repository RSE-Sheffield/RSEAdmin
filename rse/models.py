from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import timedelta

class PercentageField(models.FloatField):
    #widget = models.TextInput(attrs={"class": "percentInput"})

    def to_python(self, value):
        val = super(PercentageField, self).to_python(value)
        if val.isnumeric():
            return val/100
        return val

    def prepare_value(self, value):
        val = super(PercentageField, self).prepare_value(value)
        if val.isnumeric() and not isinstance(val, str):
            return str((float(val)*100))
        return val
        
class SalaryBand(models.Model):
    grade = models.IntegerField(default=1)
    grade_point = models.IntegerField(default=1)
    
    def __str__(self):
        return str(self.grade) + '.' + str(self.grade_point)
    
class Client(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    

class RSE(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    salary_band = models.ForeignKey(SalaryBand, on_delete=models.DO_NOTHING)
    current_employment = models.BooleanField(default=True)
    
    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name
    
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
    percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    overheads = models.BooleanField(default=True)
    STATUS_CHOICES = (
        ('P', 'Preperation'),
        ('R', 'Review'),
        ('F', 'Funded'),
        ('X', 'Rejected'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    
    def __str__(self):
        return self.name
        
    @property
    def duration(self):
        return (self.end - self.start).days
        
    
class RSEAllocation(models.Model):
    rse = models.ForeignKey(RSE, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    start = models.DateTimeField()
    end = models.DateTimeField()
    
    def __str__(self):
        return str(self.rse.user) + ' on ' + str(self.project) + ' at ' + str(self.percentage) + '%'
        
    @property
    def duration(self):
        return (self.end - self.start).days
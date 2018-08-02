from django.contrib import admin

from .models import SalaryBand
from .models import Client
from .models import RSE
from .models import Project
from .models import RSEAllocation

admin.site.register(SalaryBand)
admin.site.register(Client)
admin.site.register(RSE)
admin.site.register(Project)
admin.site.register(RSEAllocation)

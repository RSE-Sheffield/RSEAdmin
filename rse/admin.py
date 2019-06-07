from django.contrib import admin

from .models import (
    Client,
    FinancialYear,
    Project,
    RSE,
    RSEAllocation,
    SalaryBand,
    SalaryGradeChange,
)


admin.site.register(SalaryBand)
admin.site.register(Client)
admin.site.register(RSE)
admin.site.register(Project)
admin.site.register(RSEAllocation)
admin.site.register(FinancialYear)
admin.site.register(SalaryGradeChange)

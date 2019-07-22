from django.contrib import admin

from .models import (
    Client,
    FinancialYear,
    AllocatedProject,
    ServiceProject,
    RSE,
    RSEAllocation,
    SalaryBand,
    SalaryGradeChange,
)


admin.site.register(SalaryBand)
admin.site.register(Client)
admin.site.register(RSE)
admin.site.register(AllocatedProject)
admin.site.register(ServiceProject)
admin.site.register(RSEAllocation)
admin.site.register(FinancialYear)
admin.site.register(SalaryGradeChange)

Reports
=======

The RSE Admin tool provides a number of useful reports fro team administration. These are only available to Admin users (or RSE users with administrative privileges).


Recent Allocations
------------------

Allocations are not deleted from the database (unless a project is deleted). Instead they have deleted date which removes them from views and reports. The Recent Allocations report shows any created or deleted allocations from a given date. This can be useful in identifying where cost distributions have changed, especially if they need to be recreated in some external financial system periodically.

The default date in the filter is based off todays date less the HOME_PAGE_DAYS_RECENT value in the settings file.

Cost Distributions
------------------

The cost distribution report provides a breakdown of staff time (as a percentage of their FTE) per project on the current date. Only projects which have a status of funded are included. Internal projects are excluded as are service projects which are not chargeable (in which case the project will generate a surplus service income, see `Service Income`_).

Selecting *More* on an individual staff member will provide a complete breakdown of of that RSEs cost distribution for all projects for which they have a project allocation. The filter can be used to change the date range to limit this to certain financial years or custom date ranges. Similarly the funding status of projects can be changed to see cost breakdowns for projects which may be under review etc.


RSE Costs
---------

The RSE costs view provides a breakdown of each RSEs salary costs. It includes the following information which is used to determine the RSEs staffing cost liability. Liability represents salary cost not cost recovered through allocations on projects.

- **Recovered Salary :** Any recovered salary from allocations on projects (either *Allocated* projects or chargeable *Service* projects)
- **Internal Project Salary :** Any salary cost as a result of allocations on internal projects
- **Non-Recovered Staff Costs :** The salary less the recovered salary. This represents the actual salary cost to the RSE staff members underwriter (as liability considers time on internal projects).

*Note: That any overheads generated are reported separately and may result in a net cash surplus even if the staff member has a salary liability.* Any overheads generated through allocations of RSS staff on *Allocated* projects can be `viewed per project <Project Costs & Overheads>`_ or in the `Financial Summary`_.

The detail of how each RSEs salary is calculated can be viewed by selecting the :raw-html:`<i class="fa fa-calculator"></i>` icon.  This will present the `RSE Staff Costs Breakdown`_ report.

RSE Staff Costs Breakdown
~~~~~~~~~~~~~~~~~~~~~~~~~

This view provide an RSE breakdown per project of any recovered or internal project salary costs. Salary costs are separated into time periods from 1st January to 31st July and 1st August to 31st December as each 1st January date may result in a salary increment and each 1st August date will result in a new financial years salary data. For salary costs which project past know finical years salary values salary increments will be based off the last available finical year and salary inflation will be estimated at 3%. Where salary inflation is estimated this is indicated with *(estimated)* next to the salary band which was used. Inflation estimates are compounded year after year.

Service Invoicing
-----------------

The service invoicing report presents a list of *Service* projects with with a filter for *Invoice Received* which has a value of `Outstanding` if there is no specified invoice received date. The :raw-html:`<i class="fa fa-edit"></i>` icon can be selected to edit the project and specify an invoice received date.

Outstanding invoices for `Active` and `Funded` projects will result in staff time being charged (assuming the project is chargeable) without any income received. Care must be taken with invoicing to ensure that invoices are not received in separate financial years to where RSE allocation have been made.

Service Income
--------------

The service income report shows a summary of *Service* project staff costs (due to RSE allocations) compared with income received through invoicing. *Service* projects do not generate overheads in the same way as *Allocated* projects, instead they may accrue a surplus balance as a result of a rate being charged which is greater than the RSE staff costs. The surplus represents any balance (positive) of deficit (negative). The report shows all service projects which are not internal. The filter range can be used to limit the range of projects which are included. If any part of the project (specified by start and end date) is within the filter range it will be included. Only the portions of the salary calculation for the filter period will however be included.

The detail of how each projects staff cost is calculated can be viewed by selecting the :raw-html:`<i class="fa fa-calculator"></i>` icon.  This will present the `Project Staff Costs Breakdown`_ report.


Project Costs & Overheads
-------------------------

The projects costs and overheads report shows any RSE staff costs per project. The view also calculates overheads generated as a result of any *Allocated* projects based on the staff time allocated to the project. Service projects do not generate overheads but are included in this report if they are `charged`.

The detail of how each Projects staff costs is calculated can be viewed by selecting the :raw-html:`<i class="fa fa-calculator"></i>` icon.  This will present the `Project Staff Costs Breakdown`_ report.

Project Staff Costs Breakdown
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This view provides a project breakdown per RSE of any recovered or internal project salary costs. Salary costs are separated into time periods from 1st January to 31st July and 1st August to 31st December as each 1st January date may result in a salary increment and each 1st August date will result in a new financial years salary data. For salary costs which project past know finical years salary values salary increments will be based off the last available finical year and salary inflation will be estimated at 3%. Where salary inflation is estimated this is indicated with *(estimated)* next to the salary band which was used. Inflation estimates are compounded year after year.


Internal Project Costs
----------------------

The internal project costs report shows the staff actual costs associated with each internal project. This is the sum of any staff costs incurred through allocations on internal projects. 

The detail of how each Projects staff costs is calculated can be viewed by selecting the :raw-html:`<i class="fa fa-calculator"></i>` icon.  This will present the `Project Staff Costs Breakdown`_ report.


Financial Summary
-----------------

The financial summary report provides an overview of all finances for a given time period (usually by financial year). A balance for the RSE group is determined from the cost of staff less; any recovered staff costs (see `RSE Costs`_), any service income (see `Service Income`_) and any internal project costs (see `Internal Project Costs`_).

Each part of the calculation can be broken down into a detailed view by selecting the :raw-html:`<i class="fa fa-calculator"></i>` icon.


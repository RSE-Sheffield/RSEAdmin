Projects and Allocations
========================

The RSE Admin tool makes a distinction between projects which are classed as service work (*Service* projects) and projects where staff time is costed onto a research grant (*Allocated* projects). Allocated projects represent staff time costed onto a grant at a percentage of an FTE which will generate an overhead (at a set annual rate) for the institution. Service projects projects represent a commitment in terms of number of RSE days at a set service rate. 

Service projects use the HEI `Transparent Approach to Costing <https://www.trac.ac.uk/about/>`_ (TRAC) recommendation of 220 working days per year (this value can however be changed in the settings file under *WORKING_DAYS_PER_YEAR*). As such a service project of 220 days represents a full year of RSE commitment and overhead rates should factor this into any calculation to cover staff time. Allocations for RSE staff on service projects are will apply the TRAC calculation to represent the actual (FTE equivalent) time period spent on a project (rather than just the number of service days). This way each allocation has a fair share of holidays and other non working days. Allocations of RSE time onto Allocated projects are always based on a percentage of FTE time and as such always represent the actual time period spent on a project.

The site makes a distinction between effort and budget reporting on projects. Both forms of project generate an income but the level of staff commitment expected for each is different. I.e. A service project is expected to meet an effort commitment in terms of a number of staff days. Surplus income (day rate less the actual staff costs) will be accumulated as a result. Allocated projects are can be reported by either effort or budget. It is frequently desirable to over-commit staff to ensure that a staffing budget is completely spent. This is required when a project is costed with a higher grade point than the RSE assigned to it. The `Project Summary`_ view provides a summary of project commitment by either budget or effort.



Creating Projects
-----------------

Projects and clients can be created by either Admin or RSE users however only Admin users can create allocations of RSE effort onto projects.

Creating Clients
~~~~~~~~~~~~~~~~

New projects require a client which is a named person from a department or institution. A new client can be created by selecting **Admin->New Client** from the main menu or by selecting the :raw-html:`<i class="fa fa-plus"></i>` icon from the client drop down in the new project view.

Adding a New Project
~~~~~~~~~~~~~~~~~~~~

A new project can be created by selecting **Admin->New Project** from the main menu. You will then need to choose between a *Service* or *Allocated* project type. 

An internal project represents a project which does not generate income but represents a specific commitment of time. E.g. A contribution in kind (from a core budget) of RSE time to support a research grant, development or delivery of teaching or another FATPOU activity. The *internal* option allows either allocated or service projects to be marked as internal.

The forms for completing the project details differ depending on the project type.

Allocated projects have a start date, and end date and a percentage of FTE RSE commitment which represents an expected unit of time in which the project will receive RSE support. The overheads rate is the pro-rata full time equivalent rate which is used to calculate any overheads returned to the institution for the staff time on this project. The salary band used for costing represents the salary used to calculate the cost of staff time on the project. 

Service projects have a start and end date which represents the tie in which a service project may be delivered. The start and end date do not dictate a specific time commitment but rather the range in which the *Number of Service Days* may be completed. The project date range must be at least the FTE equivalent of the number of TRAC service days. The *Charged to RSE account* indicates that staff time should be billed to an RSE account (i.e. the account which accumulated RSE service income at the specified *Service Rate*). Projects which are not billed to the RSE account will generate income but not result in staff time being allocated to any cost code via a staff cost distributions (see :ref:`Cost Distributions <Cost Distributions>` report). A Service project has an invoice received date which indicates the date in which money enters the RSE account. Not that this may be before or after staff time is changed back to the RSE account. Care should be taken to not span financial years with Service projects to avoid receiving income which is absorbed by the university at the financial year end when there are staff expenditures still to cover the following year.


Viewing Projects
----------------

A list of projects can be viewed by selecting **Team->Projects** from the main menu. Alternatively projects can be viewed in the client summary view by viewing the list of clients **Team->Clients** and selecting the *Info* button. The project list view can be filtered by type, status and schedule in either view. A clients details can be edited from the client summary view by selecting the :raw-html:`<i class="fa fa-edit"></i>` icon in the *Client Details* box.


Project Summary
---------------

Selecting a project via the *Info* button on any of the project list views will give a project summary which consists of the following.

- **FTE Commitment Overview :** This graph shows the allocation of staff effort on the project. Individual staff members can be toggled from the graph by clicking on their name in the figure legend.  The red dashed line represents todays date.
- **Project Details Tabbed Summary :** This tabbed information box provides information about the project. The :raw-html:`<i class="fa fa-edit"></i>` icon can be used to edit the projects details.
- **Effort and Distribution Summary :** This tabbed information box provides a summary of the effort and budget summary (Admin users only) of the project based off the allocations within it. The :raw-html:`<i class="fa fa-eye"></i>` icon allows a detailed view (and option to edit) project allocations. The :raw-html:`<i class="fa fa-calculator"></i>` icon under the field *Total Staff Costs* provides a break down of how the staff costs have been generated (see :ref:`RSE Staff Costs Breakdown <RSE Staff Costs Breakdown>`).
- **RSE Allocations Gantt :** The gantt chart view presents an alternative view of the commitment overview, displaying allocation durations. The gantt percentages represent the percentage of FTE an allocation represents on a grant.

Project Allocation Details
--------------------------

The project allocation details view can be accessed via the :raw-html:`<i class="fa fa-edit"></i>` icon in the *Effort and Distribution Summary* box of the *Project Details* view. The view presents a breakdown of each RSE staff allocation and can be viewed by Effort or budget. Project allocations can be edited or created using the :raw-html:`<i class="fa fa-edit"></i>` icon.

Creating Project Allocations
----------------------------

The *Add an allocation* box will be pre-populated with the following information;

- **Start Date :** Will be based of the start date of the project
- **End Date :** Will be based of the start date plus any remaining effort at FTE equivalent.
- **FTE Percentage :** Will be based off the FTE percentage used for Allocated Projects or 100.0% for service projects.

The :raw-html:`<i class="fa fa-area-chart"></i>` icon next the the RSE selection can be used to view the specific :ref:`RSE Commitment Overview <RSE Commitment Overview>` of an RSE between the proposed allocation date range. By clicking this icon with no RSE selected a `Team Commitment Overview`_ will be presented between the proposed allocation date range. This is helpful in determining who is available to staff the allocation.

If the start date or FTE percentage is modified then the :raw-html:`<i class="fa fa-clock-o"></i>` icon can be used to calculate a new end date based off the remaining effort at FTE equivalent. For Allocated projects the :raw-html:`<i class="fa fa-calculator"></i>` icon can be used to calculate an end date from the project based off the selected RSE.

Return to the `Project Allocation Details`_ view by selecting the  :raw-html:`<i class="fa fa-eye"></i>` icon or to the `Project Summary`_ by selecting the :raw-html:`<i class="fa fa-area-chart"></i>` icon in the project details box.


Team Commitment Overview
------------------------

A Team and projects overview is available by selecting **Team->Team & Projects Overview** from the main menu. This view provides both a commitment summary view of RSEs allocations on projects ora gantt based view where allocations are grouped by project. Both views can by updated by changing the filters which allow the date range shown and funding states to be displayed. Within the *Commitment (RSE FTE)* tab individual staff members can be toggled from the graph by clicking on their name in the figure legend. The red dashed line represents todays date and the :raw-html:`<i class="fa fa-expand"></i>` icon can be used to rescale the graph from 100% FTE to max (staff may be over committed on projects which are under review).

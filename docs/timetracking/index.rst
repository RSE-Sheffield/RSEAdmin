Time Tracking
=============

The time tracking application is a separate django application which can be enabled in your installation of RSEAdmin by ensuring that :code:`timetracking.apps.TimetrackingConfig` is listed in your :code:`INSTALLED_APPS` within the :code:`base.py` settings. 

The time tracking application has two important global settings which can be configured in the :code:`base.py` settings file.

- :code:`WORKING_HOURS_PER_DAY` This represents the number of expected hours per day an RSE staff member is expected to work. It is used to convert fractions of days into working hours.
- :code:`WORKING_DAYS_PER_YEAR` This represents the number of working days per year. This is a setting required in the main RSE application but is used within the time tracking application to convert calendar days to working days.

The time tacking application works by reporting on **working days** rather than calendar days. For example an allocated project (at 100%FTE) over a calendar year has :code:`WORKING_DAYS_PER_YEAR` which discounts weekends, bank holidays and holidays allowance (see  :ref:`Projects and Allocations <Projects and Allocations>` documentation on TRAC). Service projects do not require the same conversion as they have an associated number of service days which correspond to working days.

The purpose fo the time tracking app is to help RSEs to manage thier time on projects. This is particularly useful for RSEs working on service projects where the delivery of a number of service days can be spread over a large time period. The :ref:`Project Time Reporting <Project Time Reporting>` provides an indication of progress against any particular project. Additionally the time tracking application permits agile working practice as RSEs can contribute to projects which they are not formally charged to (through an RSE project allocation). This allows internal accounting of time which is hidden separated from the financial charging model. Often this is helpful as recorded time sheet activity in the region of hours (or small numbers of days) may not be worth changing an RSEs cost distribution but should still be recorded against project progress.


Time Sheets
-----------

Time sheets can be edited by selecting **Time Tracking->Time Sheets** from the main menu. For Admin users there is a selectable RSE drop down box however for RSE users the calendar for the RSE is shown. The calendar has standard monthly, weekly and day views and will show any time sheet entries previously created. 

The *Projects* tab will show coloured project boxes for any funded project which is active (according to the start and end dates of the project) within the calendar view. By default this will only include projects which the RSE has a project allocation however the drop down box can be used to include all projects (which are active). If there are no projects displayed then try changing the calendar date range by moving to the next month (week or day).

To create a time sheet entry drag the project boxes onto the calendar. In the month view this will create an all day event. Within the week or day view it is possible to create hourly event, these can be configured at 30 minute intervals (by dragging to move and extend duration), all day events can be created by dropping the project onto the top *all-day* band. Days which have all day events can not also include hourly events. Any time sheet entry must be within the start and end date of a project. As a project start part way through a month or week it is possible that a project box will be displayed which can not be added to a certain day on the calendar. An error dialogue will be shown in such cases confirming the projects start and end dates.

To remove a time sheet entry event select it to display the information dialogue and then choose the *Delete* button.


Project Time Reporting
----------------------

Detailed project time reporting is available by selecting the *info* button of a project on on the **Time Tracking->Time Reporting** view. The projects list presented in this view incudes a summary of progress up to todays date. The recorded hours represent (whole rounded) days committed by time sheet entries on the project up to today and scheduled is the number of working days expected up to the current working day (calculated by considering any project allocations). 

The detailed project time report includes shows a graph with the following plots.

- **Recorded days (Green) :** This shows the recorded days committed on a project which are accumulated via time sheet entries. This line should roughly follow the proposed scheduled effort and it is expected that the final effort should represent that of the total project effort.
- **Scheduled Days (Blue) :** Scheduled effort represents working days accumulated through project allocations. This may be not linear if projects have different allocations over their duration.
- **Total Project Effort (Black) :** This shows the linear expected commitment for the duration of the project. The rate at which this increases will vary on Service projects which have a set number of days which can be delivered over any time period.
- **Current Date Today (Red dashed) :** Indicates the date today.

Each of the graph plots can be disabled or enables by clicking on ehm in the figure legend.

The views options box allows the data within the report to be changed from a team view (i.e. *--- Team ---*) to a report for an individual RSE. If an individual RSE is selected then the recorded and scheduled effort will reflect just the individual however the *Total Project Effort* plot will remain the same. The granularity view allows the level or detail in the graphing to be changed to a monthly, weekly or daily plot (warning: a daily report may be slow for projects which have a long duration. By default the view will show the most appropriate granularity depending on the project duration.

The *Todays Recorded Effort Summary* box presents break down of commitment up to today for the team (or a selected RSE). The expected days days comes from the scheduled effort. An indication of over of under committed time can assist an RSE or the team in planning future project effort.

The *Project Total Recorded Effort Summary* box presents a breakdown of commitment for the team (or selected RSE) compared to the total project effort.
Users and Roles
===============

The RSE Admin tool has two distinct user types of *Admin* and *RSE* which have different sets of privileges and information available to them. Try logging into the demo site as both an Admin and RSE user to view the site from the different users perspectives.


Admin Users
-----------

Admin users have the sites full features available including financial and salary data as well as financial reporting. Admin users can not be allocated to projects and are as such not part of the RSE team.  

RSE Users
---------

RSE users represent RSE team members and each member of an RSE team should have an account which is used for linking them with project allocations. RSE users have an individual login which allows them to view their own projects and allocations as well as view team activity. A number of the sites features are restricted from RSE users (e.g. financial reports, administrative tools, and salary information). It is possible to have joint RSE and admin users. These must be created as RSE users where there is an option to add administrative privileges


User Creation
-------------

Creating an Admin User
~~~~~~~~~~~~~~~~~~~~~~

When you initially configured the site for deployment you will have created an Admin user by issuing the Django `python manage.py createsuperuser` command (alternatively use the demo sites provided login credentials from the README). Additional Admin users can be created by selecting **Admin->Add New User** from the menu and choosing the *Administrator* option from the user type. Once an Admin user is created they will have the option to change their password after logging in from the user menu in the top right corner of the site.

Creating an RSE User
~~~~~~~~~~~~~~~~~~~~

A fresh installation of the site will contain no RSE users. Before creating one you will need to :ref:`create a number of financial years<Financial Years and Salary Data>` and salary information for them. This is required to set the starting salary of an RSE user. 

RSE users can be created by selecting **Admin->Add New User** from the menu and choosing the *RSE* option from the user type. The RSE can be ranted the same permissions as an *Admin* by selecting the *User has administration permission* check box. Once an RSE user is created they will have the option to change their password after logging in from the user menu in the top right corner of the site.

Viewing and Editing Users
-------------------------

Admin users can view all users of the site by selecting **Admin->All Users** from the sites menu. Editing the user allows the basic information to be changed. An Admin user can reset any users password via the red **Change Password** button on the user edit form.

Changes to an RSE users salary must be made from the RSE Team page.







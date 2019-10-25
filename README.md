[![Build Status](https://travis-ci.org/RSE-Sheffield/RSEAdmin.svg?branch=master)](https://travis-ci.org/RSE-Sheffield/RSEAdmin)
[![Coverage Status](https://codecov.io/gh/RSE-Sheffield/RSEAdmin/branch/master/graph/badge.svg)](https://codecov.io/gh/RSE-Sheffield/RSEAdmin)

# RSE Administration Tool

This is a tool for tracking grant applications, managing RSE commitment and reporting on staff expenses and cost recovery.
The site has two users types (Admin and RSE) which have different levels of permissions. RSE users can view, edit and create projects as well as see allocations to projects based on effort (i.e. days). Admin users are able to create allocations on projects (allocated by effort or budget) and view reports on group finance and staffing.
There is a distinction between Allocated Projects (i.e. Directly incurred projects) where staff generate overheads for the university and Service Projects which are effort based and generate overheads for the group or facility.

The tool is a web app written using the [Django][django] web framework (Python) and the [AdminLTE][adminlte2] theme.

## Installing and running using Poetry

Simpler than using [conda][conda]  or manually creating a [virtualenv][virtualenv].

 1. Ensure you have Python >= 3.6 installed
 1. Install [Poetry][poetry], a tool for Python project management 
 1. Clone this repo
 1. `poetry install` to install project dependencies in an isolated hidden virtualenv 
    Dependencies are determined using info from `pyproject.toml`

## Building the database

For a new clone of the site you must build the database migrations and apply them by running the following command:

```sh
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

Existing database can be updated by using just the migrate command.

## Collect any static files

Static files must be collected before running the development server by running the following command:

```sh
poetry run python manage.py collectstatic
```

## Populating your development database with test data

The test data can be used to generate data for experimenting with the system during development.

```sh
poetry run python manage.py shell
from rse.tests.test_random_data import *
random_project_and_allocation_data()
```

This will populate your development/production database with test data. To reset the database delete the db.sqlite3 file and remove any files from `rse/migrations` (except `__init__.py`). You will then need to rebuild the database using makemigrations and migrate.

## Creating an Admin user

To log into the admin interface (which allows the creation of other Admin and RSE users) you need a Django superuser account. You can create one as follows:

```sh
poetry run python manage.py createsuperuser
```

## Starting a development Django server and Navigating the Site

```sh
poetry run python manage.py runserver 8080
```
    
The website will then be viewable at [http://127.0.0.1:8080](http://127.0.0.1:8080).

All pages of the site require logging in. You can use your super user account or if you have generated some random data you can use the RSE users user0-user10 with the password '12345'.

The site has a self explanatory navigation menu which varies depending on the permissions of the user.


## Testing

The site uses continuous integration. You can run all tests locally for all Django Apps associated with this Django Project:

```sh
poetry run python manage.py test
```

Note: The testing is mainly around model login rather than views or templates.

[adminlte2]: https://django-adminlte2.readthedocs.io/en/latest/ 
[conda]: https://docs.conda.io/en/latest/
[django]: https://www.djangoproject.com/
[virtualenv]: https://virtualenv.pypa.io/en/latest/
[poetry]: https://poetry.eustace.io/

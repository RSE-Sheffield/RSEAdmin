[![Build Status](https://travis-ci.org/RSE-Sheffield/RSEAdmin.svg?branch=master)](https://travis-ci.org/RSE-Sheffield/RSEAdmin)
[![Coverage Status](https://codecov.io/github/RSE-Sheffield/RSEAdmin.svg?branch=master)](https://codecov.io/gh/RSE-Sheffield/RSEAdmin)

# RSE Administration Tool

This is a (work in progress) tool for tracking grant applications, RSE commitment and reporting on group overheads and costings.

The tool is a web app written using the [Django][django] web framework (Python) 
and the [AdminLTE][adminlte2] theme.

## Installing and running using Poetry

Simpler than using [conda][conda]  or manually creating a [virtualenv][virtualenv].

 1. Install [Poetry][poetry], a tool for Python project management 
 1. Clone this repo
 1. `poetry install` to install project dependencies in an isolated hidden virtualenv 
    Dependencies are determined using info from `pyproject.toml`

## Starting a development Django server

```sh
poetry run python manage.py runserver 8080
```

## Navigating the site
    
The website will then be viewable at [http://127.0.0.1:8080](http://127.0.0.1:8080).

Key URLs include:

  * `/admin` - the admin interface
  * `/project/<project_id>` - project-specific overview
  * `/rse/all` - project allocations for all RSEs
  * `/rse/<rse_username>` - project allocations for specific RSE

NB to log into the admin interface you need a Django superuser account.  
If you don't already have one:

```sh
poetry run python manage.py createsuperuser
```

## Testing

Run all tests for all Django Apps associated with this Django Project:

```sh
poetry run python manage.py test
```

## Populating your development database with test data

The test data can be used to generate data for experimenting with the system during development.

```sh
poetry run python manage.py shell
from rse.tests.test_models import *
setup_project_and_allocation_data()
```

This will populate your development/production database with test data. To reset the database delete the db.sqlite3 file and remove any files from `rse/migrations` (except `__init__.py`).

[adminlte2]: https://django-adminlte2.readthedocs.io/en/latest/ 
[conda]: https://docs.conda.io/en/latest/
[django]: https://www.djangoproject.com/
[virtualenv]: https://virtualenv.pypa.io/en/latest/
[poetry]: https://poetry.eustace.io/

# RSE Administration Tool

This is a (work in progress) tool for tracking grant applications, RSE commitment and reporting on group overheads and costings.

The tool is a web app written using the [Django][django] web framework (Python) 
and the [AdminLTE][adminlte2] theme.

## Running from a virtualenv

The easiest way to instantiate the environment required to run the app is to 
create and activate a new [virtualenv][virtualenv]:

```sh
mkdir ~/.venvs
python3 -m virtualenv ~/.venvs/RSEAdmin
source ~/.venvs/RSEAdmin/bin/activate
pip install -r requirements.txt
```

## Running from a conda environment on Windows

Alternatively you can create a conda environment for running the Django app in:

```sh
conda create --name RSEAdmin --file environment.yml
conda activate RSEAdmin
```

Note that the above only works on Windows as [environment.yml](environment.yml) contains OS-specific dependencies.
    
## Starting a development Django server

After activating your virtualenv or conda environment you can start a Django development server:

```sh
python manage.py runserver 8080
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
python manage.py createsuperuser
```


[adminlte2]: https://django-adminlte2.readthedocs.io/en/latest/ 
[conda]: https://docs.conda.io/en/latest/
[django]: https://www.djangoproject.com/
[virtualenv]: https://virtualenv.pypa.io/en/latest/

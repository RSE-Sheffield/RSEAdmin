# RSE Administration Tool

This is a (work in progress) tool for tracking grant applications, RSE commitment and reporting on group overheads and costings.

The tool is a web app written in Django (Python) using the AdminLTE theme.

## Installation

The best way to configure Django is to build a conda environment using the provided `environment.yml.` 
i.e. create a conda environment as follows:

    conda env create --name DjangoRSE -f environment.yml
    
## Running the site

Activate your conda environment and use Django to launch a development server.

    conda activate DjangoRSE
    python manage.py runserver 8080
    
The website will be viewable at [http://127.0.0.1:8080](http://127.0.0.1:8080) and 
the admin interface will be available at [http://127.0.0.1:8080/admin](http://127.0.0.1:8080/admin).

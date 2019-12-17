#!/bin/sh

set -e

# Collect Django static files under the Django STATIC_ROOT
poetry run python manage.py collectstatic --noinput 

# Process Django migrations
# poetry run python manage.py migrate  # DO NOT RUN AUTOMATICALLY - see https://stackoverflow.com/questions/33992867/how-do-you-perform-django-database-migrations-when-using-docker-compose

poetry run gunicorn --bind="${GUNICORN_HOST}:${GUNICORN_PORT}" "${DJANGO_PROJ_NAME}.wsgi"

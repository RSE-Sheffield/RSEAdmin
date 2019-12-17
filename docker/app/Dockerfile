FROM alpine:latest

LABEL maintainer="w.furnass@sheffield.ac.uk"
LABEL vendor="University of Sheffield"

SHELL ["/bin/ash", "-eu", "-c"]

ENV \
    LANG=C.UTF-8 \ 
    # python:
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    # pip:
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # poetry:
    POETRY_VERSION=1.0.5 \
    # django:
    DJANGO_PROJ_NAME=RSEAdmin \
    #DJANGO_SECRET_KEY \
    # DJANGO_ALLOWED_HOSTS=host1,host2,host3,...
    # DJANGO_DEFAULT_FROM_EMAIL=mail1,mail2,...
    # DJANGO_SERVER_EMAIL=mail1,mail2,...
    # DJANGO_DEBUG is undefined so false
    DJANGO_PROJ_ROOT=/app \
    DJANGO_DB_NAME="${DJANGO_DB_NAME:-rseadmin}" \
    DJANGO_DB_USER="${DJANGO_DB_USER:-rseadmin}" \
    #DJANGO_DB_PASSWORD=...
    DJANGO_DB_HOST="${DJANGO_DB_HOST:-localhost}"  \
    DJANGO_DB_PORT="${DJANGO_DB_PORT:-5432}"  \
    # gunicorn: 
    GUNICORN_PORT=8002 \
    GUNICORN_HOST=127.0.0.1 \
    GUNICORN_OS_USER="${GUNICORN_OS_USER:-rseadmin}"
ENV \
    # More django (required as cannot recursively define env vars above)
    DJANGO_STATIC_ROOT="${DJANGO_PROJ_ROOT}/static" \
    DJANGO_SETTINGS_MODULE="${DJANGO_PROJ_NAME}.settings.settings_deployed" \
    GUNICORN_OS_GROUP="${GUNICORN_OS_USER}" \
    GUNICORN_OS_USER_HOME="/var/lib/${GUNICORN_OS_USER}"

# Copy repo into image
COPY . "${DJANGO_PROJ_ROOT}"
COPY /docker/app/django-entrypoint.sh /usr/bin/django-entrypoint.sh
# TODO: tidy up the following (move django_settings_deployed.py into settings dir and remove symlink)
RUN ln -s "${DJANGO_PROJ_ROOT}/docker/app/django_settings_deployed.py" "${DJANGO_PROJ_ROOT}/${DJANGO_PROJ_NAME}/settings/settings_deployed.py"

# Install OS Python3 package and 
# packages required to build psycopg2 Python pkg
RUN apk add \
    python3 \
    ca-certificates \
    postgresql-dev \
    python3-dev \
    gcc \
    musl-dev

# Download poetry
RUN wget 'https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py' -qP /usr/local/bin/

# Create system user for running gunicorn
RUN addgroup \
        --system \
        "${GUNICORN_OS_GROUP}" && \
    adduser \
        --home "${GUNICORN_OS_USER_HOME}" \
        --disabled-password \
        --ingroup "${GUNICORN_OS_GROUP}" \
        --system \
        "${GUNICORN_OS_USER}"

USER "${GUNICORN_OS_USER}"
WORKDIR "${DJANGO_PROJ_ROOT}"

# Install Poetry and patch so works with Python 3 (yuk)
RUN python3 /usr/local/bin/get-poetry.py --version "${POETRY_VERSION}" --yes && \
    sed -i '1s/python$/python3/' ~/.poetry/bin/poetry
ENV PATH="${GUNICORN_OS_USER_HOME}/.poetry/bin:${PATH}"

# Install project's Python dependencies
RUN poetry install --no-dev --no-interaction --no-ansi -E gunicorn -E pgsql

EXPOSE "${GUNICORN_PORT}"
CMD /usr/bin/django-entrypoint.sh

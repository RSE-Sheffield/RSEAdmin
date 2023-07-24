#!/bin/bash

# Configure postgres database
# This should probably be run as the postgres user

# Options
user=django
database_name=django
password=django_postgres

# Create the role
psql -c "create role $user with login password '$password';"

# Create the database
createdb --owner=django $database_name

# Give the user permission to create databases.
# This is required for Django testing:
# https://docs.djangoproject.com/en/4.0/topics/testing/overview/#the-test-database
  echo "Granting $user user permission to create databases..."
  psql -c "ALTER ROLE $user CREATEDB"
  echo "You might also need to apply migrations."



#!/bin/bash

# Configure postgres database
# This should probably be run as the postgres user

# Options
user=django
database_name=django
password=django_postgres

# Create the user
psql -c "CREATE USER $user WITH login PASSWORD '$password';"

# Create the database
createdb --owner=$user $database_name

# Give the user permission to create databases.
# This is required for Django testing:
# https://docs.djangoproject.com/en/4.0/topics/testing/overview/#the-test-database
echo "Granting $user user permission to create databases..."
psql -c "ALTER ROLE $user CREATEDB"
echo "You might also need to apply migrations."



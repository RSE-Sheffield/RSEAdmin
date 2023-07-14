# Start with a Python image
FROM python:3.9

# Set working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install Poetry
RUN pip install poetry

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi
  
# Fixing a weird issue with missing imports that only occurs in docker
RUN pip install setuptools

# Make port 8000 available to the world outside this container
EXPOSE 8080


# Define the command to run the app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]

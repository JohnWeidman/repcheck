# Use Python as the base image
FROM python:3.10-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (for building and compiling packages like psycopg2)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && curl -sL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean

# Install npm (already included in the Node.js setup)
RUN apt-get install npm -y

# Copy package.json and package-lock.json from theme/static_src to /app/
COPY theme/static_src/package.json theme/static_src/package-lock.json /app/

# Install npm dependencies
RUN npm install 

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project into the container
COPY . /app/


# Run Tailwind Build
RUN python manage.py tailwind build

# Run collectstatic (for production setup)
RUN python manage.py collectstatic --noinput

# Expose the port the app will run on
EXPOSE 8000

# Use environment variable to determine the run command (development or production)
CMD exec gunicorn --workers=3 --bind 0.0.0.0:8000 RepCheck.wsgi:application

# End of Dockerfile

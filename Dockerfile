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
    && apt-get clean

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project into the container
COPY . /app/


# Collect static files (for production use)
RUN python manage.py collectstatic --noinput

# Expose the port the app will run on
EXPOSE 8000

# Use environment variable to determine the run command (development or production)
ARG DJANGO_ENV=development
# Use environment variable to determine the run command (development or production)
ARG DJANGO_ENV=development
CMD if [ "$DJANGO_ENV" = "production" ]; then \
        echo "Running collectstatic for production..."; \
        python manage.py collectstatic --noinput; \
        exec gunicorn --workers=3 --bind 0.0.0.0:8000 RepCheck.wsgi:application; \
    else \
        exec python manage.py runserver 0.0.0.0:8000; \
    fi


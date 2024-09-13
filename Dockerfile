# Use the official Python 3.12 image as the base image (Debian-based)
FROM python:3.12.6

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory in the container
WORKDIR /app

# Install build dependencies and Poetry
RUN apt-get update && apt-get install -y gcc python3-dev libffi-dev libssl-dev \
    && pip install --no-cache-dir poetry

# Copy the pyproject.toml and poetry.lock files into the container
COPY pyproject.toml poetry.lock ./ 

# Install dependencies with Poetry
RUN poetry config virtualenvs.create false && poetry install --no-root

# Copy the FastAPI application code into the container
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 9090

# Command to run the application using uvicorn
CMD ["poetry", "run", "uvicorn", "backend.main:create_app", "--host", "0.0.0.0", "--port", "9090"]

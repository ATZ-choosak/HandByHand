# Use the official Python 3.12 slim image as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install build dependencies and Poetry
RUN apt-get update && apt-get install -y gcc python3-dev libffi-dev libssl-dev cargo \
    && pip install --no-cache-dir poetry

# Copy the pyproject.toml and poetry.lock files into the container
COPY pyproject.toml poetry.lock ./

# Install dependencies with Poetry, without dev dependencies in production
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-dev

# Copy the FastAPI application code into the container
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 9090

# Command to run the application using uvicorn
CMD ["poetry", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "9090"]

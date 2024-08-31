# Use the official Python 3.12 image as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy the pyproject.toml and poetry.lock files into the container
COPY pyproject.toml poetry.lock ./

# Install dependencies with Poetry
RUN poetry install --no-root --no-dev

# Copy the FastAPI application code into the container
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 8080

# Command to run the application using uvicorn
CMD ["poetry", "run", "uvicorn", "backend.main:create_app", "--host", "0.0.0.0", "--port", "8080"]

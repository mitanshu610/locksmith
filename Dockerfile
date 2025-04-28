# Use the official Python 3.10 image from the Docker Hub
FROM python:3.10-slim as base

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY ./requirements/requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI application code into the container
COPY . .

# Change ownership of the application files
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the port that the FastAPI app runs on
EXPOSE 8000

# Command to run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
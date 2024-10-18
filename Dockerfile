# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY ./app /app

# Set Python path
ENV PYTHONPATH=/

# Expose the port the app runs on
EXPOSE 8080

# Run your application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app.main:app -k uvicorn.workers.UvicornWorker

# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy your application code
COPY ./app /app

# Expose the port the app runs on
EXPOSE 8080

# Run your application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

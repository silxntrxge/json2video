# Use an official Python runtime as a parent image
FROM python:3.9-bookworm

# Set the working directory in the container
WORKDIR /app

# Install system dependencies including ImageMagick for Debian Bookworm
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    imagemagick \
    ffmpeg \
    libsm6 \
    libxext6 \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create font cache
RUN fc-cache -f -v

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Set environment variable to specify ImageMagick path
ENV MAGICK_HOME=/usr

# Run app.py when the container launches
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]

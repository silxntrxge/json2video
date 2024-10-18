# Use an official Python runtime as a parent image with Debian Bookworm
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

# Set sticky bit on /tmp to allow secure deletion of files
RUN chmod 1777 /tmp

# Copy custom ImageMagick policy file
COPY custom_policy.xml /etc/ImageMagick-6/policy.xml

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

# Verify ImageMagick installation and print its version
RUN convert -version

# Run the application when the container launches
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]

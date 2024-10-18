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

# Configure ImageMagick policy to allow various image operations and increase memory limits
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/rights="none" pattern="LABEL"/rights="read|write" pattern="LABEL"/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/<policy domain="coder" rights="none" pattern="PNG" \/>/<policy domain="coder" rights="read|write" pattern="PNG" \/>/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/<policy domain="coder" rights="none" pattern="GIF" \/>/<policy domain="coder" rights="read|write" pattern="GIF" \/>/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/name="memory" value="256MiB"/name="memory" value="1GiB"/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/name="disk" value="1GiB"/name="disk" value="4GiB"/' /etc/ImageMagick-6/policy.xml

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

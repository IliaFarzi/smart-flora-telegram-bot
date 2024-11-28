# Use official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy only the requirements file first for caching
COPY requirements.txt .

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Install necessary system dependencies
    wget \
    unzip \
    xvfb \
    chromium \
    chromium-driver \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire application directory
COPY . .

# Set the display environment variable (needed for headless mode in Selenium)
ENV DISPLAY=:99

# Expose port 8080 (optional)
EXPOSE 8080

# Default command to run the application
CMD ["python", "main.py"]

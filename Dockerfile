# Use official Python images from Docker Hub
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only requirements file first for efficient caching
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app
COPY images images


COPY plants.csv plants.csv

# Expose port (optional, only if needed for local testing)
EXPOSE 8080

# Run the bot
CMD ["python", "main.py"]

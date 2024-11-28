# Use official Python images from Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first for efficient caching of dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application directory structure
COPY . .

# Expose port 8080 (optional, only if needed for local testing)
EXPOSE 8080

# Run the bot
CMD ["python", "main.py"]

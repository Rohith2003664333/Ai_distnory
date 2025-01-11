# Use the official Python image as a base
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    libportaudio2 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download the spaCy language model
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application code
COPY . .

# Expose the port your app runs on (optional, depends on your setup)
EXPOSE 8000

# Specify the command to run the application
CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:${PORT:-8000} app:app"]


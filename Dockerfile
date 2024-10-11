# Use an official OpenJDK runtime as the base image
FROM openjdk:11-jdk-slim

# Set the working directory
WORKDIR /app

# Install required dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    poppler-utils \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt


# Copy the FastAPI application code
COPY app/ .

# Copy the built JAR file into the container
COPY pdffigures2.jar /app/pdffigures2.jar

RUN mkdir -p /app/logs /app/uploads /app/data

# Expose port 8000 for FastAPI
EXPOSE 8000

# Set the entry point to run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
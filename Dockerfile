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

# Install FastAPI and Uvicorn
RUN pip3 install fastapi uvicorn[standard] python-multipart

# Copy the built JAR file into the container
COPY pdffigures2.jar /app/pdffigures2.jar

# Copy the FastAPI application code
COPY app.py /app/app.py
COPY helpers.py /app/helpers.py

# Expose the port (change if necessary)
EXPOSE 8000

# Set the entry point to run the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
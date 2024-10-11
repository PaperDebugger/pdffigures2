FROM python:3.10-slim

# Install OpenJDK 17 and other required dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Disable Poetry's virtual environments (optional)
ENV POETRY_VIRTUALENVS_CREATE=false

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock ./

# Install Python dependencies
RUN poetry install --no-interaction --no-ansi

# Copy the FastAPI application code
COPY app/ .

# Copy the built JAR file into the container
COPY pdffigures2.jar /app/pdffigures2.jar

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads /app/data

# Expose port 8000 for FastAPI
EXPOSE 8000

# Set the entry point to run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
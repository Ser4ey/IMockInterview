# Pull official base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Set env variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=120
ENV PIP_RETRIES=10

# Install dependencies
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade --index-url https://pypi.org/simple -r requirements.txt

# Copy project
COPY . .

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

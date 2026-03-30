# -------------------------------------
# Base image
# -------------------------------------
FROM python:3.11-slim

# -------------------------------------
# Environment settings
# -------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -------------------------------------
# Working directory
# -------------------------------------
WORKDIR /app

# -------------------------------------
# Install system dependencies
# -------------------------------------
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------
# Copy requirements first (faster rebuilds)
# -------------------------------------
COPY requirements.txt .

# -------------------------------------
# Install Python dependencies
# -------------------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------
# Copy app source code
# -------------------------------------
COPY ./app ./app

# -------------------------------------
# Expose FastAPI port
# -------------------------------------
EXPOSE 8000

# -------------------------------------
# Start FastAPI server
# -------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
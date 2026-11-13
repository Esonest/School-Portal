
FROM python:3.13-slim

WORKDIR /app

# Install system packages required for OCR and PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project
COPY . .

# Collect static files and start Gunicorn
CMD ["sh", "-c", "python manage.py collectstatic --noinput && exec gunicorn school_management.wsgi:application --workers 3 --threads 2 --timeout 120 --preload --bind 0.0.0.0:${PORT:-10000}"]

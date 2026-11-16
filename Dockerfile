# Dockerfile – packages the Employee Management API into an image

# 1. Start from an official, small Python 3.12 image (same version as the laptop)
FROM python:3.12-slim

# 2. Python settings: no .pyc files, and show logs immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Work inside the /code folder in the container
WORKDIR /code

# 4. Install the packages first (Docker caches this step when only code changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the application code
COPY app ./app
COPY create_tables.py .

# 6. Run as a normal user instead of root (safer)
RUN useradd --create-home appuser
USER appuser

# 7. The API listens on port 8000
EXPOSE 8000

# 8. Start the API when the container starts
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

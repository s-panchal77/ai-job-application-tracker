# Base Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (better Docker cache usage)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create uploads folder if missing
RUN mkdir -p uploads/resumes

# Application port
EXPOSE 8000

# Start FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
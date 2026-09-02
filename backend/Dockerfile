FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY . .

# Expose port for FastAPI
EXPOSE 8000

# Run the production server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

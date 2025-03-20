# Use official Python image
FROM python:3.10-slim

# Environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the source code
COPY . .

# Expose default port
EXPOSE 8000

# Run your app with Python (so PORT can be dynamically resolved in Python)
CMD ["python", "backend/main.py"]


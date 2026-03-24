# Base Python image
FROM python:3.8-slim

# Install necessary Python dependencies
RUN pip install boto3 requests

# Copy both scripts (ingestion and transformation)
COPY src/raw_script.py /app/raw_script.py
COPY src/transform_script.py /app/transform_script.py

# Set the working directory
WORKDIR /app

# Default command to execute both scripts sequentially
CMD ["sh", "-c", "python raw_script.py && python transform_script.py"]

# Use the official Python base image
FROM python:3.10-slim
LABEL authors="Sint Lwin Htoo"

# Set the working directory
WORKDIR /app

# Copy application code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose the port Flask will run on
EXPOSE 8080

# Set environment variables
ENV PORT=8080

# Start the Flask app
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8080", "app:app"]

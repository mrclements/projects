FROM python:3.9-slim

WORKDIR /app

# Copy only the necessary files to minimize build time
COPY scripts/requirements.txt ./
COPY scripts/wake_hf_spaces.py ./scripts/
COPY .env ./.env

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt httpx python-dotenv loguru

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV RUN_CONTINUOUSLY=true

# The script now handles its own scheduling with improved error handling
CMD ["python", "-u", "scripts/wake_hf_spaces.py"]

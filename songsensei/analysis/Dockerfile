FROM python:3.11-slim

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    libasound2-dev \
    portaudio19-dev \
    build-essential \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Cython first (required for madmom)
RUN pip install --no-cache-dir Cython numpy

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create directories for temporary files
RUN mkdir -p /tmp/audio && chmod 777 /tmp/audio

# Create non-root user
RUN useradd -m -u 1001 analysis
RUN chown -R analysis:analysis /app /tmp/audio
USER analysis

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]

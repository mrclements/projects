# SongSensei MVP

A locally-hosted web application for analyzing YouTube music videos to extract chord progressions, guitar tabs, and musical theory information.

## Architecture & Ports

- **Frontend (Web)**  
  - Technology: React + TypeScript  
  - Port: 3000  
  - URL: http://localhost:3000

- **API (Backend)**  
  - Technology: Node.js + Express  
  - Port: 4000  
  - Endpoints:  
    - `GET /api/health` – Health check  
    - `POST /api/analysis/ingest` – Submit YouTube URL  
    - `GET /api/analysis/status/:jobId` – Job status & waveform data  
    - `POST /api/analysis/analyze` – Analyze trimmed segment  
    - `GET /api/analysis/audio/:jobId` – (Not yet implemented)

- **Analysis Service**  
  - Technology: Python (yt-dlp, Essentia, madmom, music21)  
  - Port: 5000  

## Prerequisites

- Docker & Docker Compose installed  
- GNU Make (optional on Windows; PowerShell scripts provided)  
- Node.js (for local development without containers)  
- Python 3.8+ (for analysis service)

## Getting Started

### 1. Testing Setup (First Step)

Windows PowerShell:
```powershell
.\test-setup.ps1
```

Linux/Mac/WSL:
```bash
./test-setup.sh
```

This verifies connectivity and tool availability.

### 2. Build & Run (Containers)

From the project root directory:

```bash
# Build images and start all services in detached mode
make up

# Stop and remove all containers
make down

# View live logs for all services
make logs

# Restart
make restart

# Clean (remove volumes)
make clean
```

_Alternative without Make (manual Docker Compose commands):_

```bash
docker-compose build
docker-compose up -d
docker-compose down
docker-compose logs -f
```

### 3. Accessing Services

- **Web UI**: http://localhost:3000  
- **API Health Check**: http://localhost:4000/api/health  
- **Analysis Service** (raw API): http://localhost:5000

## Using the Website

1. Open your browser to http://localhost:3000  
2. In the **Load YouTube Video** form, paste a valid YouTube URL and click **Load & Extract Audio**.  
3. You will see **Status: processing** as audio extraction begins (takes ~30–60s).  
4. Once waveform data loads, an interactive waveform appears under **Trim Audio Segment**.  
   - **Click and drag** on the waveform to select the region you want to analyze (10-30 seconds recommended).  
   - The selection area will be highlighted in blue as you drag.  
   - Use the Reset button to clear your selection and start over.  
5. Under **Analyze Musical Content**, click **Analyze Chords & Tabs**.  
6. You will see **Status: analyzing** (takes ~20–40s).  
7. When complete, the **Analysis Results** section displays:  
   - Key, tempo, time signature  
   - Chord progression with timestamps  
   - Guitar tab measures  
   - Confidence score

## Expected Output

- **Status States**:  
  - `idle` – No job loaded  
  - `processing` – Audio extraction in progress  
  - `ready` – Waveform ready for trimming  
  - `analyzing` – Music analysis in progress  
  - `analyzed` – Results available

- **Sample Analysis Panel**:  
  - Chords displayed in a timeline  
  - Tab notation with fret numbers  
  - Basic metadata (title, artist, duration)

## Troubleshooting

- **Port Conflicts**: Ensure no other service is using ports 3000, 4000, or 5000.  
- **Docker Issues**:  
  - Run `docker ps` to verify containers are up.  
  - Use `make logs` to inspect errors.  
- **Browser Errors**:  
  - Check console for CORS or manifest errors.  
  - Clear cache or disable extensions if CSS/JS fails to load.  
- **API Failures**:  
  - Hit `http://localhost:4000/api/health` to confirm backend.  
  - Use Postman or curl to test endpoints directly.

---

For detailed service-specific instructions, see:

- **Web Service**: `songsensei/web/README.md`  
- **API Service**: `songsensei/api/README.md`  
- **Analysis Service**: `songsensei/analysis/README.md`

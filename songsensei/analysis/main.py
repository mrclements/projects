from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
import os
import uuid
from loguru import logger

from services.audio_extractor import AudioExtractor
from services.music_analyzer import MusicAnalyzer
from services.waveform_generator import WaveformGenerator
from models.analysis_models import JobStatus, AnalysisResult, WaveformData

app = FastAPI(
    title="SongSensei Analysis Service",
    description="Music analysis service using yt-dlp, Essentia, madmom, and music21",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (will be replaced with Redis/database)
jobs: Dict[str, Dict[str, Any]] = {}

# Initialize services
audio_extractor = AudioExtractor()
music_analyzer = MusicAnalyzer()
waveform_generator = WaveformGenerator()

class IngestRequest(BaseModel):
    youtube_url: HttpUrl
    user_consent: bool = True

class AnalyzeRequest(BaseModel):
    job_id: str
    start_time: float
    end_time: float

@app.get("/")
async def root():
    return {"message": "SongSensei Analysis Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "yt_dlp": "available",
            "essentia": "available", 
            "madmom": "available",
            "librosa": "available"
        }
    }

@app.post("/ingest")
async def ingest_audio(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Start audio extraction from YouTube URL
    """
    try:
        job_id = str(uuid.uuid4())
        
        # Initialize job
        jobs[job_id] = {
            "status": "processing",
            "youtube_url": str(request.youtube_url),
            "created_at": None,
            "waveform_data": None,
            "error": None
        }
        
        logger.info(f"Starting audio extraction for job {job_id}")
        
        # Start background task for audio extraction
        background_tasks.add_task(
            extract_audio_task,
            job_id,
            str(request.youtube_url)
        )
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Audio extraction started"
        }
        
    except Exception as e:
        logger.error(f"Error starting audio extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get status of audio extraction job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "waveform_data": job.get("waveform_data"),
        "error": job.get("error")
    }

@app.post("/analyze")
async def analyze_segment(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Analyze a trimmed audio segment for chords and musical content
    """
    try:
        job_id = request.job_id
        
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = jobs[job_id]
        
        if job["status"] != "completed":
            raise HTTPException(status_code=400, detail="Audio extraction not completed")
        
        # Update job status
        jobs[job_id]["analysis_status"] = "analyzing"
        
        logger.info(f"Starting analysis for job {job_id}, segment {request.start_time}-{request.end_time}")
        
        # Start background analysis task
        background_tasks.add_task(
            analyze_audio_task,
            job_id,
            request.start_time,
            request.end_time
        )
        
        return {
            "job_id": job_id,
            "status": "analyzing",
            "message": "Musical analysis started"
        }
        
    except Exception as e:
        logger.error(f"Error starting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis/{job_id}")
async def get_analysis_result(job_id: str):
    """
    Get analysis results for a job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if "analysis_result" not in job:
        return {
            "job_id": job_id,
            "status": job.get("analysis_status", "not_started"),
            "message": "Analysis not completed yet"
        }
    
    return {
        "job_id": job_id,
        "status": "completed",
        "analysis": job["analysis_result"]
    }

async def extract_audio_task(job_id: str, youtube_url: str):
    """
    Background task to extract audio from YouTube
    """
    try:
        logger.info(f"Extracting audio for job {job_id}")
        
        # Extract audio
        audio_path = await audio_extractor.extract_audio(youtube_url, job_id)
        
        # Generate waveform data
        waveform_data = await waveform_generator.generate_waveform(audio_path)
        
        # Update job status
        jobs[job_id].update({
            "status": "completed",
            "audio_path": audio_path,
            "waveform_data": waveform_data
        })
        
        logger.info(f"Audio extraction completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error extracting audio for job {job_id}: {str(e)}")
        jobs[job_id].update({
            "status": "failed",
            "error": str(e)
        })

async def analyze_audio_task(job_id: str, start_time: float, end_time: float):
    """
    Background task to analyze audio segment
    """
    try:
        logger.info(f"Analyzing audio segment for job {job_id}")
        
        job = jobs[job_id]
        audio_path = job["audio_path"]
        
        # Perform musical analysis
        analysis_result = await music_analyzer.analyze_segment(
            audio_path, start_time, end_time
        )
        
        # Update job with analysis results
        jobs[job_id].update({
            "analysis_status": "completed",
            "analysis_result": analysis_result
        })
        
        logger.info(f"Analysis completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error analyzing audio for job {job_id}: {str(e)}")
        jobs[job_id].update({
            "analysis_status": "failed",
            "analysis_error": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

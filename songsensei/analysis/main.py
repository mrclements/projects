from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
import os
import uuid
import asyncio
from loguru import logger

from services.audio_extractor import AudioExtractor
from services.music_analyzer import MusicAnalyzer
from services.waveform_generator import WaveformGenerator
from services.cloud_orchestrator import CloudOrchestrator
from models.analysis_models import JobStatus, AnalysisResult, WaveformData

app = FastAPI(
    title="SongSensei Analysis Service",
    description="Music analysis service using yt-dlp, Essentia, madmom, and music21",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
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
cloud_orchestrator = CloudOrchestrator()

class IngestRequest(BaseModel):
    youtube_url: HttpUrl
    user_consent: bool = True

class AnalyzeRequest(BaseModel):
    job_id: str
    start_time: float
    end_time: float
    # V2 Extensions
    analysis_version: str = "2.0"
    enable_cloud_services: bool = False
    cloud_options: Dict[str, Any] = {}

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
        jobs[job_id]["analysis_config"] = {
            "version": request.analysis_version,
            "enable_cloud": request.enable_cloud_services,
            "cloud_options": request.cloud_options
        }
        
        logger.info(f"Starting analysis for job {job_id}, segment {request.start_time}-{request.end_time}, version {request.analysis_version}")
        
        # Start background analysis task with V2 parameters
        background_tasks.add_task(
            analyze_audio_task,
            job_id,
            request.start_time,
            request.end_time,
            request.analysis_version,
            request.enable_cloud_services,
            request.cloud_options
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

@app.get("/cloud-status")
async def cloud_service_status():
    """
    Get status of all connected cloud services
    """
    try:
        status = cloud_orchestrator.get_service_status()
        return {
            "status": "healthy",
            "services": status
        }
    except Exception as e:
        logger.error(f"Error checking cloud service status: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "services": {}
        }

@app.post("/wake-spaces")
async def wake_hf_spaces(req: fastapi.Request):
    """
    Ping Hugging Face spaces to wake them up and get them ready for use
    """
    try:
        import httpx
        from datetime import datetime
        
        # Get environment variables
        spleeter_url = os.environ.get("HUGGINGFACE_SPLEETER_URL")
        demucs_url = os.environ.get("HUGGINGFACE_DEMUCS_URL")
        
        # Get Hugging Face token from request headers with fallback to environment variable
        huggingface_token = None
        try:
            # Try to get token from headers first
            huggingface_token = req.headers.get("x-huggingface-token", "")
            
            # If not in headers, try to get from environment as fallback
            if not huggingface_token:
                huggingface_token = os.environ.get("HUGGINGFACE_API_TOKEN", "")
                logger.info(f"Using environment token for wake-up: {'*' * min(len(huggingface_token), 5) if huggingface_token else 'None'}")
            else:
                logger.info(f"Using header token for wake-up: {'*' * min(len(huggingface_token), 5) if huggingface_token else 'None'}")
        except Exception as e:
            logger.warning(f"Could not extract Hugging Face token: {str(e)}")
            huggingface_token = os.environ.get("HUGGINGFACE_API_TOKEN", "")
        
        # Check if cloud services are enabled
        cloud_enabled = os.environ.get("ENABLE_CLOUD_SERVICES", "false").lower() == "true"
        if not cloud_enabled:
            logger.info("Cloud services are disabled in configuration. Skipping wakeup.")
            return {
                "spleeter": False,
                "demucs": False,
                "enabled": False,
                "timestamp": datetime.now().isoformat()
            }
            
        # Prepare for requests
        headers = {}
        if huggingface_token:
            headers["Authorization"] = f"Bearer {huggingface_token}"
            
        # Function to ping a space
        async def ping_space(client, space_url, space_name):
            if not space_url:
                logger.warning(f"No URL provided for {space_name}")
                return False

            # Ensure URL ends with a trailing slash for API compatibility
            if not space_url.endswith("/"):
                space_url = f"{space_url}/"

            # Add the health endpoint
            if not space_url.endswith("api/health") and not space_url.endswith("api/health/"):
                if "api/" in space_url:
                    health_url = f"{space_url}health"
                else:
                    health_url = f"{space_url}api/health"
            else:
                health_url = space_url

            try:
                logger.info(f"Pinging {space_name} at {health_url}")
                response = await client.get(health_url, headers=headers, timeout=30.0)
                
                if response.status_code == 200:
                    logger.info(f"Successfully pinged {space_name}: {response.text}")
                    return True
                else:
                    logger.error(f"Failed to ping {space_name}: Status {response.status_code}, {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Error pinging {space_name}: {str(e)}")
                return False

        # Ping the spaces
        async with httpx.AsyncClient() as client:
            spleeter_status = await ping_space(client, spleeter_url, "Spleeter Space")
            demucs_status = await ping_space(client, demucs_url, "Demucs Space")
            
            return {
                "spleeter": spleeter_status,
                "demucs": demucs_status,
                "enabled": True,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error waking up Hugging Face spaces: {str(e)}")
        return {
            "error": str(e),
            "spleeter": False,
            "demucs": False,
            "enabled": True,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/debug/check-service/{service_name}")
async def debug_check_service(service_name: str):
    """
    Manually trigger a health check for a specific service - for debugging purposes
    """
    try:
        from services.cloud_orchestrator import CloudService
        
        # Validate service name
        try:
            service = CloudService(service_name.lower())
        except ValueError:
            valid_services = [s.value for s in CloudService]
            return {
                "status": "error",
                "message": f"Invalid service name. Valid options are: {valid_services}"
            }
            
        # Trigger a fresh health check
        logger.info(f"Manually triggering health check for {service_name}")
        
        # Check service configuration
        service_config = cloud_orchestrator.services.get(service, {})
        base_url = service_config.get("base_url", "")
        is_enabled = service_config.get("enabled", False)
        api_key = service_config.get("api_key", "")
        api_key_masked = f"{'*' * min(len(api_key), 5)}" if api_key else "None"
        
        # Diagnostic info
        diagnostics = {
            "service": service_name,
            "enabled": is_enabled,
            "base_url": base_url,
            "api_key_present": bool(api_key),
            "api_key_preview": api_key_masked,
            "env_token": os.environ.get("HUGGINGFACE_API_TOKEN", "")[:3] + "..." if os.environ.get("HUGGINGFACE_API_TOKEN") else "None"
        }
        
        # Perform health check
        health_result = await cloud_orchestrator.health_check(service)
        
        return {
            "status": "success",
            "health_check_result": health_result,
            "diagnostics": diagnostics,
            "service_config": service_config,
            "message": f"Health check for {service_name}: {'PASSED' if health_result else 'FAILED'}"
        }
    except Exception as e:
        logger.error(f"Error running debug health check: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

class SeparateTracksRequest(BaseModel):
    job_id: str
    audio_url: str
    model: str = "demucs"  # Default to Demucs v4, can be "demucs" or "spleeter"

@app.post("/separate-tracks")
async def separate_audio_tracks(request: SeparateTracksRequest, req: fastapi.Request):
    """
    Separate audio tracks using Demucs v4 or Spleeter (vocals, drums, bass, other)
    """
    try:
        job_id = request.job_id
        
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = jobs[job_id]
        audio_path = job.get("audio_path")
        
        if not audio_path or not os.path.exists(audio_path):
            raise HTTPException(status_code=400, detail="Audio file not found")
        
        # Get Hugging Face token from request headers with fallback to environment variable
        huggingface_token = None
        try:
            # Try to get token from headers first
            huggingface_token = req.headers.get("x-huggingface-token", "")
            
            # If not in headers, try to get from environment as fallback
            if not huggingface_token:
                huggingface_token = os.environ.get("HUGGINGFACE_API_TOKEN", "")
                logger.info(f"Using environment token: {'*' * min(len(huggingface_token), 5) if huggingface_token else 'None'}")
            else:
                logger.info(f"Using header token: {'*' * min(len(huggingface_token), 5) if huggingface_token else 'None'}")
        except Exception as e:
            logger.warning(f"Could not extract Hugging Face token: {str(e)}")
            # Still try to get from environment in case of exception
            huggingface_token = os.environ.get("HUGGINGFACE_API_TOKEN", "")
        
        # Always set the token (either from header or environment)
        os.environ["HUGGINGFACE_API_TOKEN"] = huggingface_token
        
        # Process with Demucs v4 (default) or Spleeter via Cloud Orchestrator
        separation_result = await cloud_orchestrator.separate_sources(audio_path)
        
        if not separation_result.get("success"):
            raise HTTPException(status_code=500, detail="Track separation failed")
            
        # Create a dynamic tracks dictionary from all stems
        tracks = {}
        for key, value in separation_result.items():
            # Include only path fields, filter out metadata fields
            if key.endswith("_path") and value:
                # Extract the stem name from key (e.g., "vocals_path" -> "vocals")
                stem_name = key.replace("_path", "")
                tracks[stem_name] = value
        
        # Return URLs to the separated tracks
        return {
            "success": True,
            "tracks": tracks,
            "cloud_service": separation_result.get("cloud_service"),
            "fallback": separation_result.get("fallback", False)
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error separating tracks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_audio_task(
    job_id: str, 
    start_time: float, 
    end_time: float, 
    analysis_version: str = "2.0",
    enable_cloud_services: bool = False,
    cloud_options: Dict[str, Any] = {}
):
    """
    Background task to analyze audio segment with V2 support
    """
    try:
        logger.info(f"Analyzing audio segment for job {job_id} with V{analysis_version}")
        
        job = jobs[job_id]
        audio_path = job["audio_path"]
        
        # Track processing start time
        processing_start = asyncio.get_event_loop().time()
        
        # If cloud services are enabled, use cloud processing first
        cloud_processing_result = None
        if enable_cloud_services:
            try:
                logger.info(f"Using cloud services for job {job_id}")
                cloud_processing_result = await cloud_orchestrator.process_with_orchestration(audio_path)
                logger.info(f"Cloud processing completed for job {job_id}")
            except Exception as e:
                logger.error(f"Cloud processing failed: {str(e)}. Falling back to local processing.")
        
        # Perform local musical analysis
        analysis_result = await music_analyzer.analyze_segment(
            audio_path, start_time, end_time
        )
        
        # Enhance with cloud results if available
        if cloud_processing_result:
            # Add cloud-generated segments if they exist
            if cloud_processing_result.get("song_structure", {}).get("segments"):
                analysis_result["segments"] = cloud_processing_result["song_structure"]["segments"]
            
            # Add key changes and modulations if they exist
            if cloud_processing_result.get("key_analysis", {}).get("key_changes"):
                analysis_result["key_changes"] = cloud_processing_result["key_analysis"]["key_changes"]
                
            if cloud_processing_result.get("key_analysis", {}).get("modulations"):
                analysis_result["modulations"] = cloud_processing_result["key_analysis"]["modulations"]
            
            # Add cloud processing metadata
            if cloud_processing_result.get("processing_metadata"):
                analysis_result["processing"] = cloud_processing_result["processing_metadata"]
        
        # Calculate total processing time
        processing_time = asyncio.get_event_loop().time() - processing_start
        if "processing" not in analysis_result:
            analysis_result["processing"] = {}
        analysis_result["processing"]["processingTime"] = processing_time
        
        # Set version
        analysis_result["analysisVersion"] = analysis_version
        
        # Update job with analysis results
        jobs[job_id].update({
            "analysis_status": "completed",
            "analysis_result": analysis_result
        })
        
        logger.info(f"Analysis completed for job {job_id} in {processing_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Error analyzing audio for job {job_id}: {str(e)}")
        jobs[job_id].update({
            "analysis_status": "failed",
            "analysis_error": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

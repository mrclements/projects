import asyncio
import time
from typing import Dict, Any, List, Optional
from loguru import logger
import httpx
import os
from enum import Enum

class CloudService(str, Enum):
    SPLEETER = "spleeter"
    COLAB = "colab"
    RENDER = "render"
    HUGGINGFACE = "huggingface"
    GITHUB_ACTIONS = "github_actions"

class CloudOrchestrator:
    """
    Orchestrates cloud-based music analysis services with fallbacks
    """
    
    def __init__(self):
        self.services = {}
        self.service_health = {}
        self.setup_services()
    
    def setup_services(self):
        """Initialize cloud service connections"""
        try:
            # Hugging Face Spaces for source separation
            self.services[CloudService.SPLEETER] = {
                "base_url": os.getenv("HUGGINGFACE_SPLEETER_URL", ""),
                "api_key": os.getenv("HUGGINGFACE_API_TOKEN", ""),
                "enabled": bool(os.getenv("HUGGINGFACE_API_TOKEN"))
            }
            
            # Google Colab for song structure analysis
            self.services[CloudService.COLAB] = {
                "base_url": os.getenv("GOOGLE_COLAB_URL", ""),
                "api_key": os.getenv("GOOGLE_COLAB_API_KEY", ""),
                "enabled": bool(os.getenv("GOOGLE_COLAB_API_KEY"))
            }
            
            # Render.com for key detection microservice
            self.services[CloudService.RENDER] = {
                "base_url": os.getenv("RENDER_KEY_SERVICE_URL", ""),
                "api_key": os.getenv("RENDER_API_KEY", ""),
                "enabled": bool(os.getenv("RENDER_API_KEY"))
            }
            
            # GitHub Actions for tab generation
            self.services[CloudService.GITHUB_ACTIONS] = {
                "base_url": os.getenv("GITHUB_ACTIONS_URL", ""),
                "api_key": os.getenv("GITHUB_TOKEN", ""),
                "enabled": bool(os.getenv("GITHUB_TOKEN"))
            }
            
            logger.info("Cloud orchestrator initialized")
            
        except Exception as e:
            logger.warning(f"Error initializing cloud services: {str(e)}")
    
    async def health_check(self, service: CloudService) -> bool:
        """Check if a cloud service is available"""
        try:
            if not self.services[service]["enabled"]:
                return False
                
            # Simple health check (can be enhanced per service)
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.services[service]['base_url']}/health",
                    headers={"Authorization": f"Bearer {self.services[service]['api_key']}"}
                )
                healthy = response.status_code == 200
                
            self.service_health[service] = {
                "healthy": healthy,
                "last_check": time.time()
            }
            
            return healthy
            
        except Exception as e:
            logger.warning(f"Health check failed for {service}: {str(e)}")
            self.service_health[service] = {
                "healthy": False,
                "last_check": time.time(),
                "error": str(e)
            }
            return False
    
    async def separate_sources(self, audio_path: str) -> Dict[str, Any]:
        """
        Separate audio sources using Spleeter via Hugging Face Spaces
        Falls back to local processing if service unavailable
        """
        try:
            if await self.health_check(CloudService.SPLEETER):
                logger.info("Using cloud source separation (Spleeter)")
                return await self._cloud_source_separation(audio_path)
            else:
                logger.info("Cloud service unavailable, using local fallback")
                return await self._local_source_separation_fallback(audio_path)
                
        except Exception as e:
            logger.error(f"Source separation failed: {str(e)}")
            return await self._local_source_separation_fallback(audio_path)
    
    async def _cloud_source_separation(self, audio_path: str) -> Dict[str, Any]:
        """Perform source separation using cloud service"""
        try:
            # Read audio file
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.services[CloudService.SPLEETER]['base_url']}/separate",
                    files={"audio": audio_data},
                    headers={"Authorization": f"Bearer {self.services[CloudService.SPLEETER]['api_key']}"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "vocals_path": result.get("vocals_url"),
                        "drums_path": result.get("drums_url"),
                        "bass_path": result.get("bass_url"),
                        "other_path": result.get("other_url"),  # Harmonic content
                        "success": True,
                        "cloud_service": CloudService.SPLEETER
                    }
                else:
                    raise Exception(f"Cloud service returned {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Cloud source separation failed: {str(e)}")
            raise
    
    async def _local_source_separation_fallback(self, audio_path: str) -> Dict[str, Any]:
        """Fallback to local processing when cloud services unavailable"""
        logger.info("Using local fallback for source separation")
        
        # For now, just return the original audio path for all tracks
        # In the future, this could use a lightweight local separation model
        return {
            "vocals_path": None,
            "drums_path": None, 
            "bass_path": None,
            "other_path": audio_path,  # Use full mix as harmonic content
            "success": True,
            "cloud_service": None,
            "fallback": True
        }
    
    async def analyze_song_structure(self, audio_path: str) -> Dict[str, Any]:
        """
        Analyze song structure using Google Colab
        Falls back to local processing if service unavailable
        """
        try:
            if await self.health_check(CloudService.COLAB):
                logger.info("Using cloud song structure analysis (Colab)")
                return await self._cloud_structure_analysis(audio_path)
            else:
                logger.info("Cloud service unavailable, using local fallback")
                return await self._local_structure_analysis_fallback(audio_path)
                
        except Exception as e:
            logger.error(f"Song structure analysis failed: {str(e)}")
            return await self._local_structure_analysis_fallback(audio_path)
    
    async def _cloud_structure_analysis(self, audio_path: str) -> Dict[str, Any]:
        """Perform song structure analysis using cloud service"""
        try:
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.services[CloudService.COLAB]['base_url']}/analyze_structure",
                    files={"audio": audio_data},
                    headers={"Authorization": f"Bearer {self.services[CloudService.COLAB]['api_key']}"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "segments": result.get("segments", []),
                        "success": True,
                        "cloud_service": CloudService.COLAB
                    }
                else:
                    raise Exception(f"Cloud service returned {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Cloud structure analysis failed: {str(e)}")
            raise
    
    async def _local_structure_analysis_fallback(self, audio_path: str) -> Dict[str, Any]:
        """Fallback to local processing for song structure"""
        logger.info("Using local fallback for song structure analysis")
        
        # Simple fallback: create basic segments based on audio duration
        # In the future, this could use a lightweight local algorithm
        try:
            import librosa
            y, sr = librosa.load(audio_path)
            duration = len(y) / sr
            
            # Create simple segments for now
            segments = []
            if duration > 60:  # Only segment longer songs
                segment_duration = duration / 4
                labels = ["Intro", "Verse", "Chorus", "Bridge"]
                
                for i, label in enumerate(labels):
                    start_time = i * segment_duration
                    end_time = (i + 1) * segment_duration
                    
                    segments.append({
                        "id": f"segment_{i}",
                        "label": label,
                        "start_time": start_time,
                        "end_time": min(end_time, duration),
                        "confidence": 0.6  # Lower confidence for fallback
                    })
            
            return {
                "segments": segments,
                "success": True,
                "cloud_service": None,
                "fallback": True
            }
            
        except Exception as e:
            logger.error(f"Local structure analysis fallback failed: {str(e)}")
            return {
                "segments": [],
                "success": False,
                "fallback": True
            }
    
    async def detect_advanced_key_changes(self, audio_path: str) -> Dict[str, Any]:
        """
        Detect key changes using Render.com microservice
        Falls back to local processing if service unavailable
        """
        try:
            if await self.health_check(CloudService.RENDER):
                logger.info("Using cloud key detection (Render)")
                return await self._cloud_key_detection(audio_path)
            else:
                logger.info("Cloud service unavailable, using local fallback")
                return await self._local_key_detection_fallback(audio_path)
                
        except Exception as e:
            logger.error(f"Key detection failed: {str(e)}")
            return await self._local_key_detection_fallback(audio_path)
    
    async def _cloud_key_detection(self, audio_path: str) -> Dict[str, Any]:
        """Perform key detection using cloud service"""
        try:
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.services[CloudService.RENDER]['base_url']}/detect_keys",
                    files={"audio": audio_data},
                    headers={"Authorization": f"Bearer {self.services[CloudService.RENDER]['api_key']}"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "key_changes": result.get("key_changes", []),
                        "modulations": result.get("modulations", []),
                        "success": True,
                        "cloud_service": CloudService.RENDER
                    }
                else:
                    raise Exception(f"Cloud service returned {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Cloud key detection failed: {str(e)}")
            raise
    
    async def _local_key_detection_fallback(self, audio_path: str) -> Dict[str, Any]:
        """Fallback to local processing for key detection"""
        logger.info("Using local fallback for key detection")
        
        return {
            "key_changes": [],  # No key changes detected in fallback
            "modulations": [],
            "success": True,
            "cloud_service": None,
            "fallback": True
        }
    
    async def process_with_orchestration(self, audio_path: str) -> Dict[str, Any]:
        """
        Orchestrate the full cloud processing pipeline
        """
        processing_start = time.time()
        cloud_services_used = []
        
        try:
            # Step 1: Source separation
            logger.info("Starting source separation...")
            separation_result = await self.separate_sources(audio_path)
            if separation_result.get("cloud_service"):
                cloud_services_used.append(separation_result["cloud_service"])
            
            # Use separated harmonic track for analysis, or original if separation failed
            analysis_audio = separation_result.get("other_path", audio_path)
            
            # Step 2: Song structure analysis (in parallel with key detection)
            logger.info("Starting parallel cloud analysis...")
            structure_task = self.analyze_song_structure(analysis_audio)
            key_task = self.detect_advanced_key_changes(analysis_audio)
            
            structure_result, key_result = await asyncio.gather(
                structure_task, key_task, return_exceptions=True
            )
            
            # Handle results and track cloud services used
            if not isinstance(structure_result, Exception):
                if structure_result.get("cloud_service"):
                    cloud_services_used.append(structure_result["cloud_service"])
            else:
                logger.error(f"Structure analysis failed: {structure_result}")
                structure_result = {"segments": [], "success": False}
            
            if not isinstance(key_result, Exception):
                if key_result.get("cloud_service"):
                    cloud_services_used.append(key_result["cloud_service"])
            else:
                logger.error(f"Key detection failed: {key_result}")
                key_result = {"key_changes": [], "modulations": [], "success": False}
            
            processing_time = time.time() - processing_start
            
            return {
                "source_separation": separation_result,
                "song_structure": structure_result,
                "key_analysis": key_result,
                "processing_metadata": {
                    "cloudServices": cloud_services_used,
                    "sourceSeparation": separation_result.get("success", False),
                    "processingTime": processing_time,
                    "queuePosition": None  # TODO: Implement queue management
                }
            }
            
        except Exception as e:
            logger.error(f"Cloud orchestration failed: {str(e)}")
            processing_time = time.time() - processing_start
            
            return {
                "source_separation": {"success": False, "fallback": True},
                "song_structure": {"segments": [], "success": False},
                "key_analysis": {"key_changes": [], "modulations": [], "success": False},
                "processing_metadata": {
                    "cloudServices": cloud_services_used,
                    "sourceSeparation": False,
                    "processingTime": processing_time,
                    "queuePosition": None,
                    "error": str(e)
                }
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get the status of all cloud services"""
        status = {}
        for service in CloudService:
            health_info = self.service_health.get(service, {"healthy": False, "last_check": None})
            status[service] = {
                "enabled": self.services.get(service, {}).get("enabled", False),
                "healthy": health_info["healthy"],
                "last_check": health_info.get("last_check"),
                "error": health_info.get("error")
            }
        return status

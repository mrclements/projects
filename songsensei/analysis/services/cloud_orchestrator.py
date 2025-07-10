import asyncio
import time
from typing import Dict, Any, List, Optional
from loguru import logger
import httpx
import os
from enum import Enum

class CloudService(str, Enum):
    DEMUCS = "demucs"     # New service for Demucs v4
    SPLEETER = "spleeter" # Keep for backward compatibility
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
            # Hugging Face Spaces for Demucs v4 source separation
            demucs_url = os.getenv("HUGGINGFACE_DEMUCS_URL", os.getenv("HUGGINGFACE_SPLEETER_URL", ""))
            # Ensure the URL doesn't have duplicate /api/predict
            if demucs_url and "/api/predict" in demucs_url:
                self.services[CloudService.DEMUCS] = {
                    "base_url": demucs_url,
                    "api_key": os.getenv("HUGGINGFACE_API_TOKEN", ""),
                    "enabled": bool(os.getenv("HUGGINGFACE_API_TOKEN")),
                    "has_api_predict": True
                }
            else:
                self.services[CloudService.DEMUCS] = {
                    "base_url": demucs_url,
                    "api_key": os.getenv("HUGGINGFACE_API_TOKEN", ""),
                    "enabled": bool(os.getenv("HUGGINGFACE_API_TOKEN")),
                    "has_api_predict": False
                }
            
            # Keep Spleeter for backward compatibility
            spleeter_url = os.getenv("HUGGINGFACE_SPLEETER_URL", "")
            # Ensure the URL doesn't have duplicate /api/predict
            if spleeter_url and "/api/predict" in spleeter_url:
                self.services[CloudService.SPLEETER] = {
                    "base_url": spleeter_url,
                    "api_key": os.getenv("HUGGINGFACE_API_TOKEN", ""),
                    "enabled": bool(os.getenv("HUGGINGFACE_API_TOKEN")),
                    "has_api_predict": True
                }
            else:
                self.services[CloudService.SPLEETER] = {
                    "base_url": spleeter_url,
                    "api_key": os.getenv("HUGGINGFACE_API_TOKEN", ""),
                    "enabled": bool(os.getenv("HUGGINGFACE_API_TOKEN")),
                    "has_api_predict": False
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
    
    async def health_check(self, service: CloudService, max_retries: int = 3) -> bool:
        """
        Check if a cloud service is available
        
        For Hugging Face Spaces, implements retry logic to handle space wake-up (503 errors)
        """
        try:
            if not self.services[service]["enabled"]:
                logger.info(f"Service {service} is disabled, skipping health check")
                return False
            
            # Different health check approaches based on service type
            if service in [CloudService.SPLEETER, CloudService.DEMUCS]:
                return await self._huggingface_health_check(service, max_retries)
            else:
                # Default health check for other services
                return await self._standard_health_check(service)
            
        except Exception as e:
            logger.warning(f"Health check failed for {service}: {str(e)}")
            self.service_health[service] = {
                "healthy": False,
                "last_check": time.time(),
                "error": str(e)
            }
            return False
    
    async def _huggingface_health_check(self, service: CloudService, max_retries: int = 3) -> bool:
        """
        Health check specifically for Hugging Face Spaces with retry logic
        to handle spaces that are waking up or hibernating
        """
        base_url = self.services[service]['base_url']
        api_key = self.services[service]['api_key']
        
        # Ensure URL doesn't end with a slash
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        
        # Remove /api/predict if present as we just want to check connectivity
        if base_url.endswith('/api/predict'):
            base_url = base_url.replace('/api/predict', '')
        
        logger.info(f"Checking health of {service} at {base_url}")
        
        # Initialize retry counter and backoff time
        retries = 0
        backoff_time = 1.0  # Start with 1 second
        
        while retries <= max_retries:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:  # Extended timeout for reliability
                    try:
                        response = await client.get(
                            base_url,
                            headers={"Authorization": f"Bearer {api_key}"}
                        )
                        status_code = response.status_code
                        logger.info(f"Health check for {service} (retry {retries}): status code {status_code}")
                        
                        # Status handling:
                        # 2xx: Service is up and running
                        # 503: Service is waking up from hibernation
                        # Other: Service has some other issue
                        
                        if 200 <= status_code < 300:
                            # Success! Service is available
                            healthy = True
                            break
                        elif status_code == 503 and retries < max_retries:
                            # Space is hibernating and waking up
                            logger.info(f"Service {service} is waking up (503). Retrying in {backoff_time:.1f}s...")
                            await asyncio.sleep(backoff_time)
                            backoff_time *= 2  # Exponential backoff
                            retries += 1
                            continue
                        else:
                            # Other status codes are treated as errors
                            logger.warning(f"Service {service} returned unexpected status {status_code}")
                            healthy = False
                            break
                            
                    except Exception as e:
                        logger.error(f"Error during {service} health check request (retry {retries}): {str(e)}")
                        if retries < max_retries:
                            await asyncio.sleep(backoff_time)
                            backoff_time *= 2
                            retries += 1
                            continue
                        healthy = False
                        break
                        
            except Exception as outer_e:
                logger.error(f"Outer error during health check for {service}: {str(outer_e)}")
                healthy = False
                break
        
        # Update service health status
        self.service_health[service] = {
            "healthy": healthy,
            "last_check": time.time(),
            "retries": retries,
            "wake_up_attempted": retries > 0
        }
        
        return healthy
    
    async def _standard_health_check(self, service: CloudService) -> bool:
        """Standard health check for non-Hugging Face services"""
        logger.info(f"Using standard health check for {service}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.services[service]['base_url']}/health",
                    headers={"Authorization": f"Bearer {self.services[service]['api_key']}"}
                )
                logger.info(f"Health check for {service}: status code {response.status_code}")
                healthy = response.status_code == 200
            
            self.service_health[service] = {
                "healthy": healthy,
                "last_check": time.time()
            }
            
            return healthy
        except Exception as e:
            logger.error(f"Standard health check failed for {service}: {str(e)}")
            self.service_health[service] = {
                "healthy": False,
                "last_check": time.time(),
                "error": str(e)
            }
            return False
    
    async def separate_sources(self, audio_path: str) -> Dict[str, Any]:
        """
        Separate audio sources using Demucs v4 via Hugging Face Spaces
        Falls back to Spleeter if Demucs unavailable, then to local processing
        """
        try:
            # First try Demucs v4
            if await self.health_check(CloudService.DEMUCS):
                logger.info("Using cloud source separation (Demucs v4)")
                return await self._cloud_demucs_separation(audio_path)
            # Fall back to Spleeter if Demucs is unavailable
            elif await self.health_check(CloudService.SPLEETER):
                logger.info("Demucs unavailable, falling back to Spleeter")
                return await self._cloud_source_separation(audio_path)
            else:
                logger.info("Cloud services unavailable, using local fallback")
                return await self._local_source_separation_fallback(audio_path)
                
        except Exception as e:
            logger.error(f"Source separation failed: {str(e)}")
            # Try Spleeter as fallback if Demucs fails
            try:
                if await self.health_check(CloudService.SPLEETER):
                    logger.info("Falling back to Spleeter after Demucs failure")
                    return await self._cloud_source_separation(audio_path)
            except Exception as spleeter_error:
                logger.error(f"Spleeter fallback also failed: {str(spleeter_error)}")
                
            return await self._local_source_separation_fallback(audio_path)
    
    async def _cloud_demucs_separation(self, audio_path: str) -> Dict[str, Any]:
        """Perform source separation using Demucs v4 via Hugging Face Spaces Gradio API"""
        try:
            # Read audio file
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # For Gradio API in Hugging Face Spaces
            async with httpx.AsyncClient(timeout=120.0) as client:  # Longer timeout for Demucs
                # Check if the base_url already contains /api/predict
                if self.services[CloudService.DEMUCS].get("has_api_predict", False):
                    url = f"{self.services[CloudService.DEMUCS]['base_url']}"
                else:
                    url = f"{self.services[CloudService.DEMUCS]['base_url']}/api/predict"
                
                logger.info(f"Sending request to Demucs at: {url}")
                
                response = await client.post(
                    url,
                    files={"data": ("audio.wav", audio_data, "audio/wav")},
                    headers={"Authorization": f"Bearer {self.services[CloudService.DEMUCS]['api_key']}"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Handle Gradio API response format which might be nested
                    # The output will contain URLs to each stem
                    if isinstance(result, list):
                        # Demucs v4 typically returns: drums, bass, other, vocals (and possibly guitar, piano)
                        # Map the sources by their expected positions
                        stems = {}
                        source_names = ["drums", "bass", "other", "vocals"]
                        
                        # For standard 4-stem model
                        if len(result) >= 4:
                            for i, name in enumerate(source_names):
                                if i < len(result) and result[i]:
                                    stems[name] = result[i]
                            
                            # Add any additional stems with their index names
                            for i in range(4, len(result)):
                                if result[i]:
                                    stems[f"stem_{i}"] = result[i]
                        
                        return {
                            **stems,  # Include all stems dynamically
                            "success": True,
                            "cloud_service": CloudService.DEMUCS
                        }
                    else:
                        # Standard API response with named fields
                        stems = {}
                        for key, value in result.items():
                            # Convert keys like "vocals_url" to "vocals_path"
                            if key.endswith("_url"):
                                stem_name = key.replace("_url", "")
                                stems[f"{stem_name}_path"] = value
                        
                        return {
                            **stems,
                            "success": True,
                            "cloud_service": CloudService.DEMUCS
                        }
                else:
                    raise Exception(f"Cloud service returned {response.status_code}")
        except Exception as e:
            logger.error(f"Cloud Demucs separation failed: {str(e)}")
            raise
                    
    async def _cloud_source_separation(self, audio_path: str) -> Dict[str, Any]:
        """Perform source separation using Spleeter via Hugging Face Spaces with Gradio API"""
        try:
            # Read audio file
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # For Gradio API in Hugging Face Spaces
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Check if the base_url already contains /api/predict
                if self.services[CloudService.SPLEETER].get("has_api_predict", False):
                    url = f"{self.services[CloudService.SPLEETER]['base_url']}"
                else:
                    url = f"{self.services[CloudService.SPLEETER]['base_url']}/api/predict"
                
                logger.info(f"Sending request to Spleeter at: {url}")
                
                response = await client.post(
                    url,
                    files={"data": ("audio.wav", audio_data, "audio/wav")},
                    headers={"Authorization": f"Bearer {self.services[CloudService.SPLEETER]['api_key']}"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Handle Gradio API response format which might be nested
                    # The output will contain URLs to each stem
                    if isinstance(result, list) and len(result) >= 4:
                        # For Gradio interface that returns a list of outputs
                        return {
                            "vocals_path": result[0] if result[0] else None,
                            "drums_path": result[1] if result[1] else None,
                            "bass_path": result[2] if result[2] else None,
                            "other_path": result[3] if result[3] else None,  # Harmonic content
                            "success": True,
                            "cloud_service": CloudService.SPLEETER
                        }
                    else:
                        # Standard API response with named fields
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
        
        try:
            # Simple local separation for basic harmonic/percussive separation
            # Much less effective than Spleeter but better than nothing
            import librosa
            y, sr = librosa.load(audio_path, sr=None)
            
            # Harmonic-percussive separation (not as good as Spleeter but available locally)
            harmonic, percussive = librosa.effects.hpss(y)
            
            # Create temp files for the separated tracks
            import os
            import soundfile as sf
            
            base_dir = os.path.dirname(audio_path)
            harmonic_path = os.path.join(base_dir, "harmonic.wav")
            percussive_path = os.path.join(base_dir, "percussive.wav")
            
            # Save the separated tracks
            sf.write(harmonic_path, harmonic, sr)
            sf.write(percussive_path, percussive, sr)
            
            return {
                "vocals_path": None,  # Can't separate vocals with HPSS
                "drums_path": percussive_path,  # Percussive content
                "bass_path": None,  # Can't separate bass with HPSS
                "other_path": harmonic_path,  # Harmonic content for chord detection
                "success": True,
                "cloud_service": None,
                "fallback": True
            }
        except Exception as e:
            logger.error(f"Local separation fallback failed: {str(e)}")
            # If even the local separation fails, just use the original audio
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

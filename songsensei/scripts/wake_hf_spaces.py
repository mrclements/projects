#!/usr/bin/env python3
"""
wake_hf_spaces.py

This script periodically pings Hugging Face spaces to keep them awake and ready for use.
It prevents cold starts when users try to use source separation features.

Usage:
    python wake_hf_spaces.py
"""

import os
import asyncio
import time
from datetime import datetime
import httpx
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logging
logger.add("wake_spaces.log", rotation="10 MB", retention="7 days")

# Get configuration from environment variables
HUGGINGFACE_SPLEETER_URL = os.getenv("HUGGINGFACE_SPLEETER_URL")
HUGGINGFACE_DEMUCS_URL = os.getenv("HUGGINGFACE_DEMUCS_URL")
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
ENABLE_CLOUD_SERVICES_STR = os.getenv("ENABLE_CLOUD_SERVICES", "false")
ENABLE_CLOUD_SERVICES = ENABLE_CLOUD_SERVICES_STR.lower() == "true"

# Default wakeup interval in seconds (every 5 minutes to keep spaces more consistently awake)
WAKEUP_INTERVAL = 300


async def ping_space(client, space_url, space_name, max_retries=3):
    """Ping a Hugging Face space to keep it awake with retry logic."""
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

    headers = {}
    if HUGGINGFACE_API_TOKEN:
        headers["Authorization"] = f"Bearer {HUGGINGFACE_API_TOKEN}"

    # Initialize retry counter and backoff time
    retries = 0
    backoff_time = 1.0  # Start with 1 second

    while retries <= max_retries:
        try:
            logger.info(f"Pinging {space_name} at {health_url} (attempt {retries+1}/{max_retries+1})")
            response = await client.get(health_url, headers=headers, timeout=30.0)
            
            if response.status_code == 200:
                logger.success(f"Successfully pinged {space_name}: {response.text}")
                return True
            elif response.status_code == 503 and retries < max_retries:
                # Space is hibernating and waking up
                logger.warning(f"{space_name} is waking up (503). Retrying in {backoff_time:.1f}s...")
                await asyncio.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
                retries += 1
                continue
            else:
                logger.error(f"Failed to ping {space_name}: Status {response.status_code}, {response.text}")
                if retries < max_retries:
                    logger.info(f"Retrying in {backoff_time:.1f}s...")
                    await asyncio.sleep(backoff_time)
                    backoff_time *= 2
                    retries += 1
                    continue
                return False
        except Exception as e:
            logger.error(f"Error pinging {space_name}: {str(e)}")
            if retries < max_retries:
                logger.info(f"Retrying in {backoff_time:.1f}s...")
                await asyncio.sleep(backoff_time)
                backoff_time *= 2
                retries += 1
                continue
            return False
    
    return False


async def wake_spaces():
    """Ping all configured Hugging Face spaces to keep them awake."""
    # Always try to ping the spaces regardless of ENABLE_CLOUD_SERVICES setting
    # This ensures services remain awake even if temporarily disabled in the app
    enabled = ENABLE_CLOUD_SERVICES
    
    if not enabled:
        logger.warning("Cloud services are set to disabled in configuration, but still attempting wakeup to maintain readiness.")
    
    try:
        async with httpx.AsyncClient() as client:
            # If we have both URLs, ping them concurrently for efficiency
            tasks = []
            
            if HUGGINGFACE_SPLEETER_URL:
                tasks.append(ping_space(client, HUGGINGFACE_SPLEETER_URL, "Spleeter Space"))
            else:
                logger.warning("Spleeter URL not configured")
                
            if HUGGINGFACE_DEMUCS_URL:
                tasks.append(ping_space(client, HUGGINGFACE_DEMUCS_URL, "Demucs Space"))
            else:
                logger.warning("Demucs URL not configured")
                
            if not tasks:
                logger.error("No HuggingFace spaces configured. Check environment variables.")
                return {
                    "spleeter": False,
                    "demucs": False,
                    "enabled": enabled,
                    "timestamp": datetime.now().isoformat(),
                    "error": "No HuggingFace spaces configured"
                }
                
            # Ping all spaces concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            spleeter_status = False
            demucs_status = False
            
            result_idx = 0
            if HUGGINGFACE_SPLEETER_URL:
                if isinstance(results[result_idx], Exception):
                    logger.error(f"Error waking Spleeter space: {results[result_idx]}")
                    spleeter_status = False
                else:
                    spleeter_status = results[result_idx]
                result_idx += 1
                
            if HUGGINGFACE_DEMUCS_URL:
                if isinstance(results[result_idx], Exception):
                    logger.error(f"Error waking Demucs space: {results[result_idx]}")
                    demucs_status = False
                else:
                    demucs_status = results[result_idx]
            
            return {
                "spleeter": spleeter_status,
                "demucs": demucs_status,
                "enabled": enabled,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error in wake_spaces: {str(e)}")
        return {
            "spleeter": False,
            "demucs": False,
            "enabled": enabled,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


if __name__ == "__main__":
    logger.info(f"Starting Hugging Face Spaces wakeup service")
    logger.info(f"Cloud services enabled setting: {ENABLE_CLOUD_SERVICES}")
    logger.info(f"Spleeter URL: {HUGGINGFACE_SPLEETER_URL or 'Not configured'}")
    logger.info(f"Demucs URL: {HUGGINGFACE_DEMUCS_URL or 'Not configured'}")
    
    # Check if any URLs are configured
    if not HUGGINGFACE_SPLEETER_URL and not HUGGINGFACE_DEMUCS_URL:
        logger.error("No Hugging Face space URLs configured. Check your .env file.")
    
    # Check if API token is available
    if not HUGGINGFACE_API_TOKEN:
        logger.warning("No Hugging Face API token found. Authentication may fail.")
    
    # Always run in continuous mode in Docker environment
    continuous = True
    interval = WAKEUP_INTERVAL
    
    try:
        # Run the wakeup once immediately
        result = asyncio.run(wake_spaces())
        logger.info(f"Initial wakeup results: {result}")
        
        if continuous:
            logger.info(f"Running in continuous mode, will wake up every {interval} seconds")
            
            # Count for logging purposes
            wakeup_count = 1
            
            while True:
                try:
                    # Sleep until next interval
                    time.sleep(interval)
                    # Run the wakeup
                    wakeup_count += 1
                    logger.info(f"Performing wakeup #{wakeup_count}")
                    result = asyncio.run(wake_spaces())
                    logger.info(f"Wakeup #{wakeup_count} results: {result}")
                except Exception as e:
                    logger.error(f"Error in wakeup loop: {str(e)}")
                    # Continue despite errors
                    time.sleep(10)  # Short delay before retrying after an error
    except KeyboardInterrupt:
        logger.info("Wake spaces service stopped by user")
    except Exception as e:
        logger.error(f"Wake spaces service encountered an error: {str(e)}")

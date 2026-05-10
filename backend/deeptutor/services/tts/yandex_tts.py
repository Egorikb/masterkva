"""Yandex SpeechKit TTS integration."""

import hashlib
import os
import shutil
import requests
import uuid
from pathlib import Path


def get_yandex_key() -> str:
    """Load Yandex API key from environment."""
    env_path = Path("/home/egor/ai-agent/workspace/env/yandex.env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("YANDEX_API_KEY="):
                    return line.split("=", 1)[1].strip()
    # Fallback to env
    return os.getenv("YANDEX_API_KEY", "")


def synthesize_speech(text: str, voice: str = "filipp", emotion: str = "good", save_path: str = None) -> str | None:
    """Synthesize speech using Yandex SpeechKit with caching."""
    global output_dir
    
    # Determine output directory
    if save_path:
        output_dir = Path(save_path).parent
    else:
        output_dir = Path("/home/egor/ai-agent/workspace/deeptutor_analyzed/data/user/workspace/chat/audio")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = output_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Create cache filename based on text hash
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:12]
    cache_path = cache_dir / f"cache_{text_hash}.mp3"
    
    # Check cache first
    if cache_path.exists():
        print(f"--- [TTS CACHE] Using cached audio for: {text[:30]}...")
        if save_path:
            shutil.copy(cache_path, save_path)
            return save_path
        return str(cache_path)
    
    # Get API key
    api_key = get_yandex_key()
    if not api_key:
        print("Yandex API key not found")
        return None
    
    url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
    
    headers = {
        "Authorization": f"Api-Key {api_key}"
    }
    
    data = {
        "text": text,
        "voice": voice,
        "emotion": emotion,
        "format": "mp3",
        "speed": "1.0"
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=30)
        
        if response.status_code == 200:
            filename = f"voice_{uuid.uuid4().hex[:8]}.mp3"
            output_path = output_dir / filename
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            # Save to cache
            shutil.copy(output_path, cache_path)
            print(f"--- [TTS CACHE] Saved to cache: {cache_path.name}")
            
            return str(output_path)
        else:
            print(f"TTS Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"TTS Exception: {e}")
        return None


def get_audio_path(filename: str) -> str:
    """Get full path to audio file."""
    return f"/tmp/deeptutor_tts/{filename}"
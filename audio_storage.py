import os
import uuid
from pathlib import Path
import soundfile as sf
import numpy as np
from typing import Optional
from config import settings
from datetime import datetime


class AudioStorage:
    """Handles storage and retrieval of audio files"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize audio storage
        Args:
            storage_path: Path to store audio files
        """
        self.storage_path = Path(storage_path or settings.audio_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def save_audio(self, audio: np.ndarray, sample_rate: int = 16000, 
                   speaker_id: Optional[str] = None) -> str:
        """
        Save audio to file
        Args:
            audio: Audio numpy array
            sample_rate: Sample rate of audio
            speaker_id: Optional speaker ID for organizing files
        Returns:
            Path to saved audio file
        """
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}.wav"
        
        # Organize by speaker if provided
        if speaker_id:
            speaker_dir = self.storage_path / speaker_id
            speaker_dir.mkdir(exist_ok=True)
            filepath = speaker_dir / filename
        else:
            filepath = self.storage_path / filename
        
        # Save audio
        sf.write(str(filepath), audio, sample_rate)
        
        return str(filepath)
    
    def load_audio(self, filepath: str) -> tuple[np.ndarray, int]:
        """
        Load audio from file
        Args:
            filepath: Path to audio file
        Returns:
            Tuple of (audio, sample_rate)
        """
        audio, sample_rate = sf.read(filepath)
        return audio, sample_rate
    
    def delete_audio(self, filepath: str) -> bool:
        """
        Delete audio file
        Args:
            filepath: Path to audio file
        Returns:
            True if successful
        """
        try:
            Path(filepath).unlink(missing_ok=True)
            return True
        except Exception as e:
            print(f"Error deleting audio file: {e}")
            return False
    
    def get_audio_duration(self, filepath: str) -> float:
        """
        Get duration of audio file
        Args:
            filepath: Path to audio file
        Returns:
            Duration in seconds
        """
        try:
            info = sf.info(filepath)
            return info.duration
        except Exception:
            return 0.0

import numpy as np
import whisper
from typing import Tuple, Optional
from config import settings
import warnings

warnings.filterwarnings("ignore")


class SpeechRecognizer:
    """Transcribes speech and detects language using Whisper"""
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper model
        Args:
            model_size: Model size (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model"""
        try:
            print(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            print("Whisper model loaded successfully")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            self.model = None
    
    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> Tuple[str, str, float]:
        """
        Transcribe audio and detect language
        Args:
            audio: Audio numpy array
            sample_rate: Sample rate of audio
        Returns:
            Tuple of (transcription, language, confidence)
        """
        if self.model is None:
            return "", "unknown", 0.0
        
        try:
            # Whisper expects 16kHz audio
            if sample_rate != 16000:
                import librosa
                audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=16000)
            
            # Ensure audio is float32 and normalized
            audio = audio.astype(np.float32)
            if audio.max() > 1.0:
                audio = audio / 32768.0
            
            # Transcribe
            result = self.model.transcribe(
                audio,
                fp16=False,
                language=None,  # Auto-detect language
                task="transcribe"
            )
            
            transcription = result.get("text", "").strip()
            language = result.get("language", "unknown")
            
            # Calculate average confidence from segments
            segments = result.get("segments", [])
            if segments:
                confidences = [seg.get("no_speech_prob", 0.0) for seg in segments]
                confidence = 1.0 - (sum(confidences) / len(confidences))
            else:
                confidence = 0.0
            
            return transcription, language, confidence
            
        except Exception as e:
            print(f"Error during transcription: {e}")
            return "", "unknown", 0.0
    
    def detect_language(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Detect language in audio
        Args:
            audio: Audio numpy array
            sample_rate: Sample rate of audio
        Returns:
            Detected language code (e.g., 'en', 'es', 'fr')
        """
        if self.model is None:
            return "unknown"
        
        try:
            # Whisper expects 16kHz audio
            if sample_rate != 16000:
                import librosa
                audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=16000)
            
            # Ensure audio is float32
            audio = audio.astype(np.float32)
            if audio.max() > 1.0:
                audio = audio / 32768.0
            
            # Detect language (use first 30 seconds)
            audio_segment = audio[:30 * 16000]
            
            # Load audio into whisper format and detect language
            audio_padded = whisper.pad_or_trim(audio_segment)
            mel = whisper.log_mel_spectrogram(audio_padded).to(self.model.device)
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            
            return detected_language
            
        except Exception as e:
            print(f"Error detecting language: {e}")
            return "unknown"

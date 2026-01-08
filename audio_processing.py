import numpy as np
import webrtcvad
import librosa
import soundfile as sf
from typing import List, Tuple
from config import settings
import io


class VoiceActivityDetector:
    """Detects speech in audio stream using WebRTC VAD"""
    
    def __init__(self, aggressiveness: int = 3):
        """
        Initialize VAD
        Args:
            aggressiveness: 0-3, where 3 is most aggressive filtering
        """
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = 16000  # WebRTC VAD requires 16kHz
        self.frame_duration_ms = 30  # 30ms frames
        self.frame_length = int(self.sample_rate * self.frame_duration_ms / 1000)
        
    def is_speech(self, audio_data: bytes) -> bool:
        """
        Check if audio frame contains speech
        Args:
            audio_data: Raw audio bytes (16-bit PCM)
        Returns:
            True if speech detected
        """
        try:
            return self.vad.is_speech(audio_data, self.sample_rate)
        except Exception:
            return False
    
    def detect_speech_segments(self, audio: np.ndarray, sample_rate: int) -> List[Tuple[int, int]]:
        """
        Detect speech segments in audio
        Args:
            audio: Audio numpy array
            sample_rate: Sample rate of audio
        Returns:
            List of (start, end) tuples in samples
        """
        # Resample to 16kHz if needed
        if sample_rate != self.sample_rate:
            audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=self.sample_rate)
        
        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # Process in frames
        speech_frames = []
        num_frames = len(audio_int16) // self.frame_length
        
        for i in range(num_frames):
            start = i * self.frame_length
            end = start + self.frame_length
            frame = audio_int16[start:end].tobytes()
            
            if len(frame) == self.frame_length * 2:  # 2 bytes per sample
                speech_frames.append(self.is_speech(frame))
            else:
                speech_frames.append(False)
        
        # Group consecutive speech frames into segments
        segments = []
        in_speech = False
        speech_start = 0
        
        # Add padding (300ms before and after speech)
        padding_frames = 10
        
        for i, is_speech_frame in enumerate(speech_frames):
            if is_speech_frame and not in_speech:
                speech_start = max(0, i - padding_frames)
                in_speech = True
            elif not is_speech_frame and in_speech:
                speech_end = min(len(speech_frames), i + padding_frames)
                segments.append((
                    speech_start * self.frame_length,
                    speech_end * self.frame_length
                ))
                in_speech = False
        
        # Handle case where audio ends during speech
        if in_speech:
            segments.append((speech_start * self.frame_length, len(audio_int16)))
        
        return segments


class AudioSegmenter:
    """Segments audio stream into discrete voice messages"""
    
    def __init__(self):
        self.vad = VoiceActivityDetector(settings.vad_aggressiveness)
        self.sample_rate = 16000
        self.min_segment_duration = 0.5  # Minimum 0.5 seconds
        self.max_segment_duration = 30.0  # Maximum 30 seconds
        
    def segment_audio(self, audio: np.ndarray, sample_rate: int) -> List[np.ndarray]:
        """
        Segment audio into discrete voice messages
        Args:
            audio: Audio numpy array
            sample_rate: Sample rate of audio
        Returns:
            List of audio segments
        """
        segments_indices = self.vad.detect_speech_segments(audio, sample_rate)
        
        # Resample audio to target sample rate
        if sample_rate != self.sample_rate:
            audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=self.sample_rate)
        
        segments = []
        for start, end in segments_indices:
            segment = audio[start:end]
            duration = len(segment) / self.sample_rate
            
            # Filter by duration
            if self.min_segment_duration <= duration <= self.max_segment_duration:
                segments.append(segment)
        
        return segments
    
    def merge_short_segments(self, segments: List[np.ndarray], max_gap_duration: float = 1.0) -> List[np.ndarray]:
        """
        Merge segments that are close together
        Args:
            segments: List of audio segments
            max_gap_duration: Maximum gap between segments to merge (seconds)
        Returns:
            List of merged segments
        """
        if not segments:
            return []
        
        merged = [segments[0]]
        max_gap_samples = int(max_gap_duration * self.sample_rate)
        
        for segment in segments[1:]:
            # If segments are close, merge them
            gap = np.zeros(max_gap_samples)
            merged[-1] = np.concatenate([merged[-1], gap, segment])
        
        return merged

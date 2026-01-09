import numpy as np
import torch
import torchaudio
from typing import Optional, Tuple
from config import settings
import io
import pickle


class SpeakerRecognizer:
    """Identifies speakers using voice embeddings"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.threshold = settings.speaker_threshold
        self._load_model()
        
    def _load_model(self):
        """Load pre-trained speaker recognition model"""
        try:
            # Using a simple speaker verification approach with torchaudio
            # In production, you'd use a more sophisticated model like SpeechBrain or pyannote
            bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
            self.model = bundle.get_model().to(self.device)
            self.model.eval()
        except Exception as e:
            print(f"Warning: Could not load speaker model: {e}")
            self.model = None
    
    def extract_embedding(self, audio: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Extract speaker embedding from audio
        Args:
            audio: Audio numpy array
            sample_rate: Sample rate of audio
        Returns:
            Speaker embedding as numpy array
        """
        if self.model is None:
            # Fallback: use simple spectral features
            return self._extract_simple_embedding(audio, sample_rate)
        
        try:
            # Convert to torch tensor
            waveform = torch.from_numpy(audio).float().unsqueeze(0).to(self.device)
            
            # Resample if needed
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000).to(self.device)
                waveform = resampler(waveform)
            
            # Extract features
            with torch.no_grad():
                features, _ = self.model.extract_features(waveform)
                # Average pooling over time dimension
                embedding = features[-1].mean(dim=1).squeeze().cpu().numpy()
            
            # Normalize embedding
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            return embedding
            
        except Exception as e:
            print(f"Error extracting embedding: {e}")
            return self._extract_simple_embedding(audio, sample_rate)
    
    def _extract_simple_embedding(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Fallback: Extract simple spectral features as embedding
        """
        # Compute MFCC features
        import librosa
        mfcc = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=40)
        # Average over time
        embedding = np.mean(mfcc, axis=1)
        # Normalize
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        return embedding
    
    def compare_embeddings(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compare two speaker embeddings
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2) + 1e-8
        )
        return float(similarity)
    
    def is_same_speaker(self, embedding1: np.ndarray, embedding2: np.ndarray) -> bool:
        """
        Determine if two embeddings are from the same speaker
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        Returns:
            True if same speaker
        """
        similarity = self.compare_embeddings(embedding1, embedding2)
        return similarity >= self.threshold
    
    def serialize_embedding(self, embedding: np.ndarray) -> bytes:
        """Serialize embedding to bytes for database storage"""
        return pickle.dumps(embedding)
    
    def deserialize_embedding(self, data: bytes) -> np.ndarray:
        """Deserialize embedding from bytes"""
        return pickle.loads(data)

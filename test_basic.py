"""
Basic tests for VoxTrace components
"""

import numpy as np
import pytest
from audio_processing import VoiceActivityDetector, AudioSegmenter
from speaker_recognition import SpeakerRecognizer
from audio_storage import AudioStorage
import tempfile
import os


def test_voice_activity_detector():
    """Test VAD initialization and basic functionality"""
    vad = VoiceActivityDetector(aggressiveness=3)
    assert vad.sample_rate == 16000
    assert vad.frame_duration_ms == 30
    
    # Create dummy audio (silence)
    audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
    segments = vad.detect_speech_segments(audio, 16000)
    # Silence should produce no segments or very few
    assert isinstance(segments, list)


def test_audio_segmenter():
    """Test audio segmentation"""
    segmenter = AudioSegmenter()
    assert segmenter.sample_rate == 16000
    
    # Create dummy audio
    audio = np.random.randn(32000).astype(np.float32)  # 2 seconds
    segments = segmenter.segment_audio(audio, 16000)
    assert isinstance(segments, list)


def test_speaker_recognizer():
    """Test speaker recognition"""
    recognizer = SpeakerRecognizer()
    
    # Create dummy audio
    audio = np.random.randn(16000).astype(np.float32)  # 1 second
    
    # Extract embedding
    embedding = recognizer.extract_embedding(audio, 16000)
    assert isinstance(embedding, np.ndarray)
    assert len(embedding) > 0
    
    # Test serialization
    serialized = recognizer.serialize_embedding(embedding)
    assert isinstance(serialized, bytes)
    
    deserialized = recognizer.deserialize_embedding(serialized)
    assert np.allclose(embedding, deserialized)
    
    # Test comparison
    embedding2 = recognizer.extract_embedding(audio, 16000)
    similarity = recognizer.compare_embeddings(embedding, embedding2)
    assert 0 <= similarity <= 1


def test_audio_storage():
    """Test audio storage"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = AudioStorage(tmpdir)
        
        # Create and save audio
        audio = np.random.randn(16000).astype(np.float32)
        filepath = storage.save_audio(audio, 16000, speaker_id="test_speaker")
        
        assert os.path.exists(filepath)
        
        # Load audio
        loaded_audio, sample_rate = storage.load_audio(filepath)
        assert sample_rate == 16000
        assert len(loaded_audio) > 0
        
        # Get duration
        duration = storage.get_audio_duration(filepath)
        assert duration > 0
        
        # Delete audio
        success = storage.delete_audio(filepath)
        assert success
        assert not os.path.exists(filepath)


def test_embedding_comparison():
    """Test that identical audio produces similar embeddings"""
    recognizer = SpeakerRecognizer()
    
    # Create same audio twice
    audio = np.random.randn(16000).astype(np.float32)
    
    embedding1 = recognizer.extract_embedding(audio, 16000)
    embedding2 = recognizer.extract_embedding(audio, 16000)
    
    # Should be very similar (or identical)
    similarity = recognizer.compare_embeddings(embedding1, embedding2)
    assert similarity > 0.95  # High similarity for same audio


if __name__ == "__main__":
    print("Running tests...")
    test_voice_activity_detector()
    print("✅ VAD test passed")
    
    test_audio_segmenter()
    print("✅ Audio segmenter test passed")
    
    test_speaker_recognizer()
    print("✅ Speaker recognizer test passed")
    
    test_audio_storage()
    print("✅ Audio storage test passed")
    
    test_embedding_comparison()
    print("✅ Embedding comparison test passed")
    
    print("\n🎉 All tests passed!")

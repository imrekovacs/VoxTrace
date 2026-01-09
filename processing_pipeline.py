import numpy as np
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

from audio_processing import AudioSegmenter
from speaker_recognition import SpeakerRecognizer
from speech_recognition import SpeechRecognizer
from audio_storage import AudioStorage
from database import Speaker, VoiceMessage, get_db
from config import settings


class VoiceProcessingPipeline:
    """Main pipeline for processing voice messages"""
    
    def __init__(self):
        self.segmenter = AudioSegmenter()
        self.speaker_recognizer = SpeakerRecognizer()
        self.speech_recognizer = SpeechRecognizer(settings.whisper_model)
        self.audio_storage = AudioStorage()
        
    def process_audio_stream(self, audio: np.ndarray, sample_rate: int, 
                            db: Session) -> List[Dict]:
        """
        Process continuous audio stream
        Args:
            audio: Audio numpy array
            sample_rate: Sample rate
            db: Database session
        Returns:
            List of processed voice message metadata
        """
        results = []
        
        # Step 1: Segment audio into discrete voice messages
        segments = self.segmenter.segment_audio(audio, sample_rate)
        
        if not segments:
            return results
        
        # Step 2: Process each segment
        for segment in segments:
            result = self.process_voice_segment(segment, sample_rate, db)
            if result:
                results.append(result)
        
        return results
    
    def process_voice_segment(self, audio: np.ndarray, sample_rate: int, 
                             db: Session) -> Optional[Dict]:
        """
        Process a single voice segment
        Args:
            audio: Audio segment
            sample_rate: Sample rate
            db: Database session
        Returns:
            Metadata dictionary or None
        """
        try:
            # Step 1: Extract speaker embedding
            embedding = self.speaker_recognizer.extract_embedding(audio, sample_rate)
            
            # Step 2: Identify speaker (new or known)
            speaker = self._identify_or_create_speaker(embedding, db)
            
            # Step 3: Detect language and transcribe
            transcription, language, confidence = self.speech_recognizer.transcribe(
                audio, sample_rate
            )
            
            # Step 4: Save audio file
            audio_path = self.audio_storage.save_audio(
                audio, sample_rate, speaker.speaker_id
            )
            
            # Step 5: Calculate duration
            duration = len(audio) / sample_rate
            
            # Step 6: Store in database
            voice_message = VoiceMessage(
                speaker_id=speaker.id,
                audio_file_path=audio_path,
                duration=duration,
                detected_language=language,
                transcription=transcription,
                confidence_score=confidence,
                timestamp=datetime.utcnow()
            )
            db.add(voice_message)
            
            # Update speaker last_seen
            speaker.last_seen = datetime.utcnow()
            
            db.commit()
            db.refresh(voice_message)
            
            return {
                "id": voice_message.id,
                "speaker_id": speaker.speaker_id,
                "is_new_speaker": speaker.first_seen == speaker.last_seen,
                "language": language,
                "transcription": transcription,
                "confidence": confidence,
                "duration": duration,
                "timestamp": voice_message.timestamp.isoformat(),
                "audio_path": audio_path
            }
            
        except Exception as e:
            print(f"Error processing voice segment: {e}")
            db.rollback()
            return None
    
    def _identify_or_create_speaker(self, embedding: np.ndarray, 
                                   db: Session) -> Speaker:
        """
        Identify speaker or create new speaker entry
        Args:
            embedding: Speaker embedding
            db: Database session
        Returns:
            Speaker object
        """
        # Get all known speakers
        speakers = db.query(Speaker).all()
        
        # Compare with known speakers
        best_match = None
        best_similarity = 0.0
        
        for speaker in speakers:
            stored_embedding = self.speaker_recognizer.deserialize_embedding(
                speaker.embedding
            )
            similarity = self.speaker_recognizer.compare_embeddings(
                embedding, stored_embedding
            )
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = speaker
        
        # Check if we found a match
        if best_match and self.speaker_recognizer.is_same_speaker(
            embedding,
            self.speaker_recognizer.deserialize_embedding(best_match.embedding)
        ):
            return best_match
        
        # Create new speaker
        speaker_id = f"speaker_{str(uuid.uuid4())[:8]}"
        new_speaker = Speaker(
            speaker_id=speaker_id,
            embedding=self.speaker_recognizer.serialize_embedding(embedding),
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        db.add(new_speaker)
        db.commit()
        db.refresh(new_speaker)
        
        return new_speaker

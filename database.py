from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, LargeBinary, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import settings

Base = declarative_base()


class Speaker(Base):
    __tablename__ = "speakers"
    
    id = Column(Integer, primary_key=True, index=True)
    speaker_id = Column(String, unique=True, index=True, nullable=False)
    embedding = Column(LargeBinary, nullable=False)  # Stored as binary numpy array
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    voice_messages = relationship("VoiceMessage", back_populates="speaker")


class VoiceMessage(Base):
    __tablename__ = "voice_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    speaker_id = Column(Integer, ForeignKey("speakers.id"), nullable=False)
    audio_file_path = Column(String, nullable=False)
    duration = Column(Float, nullable=False)
    detected_language = Column(String, nullable=True)
    transcription = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    confidence_score = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)  # Editable notes field
    
    speaker = relationship("Speaker", back_populates="voice_messages")


# Database setup
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, LargeBinary, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import ProgrammingError, OperationalError
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
    
    # Add missing columns to existing tables (for migrations)
    # This handles the case where the model has new columns that don't exist in the database
    try:
        with engine.begin() as conn:
            # Check if 'notes' column exists in voice_messages table
            # This query works with PostgreSQL using information_schema
            result = conn.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name='voice_messages' AND column_name='notes'")
            )
            if result.fetchone() is None:
                # Column doesn't exist, add it with explicit NULL constraint
                conn.execute(text("ALTER TABLE voice_messages ADD COLUMN notes TEXT NULL"))
    except (ProgrammingError, OperationalError):
        # If table doesn't exist yet or any other database error, create_all already handles table creation
        # The notes column will be created as part of the table creation
        pass


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

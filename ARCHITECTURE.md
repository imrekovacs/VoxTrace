# VoxTrace Architecture

## Overview

VoxTrace is a real-time voice processing system that detects speech, identifies speakers, transcribes audio, and stores metadata. This document describes the system architecture and component interactions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Web Interface (main.py)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   FastAPI    │  │   REST API   │  │   WebSocket Endpoint     │  │
│  │   Server     │  │   Endpoints  │  │   /ws/audio              │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Voice Processing Pipeline (processing_pipeline.py)      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  process_audio_stream()                                       │  │
│  │    1. Segment audio into messages                             │  │
│  │    2. Extract speaker embeddings                              │  │
│  │    3. Identify/create speaker                                 │  │
│  │    4. Detect language & transcribe                            │  │
│  │    5. Save audio file                                         │  │
│  │    6. Store metadata in database                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
┌─────────────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────┐
│ Audio Processing│ │ Speaker  │ │ Speech   │ │ Audio Storage   │
│ (audio_         │ │ Recog.   │ │ Recog.   │ │ (audio_         │
│  processing.py) │ │ (speaker_│ │ (speech_ │ │  storage.py)    │
│                 │ │  recogni-│ │  recogni-│ │                 │
│ • VAD           │ │  tion.py)│ │  tion.py)│ │ • Save audio    │
│ • Segmentation  │ │          │ │          │ │ • Load audio    │
│                 │ │ • Embed. │ │ • Whisper│ │ • File mgmt     │
└─────────────────┘ │ • Compare│ │ • Lang   │ └─────────────────┘
                    │ • Match  │ │   detect │
                    └──────────┘ └──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   Database Layer     │
              │   (database.py)      │
              │                      │
              │  • Speaker model     │
              │  • VoiceMessage      │
              │  • PostgreSQL        │
              └─────────────────────┘
```

## Core Components

### 1. Web Interface (main.py)

**Purpose**: HTTP server providing REST API and web UI

**Key Features**:
- FastAPI-based REST API
- WebSocket support for real-time streaming
- Modern web interface with drag-and-drop upload
- Real-time statistics display

**Endpoints**:
- `GET /` - Web interface
- `POST /api/process-audio` - Upload & process audio
- `GET /api/messages` - Retrieve voice messages
- `GET /api/speakers` - Get speaker list
- `GET /api/stats` - System statistics
- `WS /ws/audio` - WebSocket streaming

### 2. Processing Pipeline (processing_pipeline.py)

**Purpose**: Orchestrates the entire audio processing workflow

**Key Class**: `VoiceProcessingPipeline`

**Workflow**:
1. Receive audio stream
2. Segment into discrete messages
3. Extract speaker embedding
4. Identify or create speaker
5. Transcribe and detect language
6. Save audio file
7. Store metadata in database

**Methods**:
- `process_audio_stream(audio, sample_rate, db)` - Main entry point
- `process_voice_segment(audio, sample_rate, db)` - Process single segment
- `_identify_or_create_speaker(embedding, db)` - Speaker identification

### 3. Audio Processing (audio_processing.py)

**Purpose**: Voice Activity Detection and audio segmentation

**Key Classes**:

#### VoiceActivityDetector
- Uses WebRTC VAD for speech detection
- Configurable aggressiveness (0-3)
- Operates on 16kHz audio with 30ms frames
- Returns speech segments with padding

#### AudioSegmenter
- Segments continuous audio into discrete messages
- Filters by duration (0.5s - 30s)
- Can merge nearby segments

**Technologies**:
- `webrtcvad` - Voice activity detection
- `librosa` - Audio resampling and processing
- `numpy` - Numerical operations

### 4. Speaker Recognition (speaker_recognition.py)

**Purpose**: Identify speakers using voice embeddings

**Key Class**: `SpeakerRecognizer`

**Features**:
- Extracts voice embeddings from audio
- Compares embeddings using cosine similarity
- Threshold-based speaker matching
- Fallback to MFCC features if model unavailable

**Methods**:
- `extract_embedding(audio)` - Get speaker embedding
- `compare_embeddings(emb1, emb2)` - Compute similarity
- `is_same_speaker(emb1, emb2)` - Boolean match
- `serialize/deserialize_embedding()` - DB storage

**Technologies**:
- `torchaudio` - Wav2Vec2 model
- `librosa` - MFCC extraction (fallback)

### 5. Speech Recognition (speech_recognition.py)

**Purpose**: Transcribe speech and detect language

**Key Class**: `SpeechRecognizer`

**Features**:
- Multi-language transcription
- Automatic language detection
- Confidence scoring
- Multiple model sizes (tiny to large)

**Methods**:
- `transcribe(audio)` - Get transcription, language, confidence
- `detect_language(audio)` - Language-only detection

**Technologies**:
- `openai-whisper` - State-of-the-art speech recognition

### 6. Audio Storage (audio_storage.py)

**Purpose**: Manage audio file persistence

**Key Class**: `AudioStorage`

**Features**:
- Organized storage by speaker
- Unique filename generation
- WAV format storage
- File operations (save, load, delete)

**Storage Structure**:
```
audio_storage/
├── speaker_abc123/
│   ├── 20260108_143052_a1b2c3d4.wav
│   └── 20260108_143105_e5f6g7h8.wav
└── speaker_def456/
    └── 20260108_143120_i9j0k1l2.wav
```

### 7. Database Layer (database.py)

**Purpose**: PostgreSQL persistence for metadata

**Models**:

#### Speaker
- `id` - Primary key
- `speaker_id` - Unique identifier (e.g., "speaker_abc123")
- `embedding` - Serialized voice embedding (binary)
- `first_seen` - First appearance timestamp
- `last_seen` - Last appearance timestamp
- Relationship: One-to-many with VoiceMessage

#### VoiceMessage
- `id` - Primary key
- `speaker_id` - Foreign key to Speaker
- `audio_file_path` - Path to audio file
- `duration` - Message duration (seconds)
- `detected_language` - ISO language code
- `transcription` - Speech-to-text result
- `timestamp` - Processing timestamp
- `confidence_score` - Transcription confidence (0-1)

**Technologies**:
- `SQLAlchemy` - ORM
- `PostgreSQL` - Database

## Data Flow

### Audio Upload Flow

```
1. User uploads audio file via web interface
   ↓
2. FastAPI receives file at /api/process-audio
   ↓
3. Audio loaded into numpy array
   ↓
4. VoiceProcessingPipeline.process_audio_stream()
   ↓
5. AudioSegmenter.segment_audio()
   └─→ VoiceActivityDetector detects speech
   └─→ Returns list of audio segments
   ↓
6. For each segment:
   ├─→ SpeakerRecognizer.extract_embedding()
   ├─→ Compare with known speakers in database
   ├─→ Match existing or create new speaker
   ├─→ SpeechRecognizer.transcribe()
   ├─→ AudioStorage.save_audio()
   └─→ Create VoiceMessage record in database
   ↓
7. Return results to user
```

### Real-time Streaming Flow (WebSocket)

```
1. Client connects to ws://localhost:8000/ws/audio
   ↓
2. Client sends audio data (16kHz PCM)
   ↓
3. Server converts bytes to numpy array
   ↓
4. Process through pipeline (same as upload)
   ↓
5. Send results back to client via WebSocket
   ↓
6. Repeat for continuous stream
```

## Configuration

### Environment Variables (.env)

```bash
DATABASE_URL=postgresql://user:pass@host:port/db
AUDIO_STORAGE_PATH=./audio_storage
WHISPER_MODEL=base  # tiny, base, small, medium, large
VAD_AGGRESSIVENESS=3  # 0-3
HOST=0.0.0.0
PORT=8000
```

### Configurable Parameters (config.py)

- `speaker_threshold` - Speaker similarity threshold (0.75 default)
- `whisper_model` - Model size for transcription
- `vad_aggressiveness` - VAD sensitivity level

## Performance Characteristics

### Processing Speed
- **VAD**: Real-time (> 100x)
- **Segmentation**: Real-time (> 50x)
- **Speaker Recognition**: ~5-10x real-time
- **Transcription** (base model): ~1-2x real-time (CPU)
- **Overall**: Depends on Whisper model and hardware

### Resource Usage
- **Memory**: 2-12GB (depends on Whisper model)
- **CPU**: Multi-threaded for audio processing
- **GPU**: Optional (significant speedup for transcription)
- **Storage**: ~10MB per minute of audio

### Scalability Considerations
- Single process handles sequential requests
- For high concurrency, consider:
  - Message queue (Celery, RabbitMQ)
  - Multiple worker processes
  - GPU acceleration
  - Audio compression

## Error Handling

### Graceful Degradation
- If Whisper model fails to load: Returns empty transcription
- If speaker model unavailable: Uses MFCC features
- If database unavailable: HTTP 500 error
- If audio format unsupported: HTTP 500 error

### Logging
- Component errors printed to console
- Database errors trigger rollback
- Failed segments skipped, processing continues

## Security Considerations

1. **Input Validation**
   - File type checking
   - File size limits (implement as needed)
   
2. **Database**
   - SQL injection protection (SQLAlchemy ORM)
   - Parameterized queries

3. **File Storage**
   - Unique filenames prevent collisions
   - Path traversal prevention

4. **API**
   - CORS configuration (add as needed)
   - Rate limiting (implement as needed)
   - Authentication (implement as needed)

## Future Enhancements

1. **Performance**
   - Async processing with task queue
   - GPU acceleration
   - Model optimization
   - Audio compression

2. **Features**
   - Speaker diarization (who spoke when)
   - Emotion detection
   - Noise reduction
   - Multiple audio channel support
   - Real-time dashboard updates

3. **Deployment**
   - Docker container
   - Kubernetes deployment
   - Cloud storage integration (S3, GCS)
   - Monitoring and metrics

4. **Quality**
   - Comprehensive test suite
   - CI/CD pipeline
   - Performance benchmarks
   - Error reporting system

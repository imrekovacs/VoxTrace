# VoxTrace

🎙️ **Real-time Voice Processing & Speaker Identification System**

VoxTrace is a web application that continuously listens to audio channels, detects speech, identifies speakers, detects languages, transcribes speech, and stores all metadata in PostgreSQL.

## Features

- ✅ **Real-time Audio Processing**: Near real-time processing of audio streams
- ✅ **Voice Activity Detection (VAD)**: Automatically detects when speech is present
- ✅ **Speech Segmentation**: Segments continuous audio into discrete voice messages
- ✅ **Speaker Identification**: Identifies whether a speaker is new or known using voice embeddings
- ✅ **Language Detection**: Automatically detects the language being spoken
- ✅ **Speech-to-Text**: Transcribes speech using OpenAI's Whisper model
- ✅ **PostgreSQL Storage**: Stores metadata and transcripts in a relational database
- ✅ **Audio Archive**: Saves original audio recordings organized by speaker
- ✅ **Web Interface**: Modern, responsive web UI for uploading and viewing results
- ✅ **REST API**: Full REST API for integration with other systems
- ✅ **WebSocket Support**: Real-time audio streaming via WebSocket

## Architecture

```
┌─────────────────┐
│  Audio Input    │
│  (Upload/Stream)│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Voice Activity Detection (VAD)   │
│   - WebRTC VAD                      │
│   - Speech/Non-speech detection     │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Audio Segmentation                │
│   - Split into discrete messages    │
│   - Filter by duration              │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Speaker Recognition               │
│   - Extract voice embeddings        │
│   - Compare with known speakers     │
│   - Create new speaker if needed    │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Speech Recognition                │
│   - Detect language (Whisper)       │
│   - Transcribe speech (Whisper)     │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Storage                           │
│   - Save audio file                 │
│   - Store metadata in PostgreSQL    │
└─────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 15+
- Docker & Docker Compose (optional, for database)
- FFmpeg (for audio processing)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/imrekovacs/VoxTrace.git
   cd VoxTrace
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start PostgreSQL**
   
   Using Docker Compose:
   ```bash
   docker-compose up -d
   ```
   
   Or use your existing PostgreSQL instance.

5. **Configure environment**
   
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` to match your configuration:
   ```
   DATABASE_URL=postgresql://voxtrace:voxtrace@localhost:5432/voxtrace
   AUDIO_STORAGE_PATH=./audio_storage
   WHISPER_MODEL=base
   VAD_AGGRESSIVENESS=3
   HOST=0.0.0.0
   PORT=8000
   ```

6. **Run the application**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Access the application**
   
   Open your browser and navigate to: `http://localhost:8000`

## Usage

### Web Interface

1. **Upload Audio Files**
   - Drag and drop audio files (WAV, MP3, FLAC, OGG)
   - Or click the upload area to browse files
   - Click "Upload & Process" to start processing

2. **View Results**
   - See real-time transcriptions as they're processed
   - View speaker IDs, detected languages, and confidence scores
   - Monitor system statistics (total messages, speakers, languages)

### REST API

#### Upload and Process Audio
```bash
curl -X POST "http://localhost:8000/api/process-audio" \
  -F "file=@audio.wav"
```

#### Get Voice Messages
```bash
curl "http://localhost:8000/api/messages?limit=10"
```

#### Get Speakers
```bash
curl "http://localhost:8000/api/speakers"
```

#### Get Statistics
```bash
curl "http://localhost:8000/api/stats"
```

### WebSocket Streaming

Connect to `ws://localhost:8000/ws/audio` for real-time audio streaming:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/audio');

ws.onopen = () => {
  // Send audio data (16kHz, 16-bit PCM)
  const audioData = new Int16Array(/* your audio data */);
  ws.send(audioData.buffer);
};

ws.onmessage = (event) => {
  const result = JSON.parse(event.data);
  console.log('Transcription:', result.results);
};
```

## API Documentation

Once the application is running, visit:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

## Configuration

### Whisper Model Sizes

The `WHISPER_MODEL` setting controls transcription accuracy vs speed:
- `tiny`: Fastest, lowest accuracy (~1GB RAM)
- `base`: Good balance (default, ~1GB RAM)
- `small`: Better accuracy (~2GB RAM)
- `medium`: High accuracy (~5GB RAM)
- `large`: Best accuracy (~10GB RAM)

### VAD Aggressiveness

The `VAD_AGGRESSIVENESS` setting (0-3) controls speech detection sensitivity:
- `0`: Least aggressive (more permissive)
- `1`: Low aggressiveness
- `2`: Medium aggressiveness
- `3`: Most aggressive (default, strictest filtering)

### Speaker Recognition Threshold

Edit `config.py` to adjust `speaker_threshold` (0.0-1.0):
- Lower values: More likely to match existing speakers
- Higher values: More likely to create new speaker profiles
- Default: `0.75`

## Database Schema

### Speakers Table
- `id`: Primary key
- `speaker_id`: Unique speaker identifier
- `embedding`: Voice embedding (binary)
- `first_seen`: First appearance timestamp
- `last_seen`: Last appearance timestamp

### Voice Messages Table
- `id`: Primary key
- `speaker_id`: Foreign key to speakers
- `audio_file_path`: Path to stored audio file
- `duration`: Message duration in seconds
- `detected_language`: ISO language code
- `transcription`: Speech-to-text result
- `timestamp`: Processing timestamp
- `confidence_score`: Transcription confidence

## Performance Considerations

- **Processing Speed**: Depends on Whisper model size and hardware
  - Base model: ~1-2x real-time on CPU
  - Use GPU for faster processing (CUDA support)
- **Storage**: Audio files are stored as WAV (uncompressed)
  - ~10MB per minute of audio
  - Consider implementing compression for production
- **Memory**: Depends on model size and concurrent processing
  - Base configuration: ~2-4GB RAM
  - Large model: ~10-12GB RAM

## Troubleshooting

### Database Connection Error
```
Make sure PostgreSQL is running:
docker-compose up -d
```

### Model Download Issues
```
Whisper models are downloaded automatically on first use.
Ensure you have internet connectivity and sufficient disk space.
```

### Audio Format Issues
```
Install FFmpeg:
- Ubuntu: sudo apt-get install ffmpeg
- macOS: brew install ffmpeg
- Windows: Download from ffmpeg.org
```

## Development

### Project Structure
```
VoxTrace/
├── main.py                    # FastAPI application & web interface
├── config.py                  # Configuration settings
├── database.py                # Database models & session management
├── processing_pipeline.py     # Main processing pipeline
├── audio_processing.py        # VAD & segmentation
├── speaker_recognition.py     # Speaker identification
├── speech_recognition.py      # Transcription & language detection
├── audio_storage.py           # Audio file management
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # PostgreSQL setup
└── README.md                  # This file
```

### Running Tests

(Tests to be added in future versions)

```bash
pytest
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [WebRTC VAD](https://github.com/wiseman/py-webrtcvad) for voice activity detection
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [PyTorch](https://pytorch.org/) for deep learning capabilities
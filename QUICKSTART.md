# Quick Start Guide

Get VoxTrace up and running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Docker (for PostgreSQL)
- FFmpeg (for audio processing)

## Step-by-Step Setup

### 1. Clone the Repository (Skip if already cloned)

```bash
git clone https://github.com/imrekovacs/VoxTrace.git
cd VoxTrace
```

### 2. Run the Startup Script

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```batch
start.bat
```

This script will:
- Create a virtual environment
- Install all dependencies
- Start PostgreSQL in Docker
- Create configuration files
- Launch the application

### 3. Access the Application

Open your web browser and go to:
```
http://localhost:8000
```

You should see the VoxTrace web interface!

## Manual Setup (Alternative)

If you prefer manual setup:

### 1. Create Virtual Environment

```bash
python -m venv venv

# Activate it:
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL

```bash
docker-compose up -d
```

Wait a few seconds for PostgreSQL to start.

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` if needed (default values work fine).

### 5. Run the Application

```bash
python main.py
```

## First Test

### Upload Audio via Web Interface

1. Go to `http://localhost:8000`
2. Drag and drop an audio file (or click to browse)
3. Click "Upload & Process"
4. Watch the transcription appear!

### Test via API

```bash
# Upload an audio file
curl -X POST "http://localhost:8000/api/process-audio" \
  -F "file=@your_audio.wav"

# Get statistics
curl http://localhost:8000/api/stats

# Get messages
curl http://localhost:8000/api/messages
```

### Test via Python Script

```bash
python example_api_usage.py
```

## What Happens During First Run

1. **Model Downloads**: On first run, Whisper will download the model
   - Tiny: ~75 MB
   - Base: ~140 MB (default)
   - Small: ~460 MB
   - Medium: ~1.5 GB
   - Large: ~2.9 GB

2. **Database Initialization**: Tables are created automatically

3. **Directory Creation**: `audio_storage/` folder is created

This takes a few minutes the first time. Subsequent runs are instant!

## Troubleshooting Quick Fixes

### Port 8000 Already in Use

Change the port in `.env`:
```
PORT=8080
```

### PostgreSQL Won't Start

```bash
# Check if Docker is running
docker ps

# Restart PostgreSQL
docker-compose restart
```

### Dependencies Won't Install

```bash
# Update pip first
pip install --upgrade pip

# Install PyTorch separately (if needed)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Then install other requirements
pip install -r requirements.txt
```

### Out of Memory

Use a smaller Whisper model in `.env`:
```
WHISPER_MODEL=tiny
```

## Next Steps

### Explore the Web Interface
- Upload different audio files
- Try different languages
- Watch speaker identification in action
- Monitor system statistics

### Try the API
- Read `example_api_usage.py`
- Test WebSocket streaming
- Build your own client

### Read the Documentation
- `README.md` - Full user guide
- `ARCHITECTURE.md` - Technical details
- `TROUBLESHOOTING.md` - Common issues
- `IMPLEMENTATION_SUMMARY.md` - What was built

### Customize
- Adjust VAD sensitivity in `.env`
- Change Whisper model size
- Modify speaker threshold in `config.py`
- Add your own features!

## Stopping the Application

Press `Ctrl+C` in the terminal to stop the server.

To stop PostgreSQL:
```bash
docker-compose down
```

To stop and remove all data:
```bash
docker-compose down -v
```

## Performance Tips

### For Faster Processing
1. Use GPU instead of CPU
2. Use smaller Whisper model (tiny or base)
3. Process shorter audio clips
4. Reduce audio quality to 16kHz mono

### For Better Quality
1. Use larger Whisper model (medium or large)
2. Ensure high-quality audio input
3. Minimize background noise

## System Requirements

### Minimum
- 4 GB RAM
- 10 GB disk space
- 2 CPU cores

### Recommended
- 8 GB RAM
- 50 GB disk space
- 4 CPU cores
- NVIDIA GPU (optional, for speed)

## Validation

Run the validation script to check installation:

```bash
python validate.py
```

This verifies:
- All modules can be imported
- Configuration is valid
- Components are structured correctly

## Getting Help

- Check `TROUBLESHOOTING.md` for common issues
- Run `python validate.py` to diagnose problems
- Check application logs for errors
- Review PostgreSQL logs: `docker-compose logs postgres`

## Default Configuration

| Setting | Default Value |
|---------|---------------|
| Database | `postgresql://voxtrace:voxtrace@localhost:5432/voxtrace` |
| Audio Storage | `./audio_storage` |
| Whisper Model | `base` |
| VAD Aggressiveness | `3` (most aggressive) |
| Server Host | `0.0.0.0` |
| Server Port | `8000` |
| Speaker Threshold | `0.75` |

## File Structure After Setup

```
VoxTrace/
├── venv/                   # Virtual environment
├── audio_storage/          # Stored audio files
│   └── speaker_xxxxx/      # Organized by speaker
├── .env                    # Your configuration
├── main.py                 # Run this to start
└── ... (other files)
```

## Success Checklist

- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] PostgreSQL running (check with `docker ps`)
- [ ] `.env` file created
- [ ] Application starts without errors
- [ ] Can access `http://localhost:8000`
- [ ] Can upload and process audio
- [ ] Transcriptions appear
- [ ] Stats update

If all checked, you're ready to go! 🎉

## What's Next?

1. **Upload test audio**: Try different speakers and languages
2. **Explore the API**: Build your own integrations
3. **Customize**: Adjust settings for your use case
4. **Scale**: Add GPU, async processing, or cloud storage
5. **Extend**: Add new features like sentiment analysis

---

**Need more help?** Check the full documentation in `README.md` or `TROUBLESHOOTING.md`.

**Ready to dive deep?** Read `ARCHITECTURE.md` to understand how it all works.

**Want to contribute?** The code is modular and well-documented. Start hacking!

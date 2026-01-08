# Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### 1. PyTorch Installation Failed

**Problem**: `pip install -r requirements.txt` fails with PyTorch errors

**Solution**:
```bash
# Install PyTorch first (CPU version)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Then install other requirements
pip install -r requirements.txt
```

For GPU support:
```bash
# CUDA 11.8
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### 2. psycopg2 Installation Failed

**Problem**: `ERROR: Failed building wheel for psycopg2`

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install libpq-dev python3-dev

# macOS
brew install postgresql

# Then retry
pip install psycopg2-binary
```

#### 3. soundfile/librosa Issues

**Problem**: `OSError: cannot load library 'libsndfile.so'`

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install libsndfile1

# macOS
brew install libsndfile

# Windows
# Download from: http://www.mega-nerd.com/libsndfile/
```

#### 4. FFmpeg Not Found

**Problem**: `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'`

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from: https://ffmpeg.org/download.html
# Add to PATH
```

### Database Issues

#### 1. PostgreSQL Connection Failed

**Problem**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution**:
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# If not running, start it
docker-compose up -d

# Check logs
docker-compose logs postgres

# Verify connection
psql -h localhost -U voxtrace -d voxtrace
```

#### 2. Database Does Not Exist

**Problem**: `FATAL: database "voxtrace" does not exist`

**Solution**:
```bash
# Connect to PostgreSQL
docker exec -it $(docker ps -qf "name=postgres") psql -U voxtrace

# Create database
CREATE DATABASE voxtrace;

# Exit
\q
```

#### 3. Permission Denied

**Problem**: `FATAL: role "voxtrace" does not exist`

**Solution**:
```bash
# Connect as postgres user
docker exec -it $(docker ps -qf "name=postgres") psql -U postgres

# Create user
CREATE USER voxtrace WITH PASSWORD 'voxtrace';
GRANT ALL PRIVILEGES ON DATABASE voxtrace TO voxtrace;

# Exit
\q
```

### Runtime Issues

#### 1. Out of Memory

**Problem**: `RuntimeError: CUDA out of memory` or system freezes

**Solution**:
- Use smaller Whisper model in `.env`:
  ```
  WHISPER_MODEL=tiny  # or base instead of large
  ```
- Process fewer/shorter audio files at once
- Add swap space (Linux):
  ```bash
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  ```

#### 2. Whisper Model Download Fails

**Problem**: `ConnectionError: Failed to download model`

**Solution**:
```bash
# Manually download model
python -c "import whisper; whisper.load_model('base')"

# Or specify cache directory
export WHISPER_CACHE_DIR=/path/to/cache
python main.py
```

#### 3. Port Already in Use

**Problem**: `OSError: [Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows

# Or use different port in .env
PORT=8080
```

#### 4. Audio Upload Fails

**Problem**: `HTTP 500: Error processing audio`

**Solution**:
- Check audio file format (should be WAV, MP3, FLAC, or OGG)
- Verify file is not corrupted
- Check logs for specific error
- Try converting to WAV:
  ```bash
  ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
  ```

#### 5. No Transcription Returned

**Problem**: Transcription is empty or "No transcription available"

**Possible causes**:
1. **Audio is silent**: VAD detected no speech
   - Solution: Check audio file plays correctly
   
2. **Whisper model not loaded**: Check console for errors
   - Solution: Restart application, check model downloads
   
3. **Audio too short**: Segment filtered out
   - Solution: Adjust `min_segment_duration` in `audio_processing.py`
   
4. **Language detection failed**: Some languages not well supported
   - Solution: Specify language in Whisper config

### Performance Issues

#### 1. Slow Processing

**Problem**: Audio takes very long to process

**Solutions**:
- Use smaller Whisper model (tiny or base)
- Enable GPU acceleration:
  ```bash
  pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
  ```
- Reduce audio quality:
  ```bash
  ffmpeg -i input.wav -ar 16000 -ac 1 output.wav
  ```
- Process shorter segments

#### 2. High CPU Usage

**Problem**: CPU usage at 100%

**Solution**:
- This is normal during transcription
- Use GPU instead of CPU
- Limit concurrent processing
- Use async task queue for production

#### 3. High Memory Usage

**Problem**: Memory usage keeps increasing

**Solution**:
- Restart application periodically
- Use smaller Whisper model
- Implement memory profiling:
  ```python
  pip install memory_profiler
  python -m memory_profiler main.py
  ```

### Web Interface Issues

#### 1. Blank Page

**Problem**: Opening localhost:8000 shows blank page

**Solution**:
- Check browser console for JavaScript errors
- Verify application is running: `curl http://localhost:8000`
- Try different browser
- Clear browser cache

#### 2. Upload Button Not Working

**Problem**: Click upload does nothing

**Solution**:
- Check browser console for errors
- Verify files are selected
- Check file size is reasonable (< 100MB)
- Check server logs for errors

#### 3. Stats Not Updating

**Problem**: Statistics don't change

**Solution**:
- Check database connection
- Verify data is being written: Query database directly
- Check browser network tab for API errors
- Refresh page

### Docker Issues

#### 1. Docker Compose Fails

**Problem**: `docker-compose up -d` fails

**Solution**:
```bash
# Update Docker Compose
pip install --upgrade docker-compose

# Or use Docker's built-in compose
docker compose up -d

# Check for port conflicts
docker ps
```

#### 2. Container Won't Start

**Problem**: PostgreSQL container exits immediately

**Solution**:
```bash
# Check logs
docker-compose logs postgres

# Remove old volumes
docker-compose down -v

# Start fresh
docker-compose up -d
```

### Debugging Tips

#### Enable Debug Mode

Add to `.env`:
```
DEBUG=True
LOG_LEVEL=DEBUG
```

#### Check Logs

```bash
# Application logs
python main.py 2>&1 | tee app.log

# Database logs
docker-compose logs -f postgres

# System logs
journalctl -f  # Linux
```

#### Test Components Independently

```bash
# Test database connection
python -c "from database import init_db; init_db(); print('OK')"

# Test Whisper
python -c "import whisper; m=whisper.load_model('base'); print('OK')"

# Test VAD
python test_basic.py

# Test API
curl http://localhost:8000/api/stats
```

#### Verify Dependencies

```bash
# List installed packages
pip list

# Check for conflicts
pip check

# Verify versions
python -c "import torch; print(torch.__version__)"
```

## Getting Help

If you still have issues:

1. **Check the logs**: Most errors are logged with details
2. **Search existing issues**: GitHub issues may have solutions
3. **Create an issue**: Provide:
   - Operating system and version
   - Python version
   - Error messages (full traceback)
   - Steps to reproduce
   - Configuration (without sensitive data)

## Known Limitations

1. **Speaker recognition accuracy**: Depends on audio quality and speaker variability
2. **Language support**: Whisper supports 99 languages, but accuracy varies
3. **Real-time performance**: Depends heavily on hardware
4. **Concurrent processing**: Single-threaded, sequential processing
5. **File size limits**: Large files may cause memory issues
6. **Audio formats**: Some formats may not be supported without FFmpeg

## System Requirements

### Minimum
- Python 3.8+
- 4GB RAM
- 10GB disk space
- PostgreSQL 12+

### Recommended
- Python 3.10+
- 8GB RAM (16GB for large model)
- 50GB disk space
- PostgreSQL 15+
- NVIDIA GPU with CUDA (for faster processing)

### Tested Platforms
- ✅ Ubuntu 20.04/22.04
- ✅ macOS 12+
- ✅ Windows 10/11
- ✅ Docker on Linux

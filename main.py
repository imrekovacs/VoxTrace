from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import numpy as np
import soundfile as sf
import io
from typing import List, Optional
from datetime import datetime
import json
import logging
from pydantic import BaseModel, field_validator
import os
from pathlib import Path

from database import init_db, get_db, Speaker, VoiceMessage
from processing_pipeline import VoiceProcessingPipeline
from config import settings

# Configure logging
logger = logging.getLogger(__name__)


class UpdateNotesRequest(BaseModel):
    notes: str = ""
    
    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v: str) -> str:
        if len(v) > 10000:  # Limit notes to 10,000 characters
            raise ValueError('Notes must be 10,000 characters or less')
        return v

# Initialize FastAPI app
app = FastAPI(
    title="VoxTrace",
    description="Real-time audio processing and speaker identification system",
    version="1.0.0"
)

# Initialize database
init_db()

# Initialize processing pipeline
pipeline = VoiceProcessingPipeline()


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve main web interface"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>VoxTrace - Voice Processing System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .content {
            padding: 30px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover {
            background: #f0f0f0;
            border-color: #764ba2;
        }
        .upload-area input {
            display: none;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .status {
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
        }
        .status.info {
            background: #e3f2fd;
            color: #1976d2;
        }
        .status.success {
            background: #e8f5e9;
            color: #388e3c;
        }
        .status.error {
            background: #ffebee;
            color: #c62828;
        }
        .transcriptions {
            max-height: 500px;
            overflow-y: auto;
        }
        .transcription-item {
            background: #f5f5f5;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .transcription-item .meta {
            display: flex;
            gap: 20px;
            margin-bottom: 10px;
            font-size: 0.9em;
            color: #666;
        }
        .transcription-item .meta span {
            background: white;
            padding: 5px 10px;
            border-radius: 3px;
        }
        .transcription-item .text {
            font-size: 1.1em;
            color: #333;
            line-height: 1.6;
            margin-bottom: 10px;
        }
        .notes-section {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
        }
        .notes-input {
            width: 100%;
            min-height: 60px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-family: inherit;
            font-size: 0.95em;
            resize: vertical;
            margin-bottom: 8px;
        }
        .notes-input:focus {
            outline: none;
            border-color: #667eea;
        }
        .save-notes-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 6px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.2s;
        }
        .save-notes-btn:hover {
            background: #764ba2;
        }
        .save-notes-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        }
        .audio-controls {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 15px;
            padding: 10px;
            background: white;
            border-radius: 5px;
        }
        .audio-controls audio {
            display: none;
        }
        .control-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .control-btn:hover {
            background: #764ba2;
        }
        .control-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .time-display {
            font-size: 0.9em;
            color: #666;
            min-width: 100px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-card .number {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-card .label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .file-list {
            background: #f5f5f5;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }
        .file-list-header {
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1em;
        }
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: white;
            border-radius: 5px;
            margin-bottom: 8px;
            border-left: 3px solid #667eea;
        }
        .file-item:last-child {
            margin-bottom: 0;
        }
        .file-info {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 3px;
        }
        .file-name {
            font-weight: 500;
            color: #333;
        }
        .file-size {
            font-size: 0.85em;
            color: #666;
        }
        .remove-file-btn {
            background: #ff5252;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
            transition: background 0.2s;
        }
        .remove-file-btn:hover {
            background: #ff1744;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎙️ VoxTrace</h1>
            <p>Real-time Voice Processing & Speaker Identification</p>
        </div>
        
        <div class="content">
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="number" id="totalMessages">0</div>
                    <div class="label">Voice Messages</div>
                </div>
                <div class="stat-card">
                    <div class="number" id="totalSpeakers">0</div>
                    <div class="label">Unique Speakers</div>
                </div>
                <div class="stat-card">
                    <div class="number" id="totalLanguages">0</div>
                    <div class="label">Languages Detected</div>
                </div>
            </div>
            
            <div class="section">
                <h2>📤 Upload Audio</h2>
                <div class="upload-area" id="uploadArea">
                    <input type="file" id="fileInput" accept="audio/*" multiple>
                    <div>
                        <p style="font-size: 1.2em; margin-bottom: 10px;">📁 Drop audio files here or click to browse</p>
                        <p style="color: #666;">Supported formats: WAV, MP3, FLAC, OGG</p>
                    </div>
                </div>
                <div id="fileList" style="margin-top: 15px;"></div>
                <div class="controls">
                    <button class="btn" id="uploadBtn">Upload & Process</button>
                </div>
                <div id="uploadStatus"></div>
            </div>
            
            <div class="section">
                <h2>📝 Recent Transcriptions</h2>
                <div class="transcriptions" id="transcriptions">
                    <p style="color: #666; text-align: center; padding: 40px;">No transcriptions yet. Upload audio to get started.</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        const uploadStatus = document.getElementById('uploadStatus');
        const transcriptions = document.getElementById('transcriptions');
        const fileListContainer = document.getElementById('fileList');
        
        // Store selected files
        let selectedFiles = [];
        
        // Format file size
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }
        
        // Display selected files
        function displayFileList() {
            if (selectedFiles.length === 0) {
                fileListContainer.innerHTML = '';
                return;
            }
            
            let html = '<div class="file-list">';
            html += `<div class="file-list-header">📋 Selected Files (${selectedFiles.length})</div>`;
            
            selectedFiles.forEach((file, index) => {
                html += `
                    <div class="file-item" data-index="${index}">
                        <div class="file-info">
                            <div class="file-name">🎵 ${escapeHtml(file.name)}</div>
                            <div class="file-size">${formatFileSize(file.size)}</div>
                        </div>
                        <button class="remove-file-btn" onclick="removeFile(${index})">✕ Remove</button>
                    </div>
                `;
            });
            
            html += '</div>';
            fileListContainer.innerHTML = html;
        }
        
        // Remove a file from the list
        window.removeFile = function(index) {
            selectedFiles.splice(index, 1);
            displayFileList();
            
            // Update file input
            const dt = new DataTransfer();
            selectedFiles.forEach(file => dt.items.add(file));
            fileInput.files = dt.files;
        };
        
        // Handle file selection
        function handleFileSelection(files) {
            if (!files || files.length === 0) return;
            
            // Convert FileList to Array and add to selectedFiles
            const newFiles = Array.from(files);
            selectedFiles = [...selectedFiles, ...newFiles];
            
            // Remove duplicates based on name and size
            const uniqueFiles = [];
            const seen = new Set();
            
            selectedFiles.forEach(file => {
                const key = `${file.name}-${file.size}`;
                if (!seen.has(key)) {
                    seen.add(key);
                    uniqueFiles.push(file);
                }
            });
            
            selectedFiles = uniqueFiles;
            displayFileList();
            showStatus(`${selectedFiles.length} file(s) selected`, 'info');
        }
        
        // Format timestamp in Swiss format (dd.MM.yyyy HH:mm:ss)
        function formatSwissDateTime(isoString) {
            const date = new Date(isoString);
            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const year = date.getFullYear();
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const seconds = String(date.getSeconds()).padStart(2, '0');
            return `${day}.${month}.${year} ${hours}:${minutes}:${seconds}`;
        }
        
        // Escape HTML to prevent XSS
        function escapeHtml(unsafe) {
            if (!unsafe) return '';
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }
        
        // Save notes for a message
        async function saveNotes(messageId, notes, button) {
            button.disabled = true;
            button.textContent = 'Saving...';
            
            try {
                const response = await fetch(`/api/messages/${messageId}/notes`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ notes: notes })
                });
                
                if (response.ok) {
                    button.textContent = 'Saved ✓';
                    setTimeout(() => {
                        button.textContent = 'Save Notes';
                        button.disabled = false;
                    }, 2000);
                } else {
                    button.textContent = 'Error';
                    setTimeout(() => {
                        button.textContent = 'Save Notes';
                        button.disabled = false;
                    }, 2000);
                }
            } catch (error) {
                console.error('Error saving notes:', error);
                button.textContent = 'Error';
                setTimeout(() => {
                    button.textContent = 'Save Notes';
                    button.disabled = false;
                }, 2000);
            }
        }
        
        // Click to browse
        uploadArea.addEventListener('click', () => fileInput.click());
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            handleFileSelection(e.target.files);
        });
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.background = '#f0f0f0';
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.background = '';
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.background = '';
            handleFileSelection(e.dataTransfer.files);
        });
        
        // Upload button
        uploadBtn.addEventListener('click', async () => {
            if (selectedFiles.length === 0) {
                showStatus('Please select audio files first', 'error');
                return;
            }
            
            uploadBtn.disabled = true;
            showStatus(`Processing ${selectedFiles.length} file(s)...`, 'info');
            
            let successCount = 0;
            let errorCount = 0;
            
            for (let i = 0; i < selectedFiles.length; i++) {
                const file = selectedFiles[i];
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    showStatus(`Processing ${i + 1}/${selectedFiles.length}: ${file.name}...`, 'info');
                    
                    const response = await fetch('/api/process-audio', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        successCount++;
                        if (data.results && data.results.length > 0) {
                            showStatus(`✅ Processed ${i + 1}/${selectedFiles.length}: ${file.name} (${data.results.length} segment(s) found)`, 'success');
                            addTranscriptions(data.results);
                        } else {
                            showStatus(`⚠️ Processed ${i + 1}/${selectedFiles.length}: ${file.name} (no speech segments detected)`, 'info');
                        }
                    } else {
                        errorCount++;
                        showStatus(`❌ Error processing ${file.name}: ${data.detail}`, 'error');
                    }
                } catch (error) {
                    errorCount++;
                    showStatus(`❌ Error processing ${file.name}: ${error.message}`, 'error');
                }
            }
            
            // Final summary
            if (errorCount === 0) {
                showStatus(`✅ Successfully processed all ${successCount} file(s)`, 'success');
            } else if (successCount > 0) {
                showStatus(`⚠️ Processed ${successCount} file(s), ${errorCount} failed`, 'info');
            } else {
                showStatus(`❌ All ${errorCount} file(s) failed to process`, 'error');
            }
            
            uploadBtn.disabled = false;
            selectedFiles = [];
            fileInput.value = '';
            displayFileList();
            loadStats();
        });
        
        function showStatus(message, type) {
            uploadStatus.innerHTML = `<div class="status ${type}">${message}</div>`;
        }
        
        function addTranscriptions(results) {
            if (!results || results.length === 0) {
                return;
            }
            
            results.forEach(result => {
                const item = document.createElement('div');
                item.className = 'transcription-item';
                const messageId = result.id || result.message_id;
                item.innerHTML = `
                    <div class="meta">
                        <span>🎤 ${escapeHtml(result.speaker_id)}</span>
                        <span>🌐 ${escapeHtml(result.language)}</span>
                        <span>⏱️ ${result.duration.toFixed(2)}s</span>
                        <span>📊 ${(result.confidence * 100).toFixed(1)}%</span>
                        <span>🕒 ${formatSwissDateTime(result.timestamp)}</span>
                        ${result.is_new_speaker ? '<span style="background: #4caf50; color: white;">🆕 New Speaker</span>' : ''}
                    </div>
                    <div class="text">${escapeHtml(result.transcription) || 'No transcription available'}</div>
                    <div class="notes-section">
                        <textarea class="notes-input" id="notes-${result.id}" placeholder="Add notes...">${escapeHtml(result.notes || '')}</textarea>
                        <button class="save-notes-btn" data-message-id="${result.id}">Save Notes</button>
                    </div>
                    <div class="audio-controls">
                        <audio src="/api/audio/${messageId}" preload="metadata"></audio>
                        <button class="control-btn play-btn" data-message-id="${messageId}">
                            ▶️ Play
                        </button>
                        <button class="control-btn pause-btn" data-message-id="${messageId}" style="display: none;">
                            ⏸️ Pause
                        </button>
                        <button class="control-btn stop-btn" data-message-id="${messageId}" disabled>
                            ⏹️ Stop
                        </button>
                        <span class="time-display">0:00 / ${formatTime(result.duration)}</span>
                    </div>
                `;
                
                // Attach event listener to save button
                const saveBtn = item.querySelector('.save-notes-btn');
                const textarea = item.querySelector(`#notes-${result.id}`);
                saveBtn.addEventListener('click', function() {
                    saveNotes(result.id, textarea.value, this);
                });
                
                transcriptions.insertBefore(item, transcriptions.firstChild);
                setupAudioControls(item);
            });
            
            // Remove placeholder
            const placeholder = transcriptions.querySelector('p');
            if (placeholder) placeholder.remove();
        }
        
        function formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }
        
        function setupAudioControls(item) {
            const audio = item.querySelector('audio');
            const playBtn = item.querySelector('.play-btn');
            const pauseBtn = item.querySelector('.pause-btn');
            const stopBtn = item.querySelector('.stop-btn');
            const timeDisplay = item.querySelector('.time-display');
            
            playBtn.addEventListener('click', () => {
                audio.play().catch(error => {
                    console.error('Error playing audio:', error);
                    alert('Failed to play audio. The file may be unavailable.');
                    playBtn.style.display = 'flex';
                    pauseBtn.style.display = 'none';
                    stopBtn.disabled = true;
                });
                playBtn.style.display = 'none';
                pauseBtn.style.display = 'flex';
                stopBtn.disabled = false;
            });
            
            pauseBtn.addEventListener('click', () => {
                audio.pause();
                pauseBtn.style.display = 'none';
                playBtn.style.display = 'flex';
            });
            
            stopBtn.addEventListener('click', () => {
                audio.pause();
                audio.currentTime = 0;
                pauseBtn.style.display = 'none';
                playBtn.style.display = 'flex';
                stopBtn.disabled = true;
            });
            
            audio.addEventListener('timeupdate', () => {
                const current = formatTime(audio.currentTime);
                const total = formatTime(audio.duration || 0);
                timeDisplay.textContent = `${current} / ${total}`;
            });
            
            audio.addEventListener('ended', () => {
                pauseBtn.style.display = 'none';
                playBtn.style.display = 'flex';
                stopBtn.disabled = true;
                audio.currentTime = 0;
            });
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                document.getElementById('totalMessages').textContent = stats.total_messages;
                document.getElementById('totalSpeakers').textContent = stats.total_speakers;
                document.getElementById('totalLanguages').textContent = stats.unique_languages;
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        async function loadRecent() {
            try {
                const response = await fetch('/api/messages?limit=20');
                const data = await response.json();
                
                if (data.messages && data.messages.length > 0) {
                    transcriptions.innerHTML = '';
                    data.messages.forEach(msg => {
                        const item = document.createElement('div');
                        item.className = 'transcription-item';
                        item.innerHTML = `
                            <div class="meta">
                                <span>🎤 ${escapeHtml(msg.speaker_id)}</span>
                                <span>🌐 ${escapeHtml(msg.language)}</span>
                                <span>⏱️ ${msg.duration.toFixed(2)}s</span>
                                <span>📊 ${(msg.confidence * 100).toFixed(1)}%</span>
                                <span>🕒 ${formatSwissDateTime(msg.timestamp)}</span>
                            </div>
                            <div class="text">${escapeHtml(msg.transcription) || 'No transcription available'}</div>
                            <div class="notes-section">
                                <textarea class="notes-input" id="notes-${msg.id}" placeholder="Add notes...">${escapeHtml(msg.notes || '')}</textarea>
                                <button class="save-notes-btn" data-message-id="${msg.id}">Save Notes</button>
                            </div>
                            <div class="audio-controls">
                                <audio src="/api/audio/${msg.id}" preload="metadata"></audio>
                                <button class="control-btn play-btn" data-message-id="${msg.id}">
                                    ▶️ Play
                                </button>
                                <button class="control-btn pause-btn" data-message-id="${msg.id}" style="display: none;">
                                    ⏸️ Pause
                                </button>
                                <button class="control-btn stop-btn" data-message-id="${msg.id}" disabled>
                                    ⏹️ Stop
                                </button>
                                <span class="time-display">0:00 / ${formatTime(msg.duration)}</span>
                            </div>
                        `;
                        
                        // Attach event listener to save button
                        const saveBtn = item.querySelector('.save-notes-btn');
                        const textarea = item.querySelector(`#notes-${msg.id}`);
                        saveBtn.addEventListener('click', function() {
                            saveNotes(msg.id, textarea.value, this);
                        });
                        
                        transcriptions.appendChild(item);
                        setupAudioControls(item);
                    });
                }
            } catch (error) {
                console.error('Error loading recent messages:', error);
            }
        }
        
        // Load initial data
        loadStats();
        loadRecent();
        
        // Refresh stats every 10 seconds
        setInterval(loadStats, 10000);
    </script>
</body>
</html>
    """


@app.post("/api/process-audio")
async def process_audio(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Process uploaded audio file
    """
    try:
        # Read audio file
        audio_data = await file.read()
        
        # Load audio with soundfile
        audio, sample_rate = sf.read(io.BytesIO(audio_data))
        
        # Ensure mono
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        # Process audio
        results = pipeline.process_audio_stream(audio, sample_rate, db)
        
        return {
            "status": "success",
            "filename": file.filename,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/messages")
async def get_messages(
    limit: int = 50,
    offset: int = 0,
    speaker_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get voice messages with optional filtering
    """
    query = db.query(VoiceMessage).join(Speaker)
    
    if speaker_id:
        query = query.filter(Speaker.speaker_id == speaker_id)
    
    messages = query.order_by(VoiceMessage.timestamp.desc()).offset(offset).limit(limit).all()
    
    return {
        "messages": [
            {
                "id": msg.id,
                "speaker_id": msg.speaker.speaker_id,
                "language": msg.detected_language,
                "transcription": msg.transcription,
                "duration": msg.duration,
                "confidence": msg.confidence_score,
                "timestamp": msg.timestamp.isoformat(),
                "notes": msg.notes
            }
            for msg in messages
        ]
    }


@app.put("/api/messages/{message_id}/notes")
async def update_message_notes(
    message_id: int,
    request: UpdateNotesRequest,
    db: Session = Depends(get_db)
):
    """
    Update notes for a specific voice message
    """
    message = db.query(VoiceMessage).filter(VoiceMessage.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    try:
        message.notes = request.notes
        db.commit()
        db.refresh(message)
        
        return {
            "status": "success",
            "message_id": message_id,
            "notes": message.notes
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update notes for message {message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notes")


@app.get("/api/speakers")
async def get_speakers(db: Session = Depends(get_db)):
    """
    Get all speakers
    """
    speakers = db.query(Speaker).all()
    
    return {
        "speakers": [
            {
                "id": speaker.id,
                "speaker_id": speaker.speaker_id,
                "first_seen": speaker.first_seen.isoformat(),
                "last_seen": speaker.last_seen.isoformat(),
                "message_count": len(speaker.voice_messages)
            }
            for speaker in speakers
        ]
    }


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get system statistics
    """
    total_messages = db.query(VoiceMessage).count()
    total_speakers = db.query(Speaker).count()
    
    # Get unique languages
    languages = db.query(VoiceMessage.detected_language).distinct().all()
    unique_languages = len([lang[0] for lang in languages if lang[0]])
    
    return {
        "total_messages": total_messages,
        "total_speakers": total_speakers,
        "unique_languages": unique_languages
    }


@app.get("/api/audio/{message_id}")
async def get_audio(message_id: int, db: Session = Depends(get_db)):
    """
    Serve audio file for a specific message
    """
    message = db.query(VoiceMessage).filter(VoiceMessage.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    audio_path = Path(message.audio_file_path)
    
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=str(audio_path),
        media_type="audio/wav",
        filename=f"message_{message_id}.wav"
    )


@app.websocket("/ws/audio")
async def websocket_audio(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time audio streaming
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive audio data
            data = await websocket.receive_bytes()
            
            # Expected format: JSON header + audio data
            # For simplicity, assume raw audio data at 16kHz, 16-bit PCM
            audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            sample_rate = 16000
            
            # Process audio
            results = pipeline.process_audio_stream(audio, sample_rate, db)
            
            # Send results back
            if results:
                await websocket.send_json({
                    "type": "results",
                    "results": results
                })
    
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)

"""
Example script demonstrating how to use VoxTrace API
"""

import requests
import time
from pathlib import Path

# API endpoint
BASE_URL = "http://localhost:8000"


def upload_audio(file_path: str):
    """Upload and process audio file"""
    print(f"\n📤 Uploading {file_path}...")
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/api/process-audio", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Processed {data['count']} voice message(s)")
        
        for result in data['results']:
            print(f"\n  Speaker: {result['speaker_id']}")
            print(f"  Language: {result['language']}")
            print(f"  Duration: {result['duration']:.2f}s")
            print(f"  Transcription: {result['transcription']}")
            if result['is_new_speaker']:
                print(f"  🆕 New speaker detected!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def get_stats():
    """Get system statistics"""
    print("\n📊 Getting statistics...")
    response = requests.get(f"{BASE_URL}/api/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"  Total messages: {stats['total_messages']}")
        print(f"  Total speakers: {stats['total_speakers']}")
        print(f"  Unique languages: {stats['unique_languages']}")
    else:
        print(f"❌ Error: {response.status_code}")


def get_messages(limit=10):
    """Get recent voice messages"""
    print(f"\n📝 Getting {limit} most recent messages...")
    response = requests.get(f"{BASE_URL}/api/messages?limit={limit}")
    
    if response.status_code == 200:
        data = response.json()
        messages = data['messages']
        
        if not messages:
            print("  No messages found")
            return
        
        for msg in messages:
            print(f"\n  ID: {msg['id']}")
            print(f"  Speaker: {msg['speaker_id']}")
            print(f"  Language: {msg['language']}")
            print(f"  Duration: {msg['duration']:.2f}s")
            print(f"  Transcription: {msg['transcription'][:100]}...")
    else:
        print(f"❌ Error: {response.status_code}")


def get_speakers():
    """Get all speakers"""
    print("\n👥 Getting speakers...")
    response = requests.get(f"{BASE_URL}/api/speakers")
    
    if response.status_code == 200:
        data = response.json()
        speakers = data['speakers']
        
        if not speakers:
            print("  No speakers found")
            return
        
        for speaker in speakers:
            print(f"\n  ID: {speaker['speaker_id']}")
            print(f"  First seen: {speaker['first_seen']}")
            print(f"  Last seen: {speaker['last_seen']}")
            print(f"  Messages: {speaker['message_count']}")
    else:
        print(f"❌ Error: {response.status_code}")


if __name__ == "__main__":
    print("🎙️  VoxTrace API Example")
    print("=" * 50)
    
    # Example 1: Upload audio file (you need to provide a path)
    # Uncomment and provide a valid audio file path:
    # upload_audio("path/to/your/audio.wav")
    
    # Example 2: Get statistics
    get_stats()
    
    # Example 3: Get recent messages
    get_messages(limit=5)
    
    # Example 4: Get speakers
    get_speakers()
    
    print("\n" + "=" * 50)
    print("✅ Done!")

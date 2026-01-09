"""
Validation script to check if all core components can be imported
"""

import sys

def test_imports():
    """Test that all modules can be imported"""
    try:
        print("Checking imports...")
        
        print("  ✓ config")
        import config
        
        print("  ✓ database")
        import database
        
        print("  ✓ audio_storage")
        import audio_storage
        
        print("  ✓ audio_processing")
        import audio_processing
        
        print("  ✓ speaker_recognition")
        import speaker_recognition
        
        print("  ✓ speech_recognition")
        import speech_recognition
        
        print("  ✓ processing_pipeline")
        import processing_pipeline
        
        print("  ✓ main")
        import main
        
        print("\n✅ All modules imported successfully!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def check_structure():
    """Check basic structure of components"""
    try:
        print("\nChecking component structure...")
        
        from config import settings
        print(f"  ✓ Settings loaded (DB: {settings.database_url[:20]}...)")
        
        from audio_processing import VoiceActivityDetector, AudioSegmenter
        print("  ✓ Audio processing classes available")
        
        from speaker_recognition import SpeakerRecognizer
        print("  ✓ Speaker recognition class available")
        
        from speech_recognition import SpeechRecognizer
        print("  ✓ Speech recognition class available")
        
        from audio_storage import AudioStorage
        print("  ✓ Audio storage class available")
        
        from processing_pipeline import VoiceProcessingPipeline
        print("  ✓ Processing pipeline class available")
        
        from database import Speaker, VoiceMessage, init_db
        print("  ✓ Database models available")
        
        print("\n✅ All components structured correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Structure check error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("VoxTrace Validation")
    print("=" * 60)
    
    success = test_imports() and check_structure()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 VoxTrace validation completed successfully!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start PostgreSQL: docker-compose up -d")
        print("3. Run the app: python main.py")
        print("4. Open browser: http://localhost:8000")
        sys.exit(0)
    else:
        print("⚠️  Validation failed. Please check the errors above.")
        sys.exit(1)

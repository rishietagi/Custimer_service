import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env variables from .env
load_dotenv()

from backend.app.services.ai_service import text_to_speech_hindi

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    test_text = "नमस्ते, मैं आपकी क्या मदद कर सकता हूँ?"
    print("Starting test for VibeVoice Hindi 1.5B TTS...")
    try:
        print(f"Input text length: {len(test_text)} characters.")
    except Exception:
        pass
    
    try:
        audio_bytes = text_to_speech_hindi(test_text)
        print("Success! Received audio bytes from Hugging Face Inference API.")
        
        static_dir = os.path.join("backend", "static", "audio")
        os.makedirs(static_dir, exist_ok=True)
        out_file = os.path.join(static_dir, "test_hindi.wav")
        
        with open(out_file, "wb") as f:
            f.write(audio_bytes)
            
        print(f"Saved sample WAV file to: {out_file}")
        print("Test passed successfully!")
    except Exception as e:
        print("\n=== TEST FAILED ===")
        print(f"Error encountered: {e}")
        print("\nCommon cause:")
        print("If you received a 403 Forbidden error stating that the token lacks permission to call Inference Providers:")
        print("Please log in to Hugging Face, navigate to Settings > Access Tokens, and edit your token permissions to check 'Make calls to Inference Providers'.\n")

if __name__ == "__main__":
    main()

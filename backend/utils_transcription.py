import os
import shutil

if not shutil.which("ffmpeg"):
    try:
        import imageio_ffmpeg
        _ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
        if _ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
            print(f"Added imageio-ffmpeg dir to PATH: {_ffmpeg_dir}")
    except Exception as e:
        print(f"WARNING: Could not add ffmpeg to PATH: {e}")
else:
    print(f" ffmpeg already in PATH: {shutil.which('ffmpeg')}")

from google import genai

def transcribe_with_gemini(audio_path: str) -> str:
    """
    Transcribes audio using Google Gemini API by uploading the audio file.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set. Cannot transcribe audio.")

    print(f"[utils_transcription] Transcribing audio with Gemini API for: {audio_path}")
    client = genai.Client(api_key=api_key)
    
    try:
        # Upload the audio file to the Gemini File API
        print(f"[utils_transcription] Uploading audio file to Gemini File API...")
        uploaded_file = client.files.upload(file=audio_path)
        print(f"[utils_transcription] Upload completed. File name: {uploaded_file.name}")
        
        # Call the Gemini model
        print(f"[utils_transcription] Calling Gemini API model to transcribe...")
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                uploaded_file,
                "Please transcribe this audio file into English text. "
                "Provide only the verbatim transcription without any introduction, "
                "acknowledgments, meta-commentary, or summary. Just the text spoken."
            ]
        )
        
        transcript = response.text.strip()
        print(f"[utils_transcription] Transcription completed successfully.")
        
        # Clean up file from Gemini cloud storage
        try:
            client.files.delete(name=uploaded_file.name)
            print(f"[utils_transcription] Deleted cloud file: {uploaded_file.name}")
        except Exception as delete_err:
            print(f"[utils_transcription] Warning: Failed to delete cloud file: {delete_err}")
            
        return transcript

    except Exception as e:
        print(f"[utils_transcription] ERROR: Gemini transcription failed: {e}")
        raise RuntimeError(f"Gemini API transcription failed: {e}") from e

def transcribe_video(video_path: str) -> str:
    """
    Extracts audio from video and transcribes it using Google Gemini API.
    """
    from .utils_audio import extract_audio_from_video
    
    print(f" Starting transcription for: {os.path.basename(video_path)}")
    try:
        # Extract audio from video
        audio_path = extract_audio_from_video(video_path)
        if not audio_path:
             raise RuntimeError("Failed to extract audio from video")

        # Transcribe audio
        transcript = transcribe_with_gemini(audio_path)
        
        # Clean up local temp audio file
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception:
            pass
            
        print(f"Transcription done for: {os.path.basename(video_path)}")
        return transcript

    except Exception as e:
        print(f"ERROR: Transcription failed for {os.path.basename(video_path)}: {e}")
        raise RuntimeError(f"Video transcription failed: {str(e)}") from e

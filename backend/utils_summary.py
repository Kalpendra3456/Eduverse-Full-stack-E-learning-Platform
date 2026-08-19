import os
from google import genai

def summarize_transcript(transcript: str, video_name: str = "unknown_video") -> str:
    """
    Generates a structured summary from a transcript using Google Gemini API.
    Runs entirely offline and locally if the API key is not present.
    Stores the result in the SQLAlchemy database.
    """
    if not transcript:
        return ""

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[utils_summary] WARNING: GEMINI_API_KEY not set. Using basic fallback summary.")
        return _fallback_summary(transcript, video_name)

    print(f"[utils_summary] Generating summary via Gemini API for: {video_name}...")
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""You are an elite educational content creator and summarizer. Please read the following transcript and provide a very detailed, comprehensive, and exhaustive summary of the content.

The summary should be structured as follows:
1. **Overview**: A high-level introduction to the topic.
2. **Key Concepts**: Detailed explanations of every important concept mentioned.
3. **Main Points & Takeaways**: A thorough breakdown of all significant points discussed.
4. **Conclusion**: A final wrap-up of the educational value.

IMPORTANT: 
- The summary MUST be in English, even if the transcript is in another language.
- Provide as much detail as possible. Do not be brief; capture everything important.

Transcript:
{transcript}

Extensive Summary in English:"""

        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        summary = response.text.strip()
        print(f"[utils_summary] SUCCESS: Summary generated via Gemini API")

        # Store in SQLAlchemy database
        from .models import VideoSummary
        from .extensions import db
        try:
            video_summary = VideoSummary(
                video_name=video_name,
                summary=summary,
                transcript=transcript
            )
            db.session.add(video_summary)
            print(f"DEBUG: Added summary for {video_name} to SQLAlchemy session.")
        except Exception as db_e:
            print(f"WARNING: Could not add summary to database session: {db_e}")
        
        return summary
    except Exception as e:
        print(f"[utils_summary] ERROR: Gemini Summary generation failed for {video_name}: {e}")
        return _fallback_summary(transcript, video_name)

def _fallback_summary(transcript: str, video_name: str) -> str:
    """Fallback simple extraction if Gemini API fails or key is missing."""
    sentences = [s.strip() for s in transcript.replace("\n", " ").split(".") if s.strip()]
    if not sentences:
        sentences = [transcript]

    overview_text = sentences[0] if len(sentences) > 0 else "This video covers key educational concepts."
    
    key_points = []
    for i in range(1, min(6, len(sentences))):
        key_points.append(f"- {sentences[i]}.")
    if not key_points:
        key_points.append("- No additional points could be extracted.")
    key_points_str = "\n".join(key_points)

    conclusion_text = sentences[-1] if len(sentences) > 1 else "Review these concepts to master the subject matter."

    summary = f"""**Overview**
This lecture focuses on the primary details of {video_name.replace('_', ' ').replace('-', ' ').title()}.
Details: {overview_text}.

**Key Concepts & Takeaways**
{key_points_str}

**Conclusion**
In conclusion, {conclusion_text} This is a critical building block for the overall curriculum.
"""

    # Store in SQLAlchemy database
    from .models import VideoSummary
    from .extensions import db
    try:
        video_summary = VideoSummary(
            video_name=video_name,
            summary=summary,
            transcript=transcript
        )
        db.session.add(video_summary)
        print(f"DEBUG: Added fallback summary for {video_name} to SQLAlchemy session.")
    except Exception as db_e:
        print(f"WARNING: Could not add fallback summary to database session: {db_e}")

    return summary

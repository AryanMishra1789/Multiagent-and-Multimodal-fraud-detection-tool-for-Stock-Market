import os
import tempfile
from fastapi import UploadFile
import whisper
from moviepy.editor import VideoFileClip
import mimetypes
from deepface import DeepFace
from pyAudioAnalysis import audioBasicIO, audioFeatureExtraction
import numpy as np

# Load Whisper model once (small for speed, can upgrade to base/medium if needed)
whisper_model = whisper.load_model("small")

def extract_audio_from_video(video_path, audio_path):
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path, logger=None)
    clip.close()

def transcribe_audio(audio_path):
    result = whisper_model.transcribe(audio_path)
    return result.get("text", "")

def check_video_deepface_consistency(video_path, frame_sample_rate=30):
    """Check if the same face appears throughout the video using DeepFace. Fast, but robust for hackathon use."""
    import cv2
    cap = cv2.VideoCapture(video_path)
    faces_encountered = []
    frame_count = 0
    embeddings = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_sample_rate == 0:
            try:
                result = DeepFace.represent(frame, enforce_detection=False)
                if result and isinstance(result, list) and len(result) > 0:
                    embeddings.append(result[0]["embedding"])
            except Exception:
                pass
        frame_count += 1
    cap.release()
    if len(embeddings) < 2:
        return {"authenticity": "suspicious", "reason": "No or few faces detected in video frames."}
    # Compare embeddings (cosine similarity)
    from numpy.linalg import norm
    diffs = [np.dot(embeddings[i], embeddings[i-1])/(norm(embeddings[i])*norm(embeddings[i-1])) for i in range(1, len(embeddings))]
    if min(diffs) < 0.7:  # threshold for face change
        return {"authenticity": "suspicious", "reason": "Face identity changes detected in video."}
    return {"authenticity": "likely authentic", "reason": "Face identity appears consistent throughout video."}

def check_audio_pyaudioanalysis(audio_path):
    """Use pyAudioAnalysis to check for anomalies in audio (e.g., silence, abrupt changes, speaker change)."""
    try:
        [Fs, x] = audioBasicIO.read_audio_file(audio_path)
        x = audioBasicIO.stereo_to_mono(x)
        duration = len(x) / float(Fs)
        if duration < 2.0:
            return {"authenticity": "suspicious", "reason": "Audio too short."}
        # Short-term feature extraction
        F, f_names = audioFeatureExtraction.stFeatureExtraction(x, Fs, 0.050*Fs, 0.025*Fs)
        energy = F[1, :]
        if np.mean(energy) < 0.001:
            return {"authenticity": "suspicious", "reason": "Audio is mostly silent."}
        # Check for abrupt changes in energy
        if np.percentile(np.abs(np.diff(energy)), 99) > 0.5:
            return {"authenticity": "suspicious", "reason": "Abrupt changes detected in audio energy."}
    except Exception as e:
        return {"authenticity": "unknown", "reason": f"Audio check failed: {e}"}
    return {"authenticity": "likely authentic", "reason": "Audio appears normal."}

def process_media_file(file: UploadFile):
    # Save uploaded file to temp
    suffix = os.path.splitext(file.filename)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(file.file.read())
        temp_path = temp_file.name

    # Determine if audio or video
    mime_type, _ = mimetypes.guess_type(file.filename)
    transcript = ""
    authenticity = {"authenticity": "unknown", "reason": "No specific reason provided."}
    content_verification = None
    try:
        if mime_type and mime_type.startswith("video"):
            # Extract audio from video
            audio_path = temp_path + ".wav"
            extract_audio_from_video(temp_path, audio_path)
            transcript = transcribe_audio(audio_path)
            authenticity = check_video_deepface_consistency(temp_path)
            # Analyze transcript for content fraud (text-based analysis)
            try:
                from hybrid_verification_agent import hybrid_verify_message
                content_verification = hybrid_verify_message(transcript)
            except Exception as e:
                content_verification = {"classification": "unknown", "reason": f"Text analysis failed: {e}"}
            if not authenticity.get("reason") or authenticity["reason"] == "No specific reason provided.":
                authenticity["reason"] = "Video processed, but no specific DeepFace result."
            os.remove(audio_path)
        elif mime_type and mime_type.startswith("audio"):
            transcript = transcribe_audio(temp_path)
            authenticity = check_audio_pyaudioanalysis(temp_path)
            try:
                from hybrid_verification_agent import hybrid_verify_message
                content_verification = hybrid_verify_message(transcript)
            except Exception as e:
                content_verification = {"classification": "unknown", "reason": f"Text analysis failed: {e}"}
            if not authenticity.get("reason") or authenticity["reason"] == "No specific reason provided.":
                authenticity["reason"] = "Audio processed, but no specific pyAudioAnalysis result."
        else:
            return {"error": "Unsupported file type", "reason": "File is neither audio nor video."}
    finally:
        os.remove(temp_path)

    # Compose a detailed, composite reason
    composite_reason = ""
    if content_verification and isinstance(content_verification, dict):
        text_result = content_verification.get("classification", "unknown")
        text_reason = content_verification.get("reason", "No text analysis details available.")
        composite_reason += f"Text Analysis: {text_result.capitalize()}. {text_reason} "
    if authenticity.get("reason"):
        composite_reason += f"Media Analysis: {authenticity['reason']}"
    else:
        composite_reason += "Media authenticity analysis did not return a specific reason."
    authenticity["reason"] = composite_reason.strip()

    return {
        "transcript": transcript,
        "authenticity": authenticity,
        "content_verification": content_verification
    }

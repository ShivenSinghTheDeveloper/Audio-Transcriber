audio_file = "meeting.wav"
transcript_file = "transcript.txt"


# Model size options (bigger = more accurate, but slower):
#   "tiny", "base", "small", "medium", "large-v3"
# Beginners: start with "base" -- a good speed/accuracy balance on a normal CPU.

model_size = "small"

def transcribe_audio():
    # Import inside the function to avoid heavy top-level imports
    # when this module is imported by other scripts (Windows spawn issue).
    from faster_whisper import WhisperModel

    print(f"Loading the '{model_size}' Whisper model...")
    try:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
    except Exception as e:
        print(f"ERROR loading model: {e}")
        import traceback
        traceback.print_exc()
        return
    print(f"Transcribing {audio_file}")
    segments, info = model.transcribe(audio_file, beam_size=5)
    print(f"Detected language {info.language}")
    print(f"Confidence: {info.language_probability:.2f}\n")
    full_text_parts = []
    with open(transcript_file, "w", encoding="utf-8") as f:
        for segment in segments:
            text = segment.text.strip()
            f.write(text + " ")
            full_text_parts.append(text)
    print("Transcript saved")
    return " ".join(full_text_parts)


# if __name__ == "__main__":
#     transcribe_audio()
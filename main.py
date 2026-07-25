"""
main.py
-------
Runs the full Meeting Summarizer pipeline in one go:
  1. record_audio.py  -> records your system audio to meeting.wav
  2. transcribe.py    -> turns meeting.wav into transcript.txt
  3. summarize.py     -> turns transcript.txt into summary.txt

WHY ARE IMPORTS INSIDE if __name__ == "__main__"?
On Windows, libraries like faster-whisper spawn background worker
processes to do their work. When those workers start, Windows
re-runs this file from the top. If imports like pyaudiowpatch are
at the top level, those workers try to load audio drivers too --
which crashes silently. Moving imports inside the if __name__ block
means only the MAIN process runs them, not the workers.
"""

import multiprocessing
import os
import time

    
def ask(question):
    """Ask a Y/N question and return True if the user says yes."""
    answer = input(f"\n{question} (y/n): ").strip().lower()
    return answer == "y"


if __name__ == "__main__":
    # Required on Windows when using libraries that spawn worker processes
    # (like faster-whisper). Must be the first line inside __main__.
    multiprocessing.freeze_support()

    # Imports are INSIDE __main__ on purpose -- see note at top of file
    from record_audio import record_system_audio
    from transcribe import transcribe_audio
    from summarize import summarize_transcript

    # ── STEP 1: Record ───────────────────────────────────────────────
    print("=" * 40)
    print("STEP 1: Recording audio...")
    print("=" * 40)
    record_system_audio()

    print("Waiting for audio device to release...")
    time.sleep(3)

    # NEW — always looks in the same folder as main.py, no matter what
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    WAV_FILE   = os.path.join(SCRIPT_DIR, "meeting.wav")
    size = os.path.getsize(WAV_FILE)
    print(f"meeting.wav size: {size / 1024:.1f} KB")

    if size < 50000:
        print("ERROR: meeting.wav is too small — nothing was recorded.")
        print("Make sure audio is playing when you run the script!")

    else:
        # ── STEP 2: Transcribe ────────────────────────────────────────
        if ask("Recording done! Proceed to transcription?"):
            print("\n" + "=" * 40)
            print("STEP 2: Transcribing audio...")
            print("=" * 40)
            transcribe_audio()
            time.sleep(1)

            # ── STEP 3: Summarize ─────────────────────────────────────
            if ask("Transcription done! Proceed to summarization?"):
                print("\n" + "=" * 40)
                print("STEP 3: Summarizing transcript...")
                print("=" * 40)
                summarize_transcript()

                print("\n" + "=" * 40)
                print("All done! Check summary.txt for your meeting summary.")
                print("=" * 40)
            else:
                print("Stopped after transcription. transcript.txt is ready.")
        else:
            print("Stopped after recording. meeting.wav is ready.")
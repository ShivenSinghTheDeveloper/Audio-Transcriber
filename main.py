"""
main.py
-------
Runs the full Meeting Summarizer pipeline in one go, using SEPARATE
processes for each step:
  1. record_audio.py  -> records your system audio to meeting.wav
  2. transcribe.py    -> turns meeting.wav into transcript.txt
  3. summarize.py     -> turns transcript.txt into summary.txt

WHY SEPARATE PROCESSES INSTEAD OF JUST CALLING THE FUNCTIONS?
Audio recording libraries (PyAudioWPatch) sometimes leave background
state behind even after they're "done" -- especially with WASAPI
loopback + microphone running together. If the next step (Whisper)
runs in the SAME process, that leftover state can cause a native
crash with no Python error message.

Running each step as its own process means Windows fully cleans up
everything when recording finishes, before transcription even starts.
This is also just good practice for pipelines: each stage is
independent and easy to re-run on its own if something goes wrong.
"""

import os
import subprocess
import sys

SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
WAV_FILE        = os.path.join(SCRIPT_DIR, "meeting.wav")
TRANSCRIPT_FILE = os.path.join(SCRIPT_DIR, "transcript.txt")


def ask(question):
    """Ask a Y/N question and return True if the user says yes."""
    while True:
        answer = input(f"\n{question} (y/n): ").strip().lower()
        if answer in ("y", "n"):
            return answer == "y"
        print("Please type y or n")


def run_step(script_name):
    """
    Runs a script as a completely separate process using the same
    Python interpreter that's running this script. Returns True if
    it finished successfully (exit code 0), False otherwise.
    """
    script_path = os.path.join(SCRIPT_DIR, script_name)
    result = subprocess.run([sys.executable, script_path], cwd=SCRIPT_DIR)
    return result.returncode == 0


if __name__ == "__main__":

    # ── STEP 1: Record ───────────────────────────────────────────────
    print("=" * 40)
    print("STEP 1: Recording audio...")
    print("=" * 40)

    if not run_step("record_audio.py"):
        print("ERROR: recording step failed.")
        sys.exit(1)

    if not os.path.exists(WAV_FILE):
        print(f"ERROR: {WAV_FILE} was not created.")
        sys.exit(1)

    size = os.path.getsize(WAV_FILE)
    print(f"\nmeeting.wav size: {size / 1024:.1f} KB")

    if size < 50000:
        print("ERROR: meeting.wav is too small — nothing was recorded.")
        print("Make sure audio is playing when you run the script!")
        sys.exit(1)

    print("Recording looks good!")

    # ── STEP 2: Transcribe ───────────────────────────────────────────
    if ask("Proceed to transcription?"):
        print("\n" + "=" * 40)
        print("STEP 2: Transcribing audio...")
        print("=" * 40)

        if not run_step("transcribe.py"):
            print("ERROR: transcription step failed.")
            sys.exit(1)

        # ── STEP 3: Summarize ─────────────────────────────────────────
        if ask("Proceed to summarization?"):
            print("\n" + "=" * 40)
            print("STEP 3: Summarizing transcript...")
            print("=" * 40)

            if not run_step("summarize.py"):
                print("ERROR: summarization step failed.")
                sys.exit(1)

            print("\n" + "=" * 40)
            print("All done! Check summary.txt for your meeting summary.")
            print("=" * 40)
        else:
            print("Stopped after transcription. transcript.txt is ready.")
    else:
        print("Stopped after recording. meeting.wav is ready.")
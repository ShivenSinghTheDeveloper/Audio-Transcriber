"""
record_audio.py  —  STEP 1: Record system audio on Windows

Captures three audio sources simultaneously and mixes into one .wav:
  1. Game channel  (YouTube, Spotify, system sounds)
  2. Chat channel  (Zoom/Teams incoming audio from others)
  3. Microphone    (YOUR own voice)
"""

import threading
import time
import wave

import numpy as np
import pyaudiowpatch as pyaudio

DURATION_SECONDS = 30
OUTPUT_FILENAME  = "meeting.wav"
CHUNK            = 512


def find_loopback_device(pa, keywords, ignored=None):
    ignored = ignored or []
    for device in pa.get_loopback_device_info_generator():
        name = device["name"]
        if any(kw in name for kw in ignored):
            continue
        if any(kw in name for kw in keywords):
            return device
    return None


def find_microphone(pa):
    ignored   = ["Voicemod", "Loopback", "S/PDIF", "Digital", "Mapper"]
    preferred = ["HyperX", "Microphone", "Mic"]

    for i in range(pa.get_device_count()):
        device = pa.get_device_info_by_index(i)
        if device["maxInputChannels"] == 0:
            continue
        name = device["name"]
        if any(kw in name for kw in ignored):
            continue
        if any(kw in name for kw in preferred):
            return device

    try:
        return pa.get_default_input_device_info()
    except OSError:
        return None


def record_stream(pa, device, stop_event, frames_container):
    """
    Records audio until stop_event is set.
    Each device uses its own native sample rate to avoid
    'Invalid sample rate' errors on Chat/mic devices.
    Frames are stored as raw bytes (not numpy) to avoid memory issues.
    """
    channels    = device["maxInputChannels"] or 2
    device_rate = int(device["defaultSampleRate"])

    try:
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=device_rate,
            frames_per_buffer=CHUNK,
            input=True,
            input_device_index=device["index"],
        )
    except Exception as e:
        print(f"  Warning: could not open {device['name']}: {e}")
        return

    while not stop_event.is_set():
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames_container.append((data, channels))
        except Exception:
            break

    stream.stop_stream()
    stream.close()


def mix_and_save(streams_with_channels, output_filename, output_rate):
    """
    Mixes multiple audio streams chunk by chunk and writes directly
    to the wav file. This avoids loading everything into memory at once,
    which was causing silent crashes with large recordings.

    Each stream entry is a list of (raw_bytes, channels) tuples.
    """
    # Filter out empty streams
    valid = [s for s in streams_with_channels if s]

    if not valid:
        raise RuntimeError(
            "No audio was recorded.\n"
            "Make sure audio is playing when you run the script!"
        )

    print(f"  Mixing {len(valid)} stream(s) chunk by chunk...")

    # Find the shortest stream so all streams stay aligned
    min_chunks = min(len(s) for s in valid)
    print(f"  Total chunks to process: {min_chunks}")

    with wave.open(output_filename, "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)  # 2 bytes = int16
        wav_file.setframerate(output_rate)

        for i in range(min_chunks):
            mixed = None

            for stream in valid:
                raw, channels = stream[i]

                # Convert raw bytes to int32 numpy array for mixing
                audio = np.frombuffer(raw, dtype=np.int16).astype(np.int32)

                # If mono mic, duplicate to stereo
                if channels == 1:
                    audio = np.repeat(audio, 2)

                # Trim to same length in case of small size differences
                if mixed is None:
                    mixed = audio
                else:
                    min_len = min(len(mixed), len(audio))
                    mixed   = mixed[:min_len] + audio[:min_len]

            # Average and clip back to int16
            result = np.clip(mixed // len(valid), -32768, 32767).astype(np.int16)
            wav_file.writeframes(result.tobytes())

    print(f"  Done mixing.")


def record_system_audio():
    with pyaudio.PyAudio() as pa:

        game_device = find_loopback_device(
            pa,
            keywords=["Game", "Speakers", "HyperX"],
            ignored=["Chat", "Voicemod", "S/PDIF", "Digital", "NVIDIA"]
        )
        chat_device = find_loopback_device(
            pa,
            keywords=["Chat", "Headset", "Earphone"],
            ignored=["Voicemod", "S/PDIF", "Digital", "NVIDIA"]
        )
        mic_device = find_microphone(pa)

        print("Audio sources:")
        print(f"  Game channel : {game_device['name'] if game_device else 'NOT FOUND'}")
        print(f"  Chat channel : {chat_device['name'] if chat_device else 'NOT FOUND'}")
        print(f"  Microphone   : {mic_device['name'] if mic_device else 'NOT FOUND'}")

        if not game_device:
            raise RuntimeError("Could not find a speaker loopback device.")

        game_frames = []
        chat_frames = []
        mic_frames  = []

        stop_event = threading.Event()

        threads = [
            threading.Thread(target=record_stream,
                args=(pa, game_device, stop_event, game_frames))
        ]
        if chat_device:
            threads.append(threading.Thread(target=record_stream,
                args=(pa, chat_device, stop_event, chat_frames)))
        if mic_device:
            threads.append(threading.Thread(target=record_stream,
                args=(pa, mic_device, stop_event, mic_frames)))

        print(f"\nRecording for {DURATION_SECONDS} seconds...")
        print("Speak into your mic AND have your meeting running!\n")

        for t in threads:
            t.start()

        for remaining in range(DURATION_SECONDS, 0, -5):
            print(f"  {remaining} seconds remaining...")
            time.sleep(5)

        print("\nStopping recording...")
        stop_event.set()
        for t in threads:
            t.join(timeout=3)

        print(f"  Game chunks : {len(game_frames)}")
        print(f"  Chat chunks : {len(chat_frames)}")
        print(f"  Mic chunks  : {len(mic_frames)}")

        output_rate = int(game_device["defaultSampleRate"])

        print("Mixing and saving audio...")
        try:
            streams_to_mix = [game_frames]
            if chat_frames:
                streams_to_mix.append(chat_frames)
            if mic_frames:
                streams_to_mix.append(mic_frames)

            mix_and_save(streams_to_mix, OUTPUT_FILENAME, output_rate)
        except Exception as e:
            print(f"ERROR during mixing: {e}")
            import traceback
            traceback.print_exc()
            return

    print(f"Done! Saved to: {OUTPUT_FILENAME}")


if __name__ == "__main__":
    record_system_audio()
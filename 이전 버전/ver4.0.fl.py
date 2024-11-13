import numpy as np
import queue
import threading
import matplotlib.pyplot as plt
import parselmouth
import speech_recognition as sr
from faster_whisper import WhisperModel
from gtts import gTTS

# declare and initialize varible
r = sr.Recognizer()
audio_queue = queue.Queue()
plot_queue = queue.Queue()

# load model
model = WhisperModel("tiny.en", device="cpu", compute_type="int8")


def record_audio():
    """
    record audio and add to audio queue
    """
    with sr.Microphone(sample_rate=16000) as source:
        r.adjust_for_ambient_noise(source)
        print("Recording... Press Ctrl+C to stop.")
        try:
            while True:
                audio_queue.put(r.listen(source))
        except KeyboardInterrupt:
            print("Recording stopped.")
            audio_queue.put(None)


def transcribe_audio():
    """
    fetch audio_data from audio_queue and transcribe
    """
    while True:
        audio = audio_queue.get()
        if audio is None:
            break
        try:
            audio_data = np.frombuffer(audio.get_raw_data(),
                                       np.int16).astype(np.float32) / 32768.0
            segments, _ = model.transcribe(audio_data, beam_size=5)

            text = " ".join(segment.text for segment in segments)
            print(text)

            plot_queue.put((audio_data, text))

        except Exception as e:
            print("Error during transcription:", e)


def process_data(audio_data, text, threshold=5):
    # Process original audio
    og_voice = parselmouth.Sound(audio_data, 16000)
    og_pitch = og_voice.to_pitch()
    og_times = og_pitch.xs()
    og_freq = og_pitch.selected_array['frequency']

    # Trim leading and trailing zeros in original pitch data
    nz_indices_og = np.nonzero(og_freq)[0]
    if nz_indices_og.size > 0:
        start_og, end_og = nz_indices_og[0], nz_indices_og[-1] + 1
        og_times = og_times[start_og:end_og]
        og_freq = og_freq[start_og:end_og]

    # Remove short non-zero segments in original pitch data
    non_zero_indices = np.nonzero(og_freq)[0]
    if non_zero_indices.size > 0:
        start = non_zero_indices[0]
        filtered_times = []
        filtered_freq = []

        for i in range(1, len(non_zero_indices)):
            # Check if the current index is consecutive
            if non_zero_indices[i] != non_zero_indices[i - 1] + 1:
                end = non_zero_indices[i - 1]
                segment_length = end - start + 1
                if segment_length >= threshold:
                    # Retain the segment
                    filtered_times.extend(og_times[start:end + 1])
                    filtered_freq.extend(og_freq[start:end + 1])
                start = non_zero_indices[i]

        # Handle the last segment
        end = non_zero_indices[-1]
        segment_length = end - start + 1
        if segment_length >= threshold:
            filtered_times.extend(og_times[start:end + 1])
            filtered_freq.extend(og_freq[start:end + 1])

        og_times = np.array(filtered_times)
        og_freq = np.array(filtered_freq)

    # Generate TTS audio from text
    tts = gTTS(text=text, lang="en")
    tts.save("audio.mp3")

    # Process TTS audio
    tts_voice = parselmouth.Sound("audio.mp3")
    tts_pitch = tts_voice.to_pitch()
    tts_times = tts_pitch.xs()
    tts_freq = tts_pitch.selected_array['frequency']

    # Trim leading and trailing zeros in TTS pitch data
    nz_indices_tts = np.nonzero(tts_freq)[0]
    if nz_indices_tts.size > 0:
        start_tts, end_tts = nz_indices_tts[0], nz_indices_tts[-1] + 1
        tts_times = tts_times[start_tts:end_tts]
        tts_freq = tts_freq[start_tts:end_tts]

    return og_times, og_freq, tts_times, tts_freq


def plot_graph():
    while True:
        plot_data = plot_queue.get()
        audio_data, text = plot_data

        if text == "" or text == ".":
            continue

        # Process data
        og_times, og_freq, tts_times, tts_freq = process_data(audio_data, text)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 7))

        ax1.set_title(f"OG-TTS Pitch - {text}")
        ax1.set_ylim(0, 500)
        ax1.set_xticks([])
        ax1.set_yticks([])

        for i in range(len(og_freq) - 1):
            if abs(og_freq[i + 1] - og_freq[i]) <= 25:
                ax1.plot(og_times[i:i + 2], og_freq[i:i + 2], color='blue',
                         linestyle='-')
            ax1.plot(og_times[i], og_freq[i], color='blue', markersize=3)
        ax1.legend(["Original Voice Pitch"])

        ax2.set_ylim(0, 500)
        ax2.set_xticks([])
        ax2.set_yticks([])

        for i in range(len(tts_freq) - 1):
            if abs(tts_freq[i + 1] - tts_freq[i]) <= 25:
                ax2.plot(tts_times[i:i + 2], tts_freq[i:i + 2], color='red',
                         linestyle='-')
            ax2.plot(tts_times[i], tts_freq[i], color='red', markersize=3)
        ax2.legend(["TTS Voice Pitch"])

        plt.tight_layout()
        plt.show()


# 쓰레딩
record_thread = threading.Thread(target=record_audio)
transcribe_thread = threading.Thread(target=transcribe_audio)
plot_thread = threading.Thread(target=plot_graph)

record_thread.start()
transcribe_thread.start()
plot_thread.start()

record_thread.join()
transcribe_thread.join()
plot_thread.join()

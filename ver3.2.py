from threading import Thread
from queue import Queue
import numpy as np
import speech_recognition as sr
from faster_whisper import WhisperModel
import parselmouth
import matplotlib.pyplot as plt
from gtts import gTTS

r = sr.Recognizer()
audio_queue = Queue()

model = WhisperModel("tiny.en", device="cpu", compute_type="int8")


def plot_pitch(audio_data, sample_rate, text):
    tts = gTTS(text=text, lang="en")
    tts.save("audio.mp3")

    snd = parselmouth.Sound("audio.mp3")
    pitch = snd.to_pitch()
    pitch_values = pitch.selected_array["frequency"]
    pitch_values[pitch_values == 0] = np.nan
    time_pitch = pitch.xs()

    snd2 = parselmouth.Sound(audio_data, sampling_frequency=sample_rate)
    pitch2 = snd2.to_pitch()
    original_values = pitch2.selected_array['frequency']
    original_values[original_values == 0] = np.nan
    time_pitch2 = pitch2.xs()

    target_length = len(original_values)
    pitch_values = np.interp(
            np.linspace(0, len(pitch_values) - 1, target_length),
            np.arange(len(pitch_values)), pitch_values
            )
    time_pitch = np.interp(
            np.linspace(0, len(time_pitch) - 1, target_length),
            np.arange(len(time_pitch)), time_pitch
            )

    plt.figure(figsize=(10, 6))
    plt.plot(time_pitch2, original_values, 'o', markersize=3,
             color='b', label="Original Audio Pitch")
    plt.plot(time_pitch, pitch_values, 'o', markersize=3,
             color='g', label="Synthesized Audio Pitch")
    plt.xlabel("Time (s)")
    plt.ylabel("Pitch (Hz)")
    plt.title("Comparison of Original and Synthesized Audio Pitch Over Time")
    plt.legend()
    plt.tight_layout()
    plt.show()


def recognize_worker():
    while True:
        audio = audio_queue.get()
        if audio is None:
            break

        try:
            audio_data = np.frombuffer(
                audio.get_raw_data(),
                np.int16
            ).astype(np.float32) / 32768.0

            segments, _ = model.transcribe(audio_data, beam_size=5)

            for segment in segments:
                text = segment.text
                print(text)

                plot_pitch(audio_data, 16000, text)

        except Exception as e:
            print(e)

        audio_queue.task_done()


recognize_thread = Thread(target=recognize_worker)
recognize_thread.daemon = True
recognize_thread.start()

with sr.Microphone(sample_rate=16000) as source:
    r.adjust_for_ambient_noise(source)
    print("Recording... Press Ctrl+C to stop.")
    try:
        while True:
            audio_queue.put(r.listen(source))
    except KeyboardInterrupt:
        pass

audio_queue.join()
audio_queue.put(None)
recognize_thread.join()

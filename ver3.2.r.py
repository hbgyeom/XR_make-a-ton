import numpy as np
import queue
import threading
import matplotlib.pyplot as plt
import librosa
import speech_recognition as sr
from faster_whisper import WhisperModel

r = sr.Recognizer()
audio_queue = queue.Queue()
plot_queue = queue.Queue()

model = WhisperModel("tiny.en", device="cpu", compute_type="int8")


def record_audio():
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
    while True:
        audio = audio_queue.get()
        if audio is None:
            plot_queue.put(None)
            break
        try:
            audio_data = np.frombuffer(audio.get_raw_data(),
                                       np.int16).astype(np.float32) / 32768.0
            segments, _ = model.transcribe(audio_data, beam_size=5)

            text = "".join(segment.text for segment in segments)
            print(text)

            plot_queue.put((audio_data, text))

        except Exception as e:
            print("Error during transcription:", e)


def plot_graph():
    while True:
        item = plot_queue.get()
        if item is None:
            break
        audio_data, text = item

        sr = 16000


record_thread = threading.Thread(target=record_audio)
transcribe_thread = threading.Thread(target=transcribe_audio)
plot_thread = threading.Thread(target=plot_graph)

record_thread.start()
transcribe_thread.start()
plot_thread.start()

record_thread.join()
transcribe_thread.join()
plot_thread.join()

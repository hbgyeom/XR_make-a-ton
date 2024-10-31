from threading import Thread
from queue import Queue
import numpy as np
import speech_recognition as sr
from faster_whisper import WhisperModel

r = sr.Recognizer()
audio_queue = Queue()

model = WhisperModel("base", device="cpu", compute_type="int8")


def recognize_worker():
    while True:
        audio = audio_queue.get()
        if audio is None:
            break

        try:
            audio_data = np.frombuffer(audio.get_raw_data(), np.int16).astype(np.float32) / 32768.0

            segments, _ = model.transcribe(audio_data, language="ko", beam_size=5)

            for segment in segments:
                print(segment.text)

        except Exception as e:
            print(e)

        audio_queue.task_done()


recognize_thread = Thread(target=recognize_worker)
recognize_thread.daemon = True
recognize_thread.start()
with sr.Microphone(sample_rate=16000) as source:
    try:
        while True:
            audio_queue.put(r.listen(source))
    except KeyboardInterrupt:
        pass

audio_queue.join()
audio_queue.put(None)
recognize_thread.join()

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

model = WhisperModel("tiny", device="cpu", compute_type="int8")


def recognize_worker():
    while True:
        audio = audio_queue.get()
        if audio is None:
            break

        try:
            audio_data = np.frombuffer(audio.get_raw_data(), np.int16).astype(np.float32) / 32768.0

            segments, _ = model.transcribe(audio_data, beam_size=5)

            for segment in segments:
                print(segment.text)
                tts = gTTS(text=segment.text, lang='en')
                tts.save("audio.mp3")
                snd = parselmouth.Sound("audio.mp3")
                pitch = snd.to_pitch()
                pitch_values = pitch.selected_array['frequency']
                pitch_values[pitch_values == 0] = np.nan
                time_pitch = pitch.xs()
                plt.figure(figsize=(10, 6))
                plt.plot(time_pitch, pitch_values, 'o', markersize=3, color='b')
                plt.xlabel("Time (s)")
                plt.ylabel("Pitch (Hz)")
                plt.title("Pitch over time")
                plt.tight_layout()
                plt.show()

                break

        except Exception as e:
            print(e)

        audio_queue.task_done()


recognize_thread = Thread(target=recognize_worker)
recognize_thread.daemon = True
recognize_thread.start()
with sr.Microphone(sample_rate=16000) as source:
    print("Ready for recording")
    try:
        while True:
            audio_queue.put(r.listen(source))
    except KeyboardInterrupt:
        pass

audio_queue.join()
audio_queue.put(None)
recognize_thread.join()

import numpy as np
import queue
import threading
import matplotlib.pyplot as plt
import parselmouth
import speech_recognition as sr
from faster_whisper import WhisperModel
from gtts import gTTS

# 변수 선언
r = sr.Recognizer()
audio_queue = queue.Queue()
plot_queue = queue.Queue()

# 모델 로드
model = WhisperModel("tiny.en", device="cpu", compute_type="int8")


def record_audio():
    """
    오디오 녹음 후 audio_queue에 추가
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
    audio_queue에서 audio_data 가져온 후 모델 로드해 transcribe
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


def plot_graph():
    """
    plot_queue에서 audio_data, text 가져온 후 그래프 그림
    """
    while True:
        plot_data = plot_queue.get()
        audio_data, text = plot_data

        og_voice = parselmouth.Sound(audio_data, 16000)
        og_pitch = og_voice.to_pitch()
        og_times = og_pitch.xs()
        og_freq = og_pitch.selected_array['frequency']

        nz_indices_og = np.nonzero(og_freq)[0]
        if nz_indices_og.size > 0:  # Ensure there are non-zero elements
            start_og, end_og = nz_indices_og[0], nz_indices_og[-1] + 1
            og_times = og_times[start_og:end_og]
            og_freq = og_freq[start_og:end_og]
            
        if text == "":
            print("Text is empty, skipping plot.")
            continue
        elif text == ".":
            print("Text is just a period, skipping plot.")
            continue
            
        tts = gTTS(text=text, lang="en")
        tts.save("audio.mp3")
        tts_voice = parselmouth.Sound("audio.mp3")
        tts_pitch = tts_voice.to_pitch()
        tts_times = tts_pitch.xs()
        tts_freq = tts_pitch.selected_array['frequency']

        nz_indices_tts = np.nonzero(tts_freq)[0]
        if nz_indices_tts.size > 0:  # Ensure there are non-zero elements
            start_tts, end_tts = nz_indices_tts[0], nz_indices_tts[-1] + 1
            tts_times = tts_times[start_tts:end_tts]
            tts_freq = tts_freq[start_tts:end_tts]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 5))

        ax1.scatter(og_times, og_freq, color='blue', s=25,
                    label="Original Voice Pitch")
        ax1.set_title(f"{text}")
        ax1.set_ylim(0, 500)

        ax2.scatter(tts_times, tts_freq, color='red', s=25,
                    label="TTS Voice Pitch")
        ax2.set_ylim(0, 500)

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

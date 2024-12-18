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
new_request = 0

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
            
            if text == "":
                print("Text is empty, skipping plot.")
                continue
            elif text == ".":
                print("Text is just a period, skipping plot.")
                continue
            elif text == " ":
                print(" skipping plot.")
                continue
            new_request = 1
            print("new request changed")
            print(text)

            plot_queue.put((audio_data, text))

        except Exception as e:
            print("Error during transcription:", e)

def plot_graph():
    """
    Retrieves audio_data and text from plot_queue, then plots pitch and intensity graphs.
    """
    while True:
        plot_data = plot_queue.get()
        audio_data, text = plot_data

        og_voice = parselmouth.Sound(audio_data, 16000)
        
        # Pitch analysis
        og_pitch = og_voice.to_pitch()
        og_times = og_pitch.xs()
        og_freq = og_pitch.selected_array['frequency']
        
        # Filter non-zero frequencies for original pitch
        nz_indices_og = np.nonzero(og_freq)[0]
        if nz_indices_og.size > 0:
            start_og, end_og = nz_indices_og[0], nz_indices_og[-1] + 1
            og_times = og_times[start_og:end_og]
            og_freq = og_freq[start_og:end_og]
        
        # Intensity analysis
        og_intensity = og_voice.to_intensity()
        og_intensity_times = og_intensity.xs()
        og_intensity_values = og_intensity.values.T
        
        if text == "":
            print("Text is empty, skipping plot.")
            continue
        elif text == ".":
            print("Text is just a period, skipping plot.")
            continue
        elif text == " ":
            print(" skipping plot.")
            continue
        
        # TTS audio and analysis
        tts = gTTS(text=text, lang="en")
        tts.save("audio.mp3")
        tts_voice = parselmouth.Sound("audio.mp3")
        
        # TTS pitch analysis
        tts_pitch = tts_voice.to_pitch()
        tts_times = tts_pitch.xs()
        tts_freq = tts_pitch.selected_array['frequency']
        
        # Filter non-zero frequencies for TTS pitch
        nz_indices_tts = np.nonzero(tts_freq)[0]
        if nz_indices_tts.size > 0:
            start_tts, end_tts = nz_indices_tts[0], nz_indices_tts[-1] + 1
            tts_times = tts_times[start_tts:end_tts]
            tts_freq = tts_freq[start_tts:end_tts]
        
        # TTS intensity analysis
        tts_intensity = tts_voice.to_intensity()
        tts_intensity_times = tts_intensity.xs()
        tts_intensity_values = tts_intensity.values.T

        # Plotting
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 7))
        ax1.patch.set_alpha(0.0)  # Transparent axis background for ax1
        ax2.patch.set_alpha(0.0)  # Transparent axis background for ax2

        # Original Voice Pitch plot
        ax1.scatter(og_times, og_freq, color='blue', s=25, label="Original Voice Pitch")
        ax1.plot(og_intensity_times, 3*og_intensity_values, color='green', label="Original Voice Intensity")
        ax1.set_title(f"{text}")
        ax1.set_ylim(0, 300)
        ax1.set_xticks([])  # Remove x-axis ticks
        ax1.set_yticks([])  # Remove y-axis ticks

        # TTS Voice Pitch plot
        ax2.scatter(tts_times, tts_freq, color='red', s=25, label="TTS Voice Pitch")
        ax2.plot(tts_intensity_times, 2*tts_intensity_values, color='green', label="TTS Voice Intensity")
        ax2.set_ylim(0, 500)
        ax2.set_xticks([])  # Remove x-axis ticks
        ax2.set_yticks([])  # Remove y-axis ticks
        plt.tight_layout()
        new_request = 0
        plt.draw() 
        while True:
            if(new_request):
                plt.close('all')
                print("close all")
                break

        


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

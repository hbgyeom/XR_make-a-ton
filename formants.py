import numpy as np
import queue
import threading
import matplotlib
import matplotlib.pyplot as plt
import parselmouth
import speech_recognition as sr
from faster_whisper import WhisperModel
from gtts import gTTS
from PIL import Image
import os

# Run matplotlib in headless backend
matplotlib.use('Agg')

# Initialize recognizer, queues, spaces
r = sr.Recognizer()
audio_queue = queue.Queue()
plot_queue = queue.Queue()
spaces = [" " * 80, " " * 40, " " * 30, " " * 22, " " * 19, " " * 16]

# Load model
model = WhisperModel("tiny.en", device="cpu", compute_type="int8")


def transcribe_audio():
    """
    Add comments here
    """
    while True:
        audio = audio_queue.get()
        if audio is None:
            print("Trascribing stopped")
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


def high_seg(times, freq):
    """
    Filters out anomaly with 2-sigma upper limit
    """
    mean_freq = np.mean(freq)
    std_freq = np.std(freq)

    filtered_freq = np.where(freq > mean_freq + 2 * std_freq, 0, freq)
    return np.array(times), np.array(filtered_freq)


def short_seg(times, freq, threshold):
    """
    Filters out segments shorter than threshold
    """
    filtered_times = []
    filtered_freq = []
    current_segment_times = []
    current_segment_freq = []

    for i in range(len(freq)):
        if freq[i] != 0:
            current_segment_times.append(times[i])
            current_segment_freq.append(freq[i])
        else:
            if len(current_segment_freq) >= threshold:
                filtered_times.extend(current_segment_times)
                filtered_freq.extend(current_segment_freq)
            filtered_times.append(times[i])
            filtered_freq.append(freq[i])
            current_segment_times = []
            current_segment_freq = []

    if len(current_segment_freq) >= threshold:
        filtered_times.extend(current_segment_times)
        filtered_freq.extend(current_segment_freq)

    return np.array(filtered_times), np.array(filtered_freq)


def process_data(audio_data, text, threshold=5):
    """
    Processes the audio to extract formant frequencies (F1, F2, F3).
    """
    og_voice = parselmouth.Sound(audio_data, 16000)

    # Extract formants using Burg method
    og_formant = og_voice.to_formant_burg()
    og_times = og_formant.xs()
    f1 = og_formant.get_value_at_time(1, og_times)
    f2 = og_formant.get_value_at_time(2, og_times)
    f3 = og_formant.get_value_at_time(3, og_times)

    # Clean up data (remove NaNs or zeros)
    f1 = np.nan_to_num(f1)
    f2 = np.nan_to_num(f2)
    f3 = np.nan_to_num(f3)

    # Text-to-speech synthesis
    tts = gTTS(text=text, lang="en")
    tts.save("audio.mp3")

    tts_voice = parselmouth.Sound("audio.mp3")
    tts_formant = tts_voice.to_formant_burg()
    tts_times = tts_formant.xs()
    tts_f1 = tts_formant.get_value_at_time(1, tts_times)
    tts_f2 = tts_formant.get_value_at_time(2, tts_times)
    tts_f3 = tts_formant.get_value_at_time(3, tts_times)

    tts_f1 = np.nan_to_num(tts_f1)
    tts_f2 = np.nan_to_num(tts_f2)
    tts_f3 = np.nan_to_num(tts_f3)

    formants_return = [og_times, f1, f2, f3, tts_times, tts_f1, tts_f2, tts_f3]

    os.remove("audio.mp3")
    return formants_return



def create_plot(ax, formant_data, color, text):
    """
    Creates the plot for formants (F1, F2, F3).
    """
    ax[0].set_title(f"{text}")
    ax[0].set_xticks([])
    ax[0].set_yticks([])
    ax[0].plot(formant_data[0], formant_data[1], color='red', label='F1', linewidth=2)
    ax[0].plot(formant_data[0], formant_data[2], color='green', label='F2', linewidth=2)
    ax[0].plot(formant_data[0], formant_data[3], color='blue', label='F3', linewidth=2)
    ax[0].legend(loc="upper right")

    ax[1].set_title("                        ")
    ax[1].set_xticks([])
    ax[1].set_yticks([])
    ax[1].plot(formant_data[4], formant_data[5], color='red', linestyle='--', label='F1 (TTS)', linewidth=2)
    ax[1].plot(formant_data[4], formant_data[6], color='green', linestyle='--', label='F2 (TTS)', linewidth=2)
    ax[1].plot(formant_data[4], formant_data[7], color='blue', linestyle='--', label='F3 (TTS)', linewidth=2)
    ax[1].legend(loc="upper right")



def plot_graph():
    """
    Add comments here
    """
    while True:
        plot_data = plot_queue.get()
        if plot_data is None:
            print("Plotting stopped.")
            break

        try:
            audio_data, text = plot_data

            if text == "" or text == ".":
                continue

            formants_return = process_data(audio_data, text)
            
            create_plot(ax1, formants_return[:4], color='blue', text=text)
            create_plot(ax2, formants_return[4:], color='red', text=text)


            if ',' in text:
                text = spaces[0].join(text.split(','))
            else:
                words = text.split()
                num_words = len(words)
                if (num_words > 7):
                    num_words = 7
                    text = spaces[num_words - 2].join(words)

            fig1, ax1 = plt.subplots(2, 1, figsize=(10, 4))
            ax1[0].set_ylabel('Pitch  ', rotation=0, labelpad=22, fontsize=20)
            plt.ylabel('Intensity', rotation=0, labelpad=33, fontsize=15)
            create_plot(ax1, pitch_return[:2], intensity_return[:2],
                        color='blue', text=text)
            plt.savefig("og_plot.png", pad_inches=0)
            plt.close(fig1)

            fig2, ax2 = plt.subplots(2, 1, figsize=(10, 4))
            create_plot(ax2, pitch_return[2:], intensity_return[2:],
                        color='red', text=text)
            plt.savefig("tts_plot.png", pad_inches=0)
            plt.close(fig2)

            og_img = Image.open("og_plot.png")
            tts_img = Image.open("tts_plot.png")
            blended_img = Image.blend(og_img, tts_img, alpha=0.5)
            blended_img.save("blended_img.png")

            og_img.close()
            tts_img.close()
            blended_img.close()
            os.remove("og_plot.png")
            os.remove("tts_plot.png")

        except Exception as e:
            print(e)


# Start threading
transcribe_thread = threading.Thread(target=transcribe_audio, daemon=True)
plot_thread = threading.Thread(target=plot_graph, daemon=True)
transcribe_thread.start()
plot_thread.start()

# Record audio
with sr.Microphone(sample_rate=16000) as source:
    r.adjust_for_ambient_noise(source)
    print("Recording... Press Ctrl+C to stop.")
    try:
        while True:
            audio_queue.put(r.listen(source))
    except KeyboardInterrupt:
        print("Recording stopped.")
        audio_queue.put(None)
        plot_queue.put(None)
        transcribe_thread.join()
        plot_thread.join()

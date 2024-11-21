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


def process_formant(og_voice, tts_voice):
    og_pitch = og_voice.to_pitch()
    og_times = og_pitch.xs()
    og_freq = og_pitch.selected_array['frequency']

    nz_indices_og = np.nonzero(og_freq)[0]
    if nz_indices_og.size > 0:
        start_og, end_og = nz_indices_og[0], nz_indices_og[-1] + 1
        og_times = og_times[start_og:end_og]
        og_freq = og_freq[start_og:end_og]
    else:
        start_og, end_og = 0, len(og_freq) - 1

    og_formant = og_voice.to_formant_burg(time_step=0.01,
                                          max_number_of_formants=5)
    og_valid_times = [t for t, p in zip(og_times, og_freq) if p > 0]
    formant_0 = [og_formant.get_value_at_time(1, t) for t in og_valid_times]
    formant_1 = [og_formant.get_value_at_time(2, t) for t in og_valid_times]
    formant_2 = [og_formant.get_value_at_time(3, t) for t in og_valid_times]

    tts_pitch = tts_voice.to_pitch()
    tts_times = tts_pitch.xs()
    tts_freq = tts_pitch.selected_array['frequency']

    nz_indices_tts = np.nonzero(tts_freq)[0]
    if nz_indices_tts.size > 0:
        start_tts, end_tts = nz_indices_tts[0], nz_indices_tts[-1] + 1
        tts_times = tts_times[start_tts:end_tts]
        tts_freq = tts_freq[start_tts:end_tts]
    else:
        start_tts, end_tts = 0, len(tts_freq) - 1

    tts_formant = tts_voice.to_formant_burg(time_step=0.01,
                                            max_number_of_formants=5)
    tts_valid_times = [t for t, p in zip(tts_times, tts_freq) if p > 0]
    formant_3 = [tts_formant.get_value_at_time(1, t) for t in tts_valid_times]
    formant_4 = [tts_formant.get_value_at_time(2, t) for t in tts_valid_times]
    formant_5 = [tts_formant.get_value_at_time(3, t) for t in tts_valid_times]

    formant_times = [og_valid_times, tts_valid_times]
    formant_return = [formant_0, formant_1, formant_2, formant_3,
                      formant_4, formant_5]
    return formant_times, formant_return


def process_data(audio_data, text, threshold=5):
    """
    Add comments here
    """
    og_voice = parselmouth.Sound(audio_data, 16000)

    og_pitch = og_voice.to_pitch()
    og_times = og_pitch.xs()[::2]
    temp = len(og_times)
    og_freq = og_pitch.selected_array['frequency'][::2]

    og_times, og_freq = high_seg(og_times, og_freq)
    og_times, og_freq = short_seg(og_times, og_freq, 5)

    nz_indices_og = np.nonzero(og_freq)[0]
    if nz_indices_og.size > 0:
        start_og, end_og = nz_indices_og[0], nz_indices_og[-1] + 1
        og_times = og_times[start_og:end_og]
        og_freq = og_freq[start_og:end_og]
    else:
        start_og, end_og = 0, len(og_freq) - 1

    og_intensity = og_voice.to_intensity()
    og_intensity_times = og_intensity.xs()[::2]
    length = len(og_intensity_times)
    og_intensity_times = og_intensity_times[
        length * start_og // temp:length * end_og // temp]
    og_intensity_values = og_intensity.values.T[::2]
    og_intensity_values = og_intensity_values[
        length * start_og // temp:length * end_og // temp]

    tts = gTTS(text=text, lang="en")
    tts.save("audio.mp3")

    tts_voice = parselmouth.Sound("audio.mp3")

    tts_pitch = tts_voice.to_pitch()
    tts_times = tts_pitch.xs()[::2]
    temp2 = len(tts_times)
    tts_freq = tts_pitch.selected_array['frequency'][::2]

    nz_indices_tts = np.nonzero(tts_freq)[0]
    if nz_indices_tts.size > 0:
        start_tts, end_tts = nz_indices_tts[0], nz_indices_tts[-1] + 1
        tts_times = tts_times[start_tts:end_tts]
        tts_freq = tts_freq[start_tts:end_tts]
    else:
        start_tts, end_tts = 0, len(tts_freq) - 1

    tts_intensity = tts_voice.to_intensity()
    tts_intensity_times = tts_intensity.xs()[::2]
    length2 = len(tts_intensity_times)
    tts_intensity_times = tts_intensity_times[
        length2 * start_tts // temp2:length2 * end_tts // temp2]
    tts_intensity_values = tts_intensity.values.T[::2]
    tts_intensity_values = tts_intensity_values[
        length2 * start_tts // temp2:length2 * end_tts // temp2]

    formant_times, formant_return = process_formant(og_voice, tts_voice)

    pitch_return = [og_times, og_freq, tts_times, tts_freq]
    intensity_return = [og_intensity_times, og_intensity_values,
                        tts_intensity_times, tts_intensity_values]

    os.remove("audio.mp3")

    return pitch_return, intensity_return, formant_times, formant_return


def create_plot(ax, pitch_data, intensity_data, color, text):
    """
    Add comments here
    """
    ax[0].set_title(f"{text}")
    ax[0].set_ylim(min(pitch_data[1]) * 0.9, max(pitch_data[1]) * 1.1)
    ax[0].set_xticks([])
    ax[0].set_yticks([])
    for i in range(len(pitch_data[1]) - 1):
        if abs(pitch_data[1][i + 1] - pitch_data[1][i]) <= 50:
            ax[0].plot(pitch_data[0][i:i + 2], pitch_data[1][i:i + 2],
                       color=color, linestyle='-', linewidth=3)
        ax[0].plot(pitch_data[0][i], pitch_data[1][i],
                   color=color, markersize=3)

    ax[1].set_title("                        ")
    ax[1].set_ylim(min(intensity_data[1]), max(intensity_data[1]) * 1.1)
    ax[1].set_xticks([])
    ax[1].set_yticks([])
    ax[1].plot(intensity_data[0], intensity_data[1],
               color=color, linestyle='-', linewidth=3)


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

            pitch_return, intensity_return, formant_times, formant_return = process_data(audio_data, text)

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

            plt.figure(figsize=(12, 6))
            plt.scatter(formant_times[0], formant_return[0],
                        color="blue", s=10)
            plt.scatter(formant_times[0], formant_return[1],
                        color="blue", s=10)
            plt.scatter(formant_times[0], formant_return[2],
                        color="blue", s=10)

            plt.title(text, fontsize=14)
            plt.xticks([])
            plt.yticks([])

            plt.tight_layout()
            plt.savefig("og_formant.png", pad_inches=0)

            # tts
            plt.figure(figsize=(12, 6))
            plt.scatter(formant_times[1], formant_return[3],
                        color="red", s=10)
            plt.scatter(formant_times[1], formant_return[4],
                        color="red", s=10)
            plt.scatter(formant_times[1], formant_return[5],
                        color="red", s=10)

            plt.title(text, fontsize=14)
            plt.xticks([])
            plt.yticks([])

            plt.tight_layout()
            plt.savefig("tts_formant.png", pad_inches=0)
            plt.close()

            og_img2 = Image.open("og_formant.png")
            tts_img2 = Image.open("tts_formant.png")
            blended_img = Image.blend(og_img2, tts_img2, alpha=0.5)
            blended_img.save("formant_blended.png")

            og_img2.close()
            tts_img2.close()
            os.remove("og_formant.png")
            os.remove("tts_formant.png")

            left = Image.open("ang.png")

            total_width = left.width + blended_img.width
            new_image = Image.new("RGB", (total_width, left.height))
            new_image.paste(left, (0, 0))
            new_image.paste(blended_img, (left.width, 0))
            new_image.save("connected_image.jpg")
            os.remove("formant_blended.png")

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

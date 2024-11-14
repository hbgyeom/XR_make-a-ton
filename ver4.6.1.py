import numpy as np
import queue
import threading
import matplotlib.pyplot as plt
import parselmouth
import speech_recognition as sr
from faster_whisper import WhisperModel
from gtts import gTTS
from PIL import Image
import os

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
    mean_freq = np.mean(freq)
    std_freq = np.std(freq)

    filtered_freq = np.where(freq > mean_freq + 2 * std_freq, 0, freq)
    return np.array(times), np.array(filtered_freq)


def short_seg(times, freq, threshold):
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
    og_voice = parselmouth.Sound(audio_data, 16000)

    og_pitch = og_voice.to_pitch()
    og_times = og_pitch.xs()
    temp = len(og_times)
    og_freq = og_pitch.selected_array['frequency']

    og_times, og_freq = high_seg(og_times, og_freq)
    og_times, og_freq = short_seg(og_times, og_freq, 5)

    nz_indices_og = np.nonzero(og_freq)[0]
    if nz_indices_og.size > 0:
        start_og, end_og = nz_indices_og[0], nz_indices_og[-1] + 1
        og_times = og_times[start_og:end_og]
        og_freq = og_freq[start_og:end_og]

    og_intensity = og_voice.to_intensity()
    og_intensity_times = og_intensity.xs()
    length = len(og_intensity_times)
    og_intensity_times = og_intensity_times[
        length * start_og // temp:length * end_og // temp]
    og_intensity_values = og_intensity.values.T
    og_intensity_values = og_intensity_values[
        length * start_og // temp:length * end_og // temp]

    tts = gTTS(text=text, lang="en")
    tts.save("audio.mp3")

    tts_voice = parselmouth.Sound("audio.mp3")

    tts_pitch = tts_voice.to_pitch()
    tts_times = tts_pitch.xs()
    temp2 = len(tts_times)
    tts_freq = tts_pitch.selected_array['frequency']

    tts_times, tts_freq = high_seg(tts_times, tts_freq)
    tts_times, tts_freq = short_seg(tts_times, tts_freq, 5)

    nz_indices_tts = np.nonzero(tts_freq)[0]
    if nz_indices_tts.size > 0:
        start_tts, end_tts = nz_indices_tts[0], nz_indices_tts[-1] + 1
        tts_times = tts_times[start_tts:end_tts]
        tts_freq = tts_freq[start_tts:end_tts]

    tts_intensity = tts_voice.to_intensity()
    tts_intensity_times = tts_intensity.xs()
    length2 = len(tts_intensity_times)
    tts_intensity_times = tts_intensity_times[
        length2 * start_tts // temp2:length2 * end_tts // temp2]
    tts_intensity_values = tts_intensity.values.T
    tts_intensity_values = tts_intensity_values[
        length2 * start_tts // temp2:length2 * end_tts // temp2]

    os.remove("audio.mp3")

    pitch_return = [og_times, og_freq, tts_times, tts_freq]
    intensity_return = [og_intensity_times, og_intensity_values,
                        tts_intensity_times, tts_intensity_values]

    return pitch_return, intensity_return


def plot_plot(ax, data, top, color, text, scale):
    ax.set_title(f"{text}")
    ax.set_ylim(0, top)
    ax.set_xticks([])
    ax.set_yticks([])

    for i in range(len(data[1]) - 1):
        if abs(data[1][i + 1] - data[1][i]) <= 25:
            ax.plot(data[0][i:i + 2], scale * data[1][i:i + 2],
                    color=color, linestyle='-')
        ax.plot(data[0][i], scale * data[1][i], color=color, markersize=3)


def plot_graph():
    while True:
        plot_data = plot_queue.get()
        audio_data, text = plot_data

        if text == "" or text == ".":
            continue

        pitch_return, intensity_return = process_data(audio_data, text)

        fig1, ax1 = plt.subplots()
        plot_plot(ax1, pitch_return[:2], 350, color='blue', text=text, scale=2)
        plt.savefig("plot1.png", transparent=True,
                    bbox_inches='tight', pad_inches=0)

        fig3, ax3 = plt.subplots()
        plot_plot(ax3, pitch_return[2:], 400, color='red', text=" ", scale=1)
        plt.savefig("plot3.png", transparent=True,
                    bbox_inches='tight', pad_inches=0)

        fig2, ax2 = plt.subplots()
        plot_plot(ax2, intensity_return[:2], max(intensity_return[1]) * 1.1,
                  color='green', text=text, scale=1)
        plt.savefig("plot2.png", transparent=True,
                    bbox_inches='tight', pad_inches=0)

        fig4, ax4 = plt.subplots()
        plot_plot(ax4, intensity_return[2:], max(intensity_return[3]) * 1.1,
                  color='purple', text=" ", scale=1)
        plt.savefig("plot4.png", transparent=True,
                    bbox_inches='tight', pad_inches=0)
        # plt.show()

        img1 = Image.open("plot1.png")
        img3 = Image.open("plot3.png")
        blended_img1 = Image.blend(img1, img3, alpha=0.5)

        img2 = Image.open("plot2.png")
        img4 = Image.open("plot4.png")
        blended_img2 = Image.blend(img2, img4, alpha=0.5)

        width1, height1 = blended_img1.size
        width2, height2 = blended_img2.size
        max_width = max(width1, width2)
        total_height = height1 + height2

        concatenated_image = Image.new('RGB', (max_width, total_height))

        concatenated_image.paste(blended_img1, (0, 0))
        concatenated_image.paste(blended_img2, (0, height1))

        concatenated_image.show()
        concatenated_image.save('concatenated_blended_image.png')


record_thread = threading.Thread(target=record_audio)
transcribe_thread = threading.Thread(target=transcribe_audio)
plot_thread = threading.Thread(target=plot_graph)

record_thread.start()
transcribe_thread.start()
plot_thread.start()

record_thread.join()
transcribe_thread.join()
plot_thread.join()

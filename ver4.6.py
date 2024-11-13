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

# Declare and initialize varible
r = sr.Recognizer()
audio_queue = queue.Queue()
plot_queue = queue.Queue()

# Load model
model = WhisperModel("tiny.en", device="cpu", compute_type="int8")


def record_audio():
    """
    Record audio and add to audio queue
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
    Fetch audio_data from audio_queue and transcribe
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


def short_seg(times, freq, threshold):
    filtered_times = []
    filtered_freq = []
    current_segment_times = []
    current_segment_freq = []

    for i in range(len(freq)):
        if freq[i] != 0:
            # Add to current non-zero segment
            current_segment_times.append(times[i])
            current_segment_freq.append(freq[i])
        else:
            # If zero is encountered, check the current segment length
            if len(current_segment_freq) >= threshold:
                # Keep the segment if it meets the length threshold
                filtered_times.extend(current_segment_times)
                filtered_freq.extend(current_segment_freq)
            # Add the zero value and reset the current segment
            filtered_times.append(times[i])
            filtered_freq.append(freq[i])
            current_segment_times = []
            current_segment_freq = []

    # Handle the last segment if it was non-zero
    if len(current_segment_freq) >= threshold:
        filtered_times.extend(current_segment_times)
        filtered_freq.extend(current_segment_freq)

    return np.array(filtered_times), np.array(filtered_freq)


def process_data(audio_data, text, threshold=5):
    """
    Process audio_data for plotting
    """
    # Load og_voice
    og_voice = parselmouth.Sound(audio_data, 16000)

    # Create pitch data for og_voice
    og_pitch = og_voice.to_pitch()
    og_times = og_pitch.xs()
    og_freq = og_pitch.selected_array['frequency']

    og_times, og_freq = short_seg(og_times, og_freq, 5)

    # Trim leading and trailing zeros in og_freq
    nz_indices_og = np.nonzero(og_freq)[0]
    if nz_indices_og.size > 0:
        start_og, end_og = nz_indices_og[0], nz_indices_og[-1] + 1
        og_times = og_times[start_og:end_og]
        og_freq = og_freq[start_og:end_og]

    # Create intensity data for og_voice
    og_intensity = og_voice.to_intensity()
    og_intensity_times = og_intensity.xs()
    og_intensity_times = og_intensity_times[start_og:end_og]
    og_intensity_values = og_intensity.values.T
    og_intensity_values = og_intensity_values[start_og:end_og]

    # Generate TTS audio
    tts = gTTS(text=text, lang="en")
    tts.save("audio.mp3")

    # Load tts_voice
    tts_voice = parselmouth.Sound("audio.mp3")

    # Create pitch data for tts_voice
    tts_pitch = tts_voice.to_pitch()
    tts_times = tts_pitch.xs()
    tts_freq = tts_pitch.selected_array['frequency']

    tts_times, tts_freq = short_seg(tts_times, tts_freq, 5)

    # Trim leading and trailing zeros in tts_freq
    nz_indices_tts = np.nonzero(tts_freq)[0]
    if nz_indices_tts.size > 0:
        start_tts, end_tts = nz_indices_tts[0], nz_indices_tts[-1] + 1
        tts_times = tts_times[start_tts:end_tts]
        tts_freq = tts_freq[start_tts:end_tts]

    # Create intensity data for tts_voice
    tts_intensity = tts_voice.to_intensity()
    tts_intensity_times = tts_intensity.xs()
    tts_intensity_times = tts_intensity_times[start_tts:end_tts]
    tts_intensity_values = tts_intensity.values.T
    tts_intensity_values = tts_intensity_values[start_tts:end_tts]

    os.remove("audio.mp3")

    pitch_return = [og_times, og_freq, tts_times, tts_freq]
    intensity_return = [og_intensity_times, og_intensity_values,
                        tts_intensity_times, tts_intensity_values]

    return pitch_return, intensity_return


def plot_graph():
    """
    Plot data for pitch and intensity
    """
    while True:
        plot_data = plot_queue.get()
        audio_data, text = plot_data

        if text == "" or text == ".":
            continue

        # Process data
        pitch_return, intensity_return = process_data(audio_data, text)

        # Original Voice Pitch Plot
        fig1, ax1 = plt.subplots()
        ax1.set_title(f"Original Voice Pitch - {text}")
        ax1.set_ylim(0, 500)
        ax1.set_xticks([])
        ax1.set_yticks([])
        for i in range(len(pitch_return[1]) - 1):
            if abs(pitch_return[1][i + 1] - pitch_return[1][i]) <= 25:
                ax1.plot(pitch_return[0][i:i + 2], 2*pitch_return[1][i:i + 2],
                         color='blue', linestyle='-')
            ax1.plot(pitch_return[0][i], 2*pitch_return[1][i], color='blue',
                     markersize=3)
        plt.savefig("plot1.png", transparent=True, bbox_inches='tight',
                    pad_inches=0)

        # Original Voice Intensity Plot
        fig2, ax2 = plt.subplots()
        ax2.set_title(f"Original Voice Intensity - {text}")
        ax2.set_ylim(0, max(intensity_return[1]) * 1.1)
        ax2.set_xticks([])
        ax2.set_yticks([])
        for i in range(len(intensity_return[1]) - 1):
            if abs(intensity_return[1][i + 1] - intensity_return[1][i]) <= 25:
                ax2.plot(intensity_return[0][i:i + 2],
                         intensity_return[1][i:i + 2], color='green',
                         linestyle='-')
            ax2.plot(intensity_return[0][i], intensity_return[1][i],
                     color='green', markersize=3)
        plt.savefig("plot2.png", transparent=True, bbox_inches='tight',
                    pad_inches=0)

        # TTS Voice Pitch Plot
        fig3, ax3 = plt.subplots()
        ax3.set_title(f"TTS Voice Pitch - {text}")
        ax3.set_ylim(0, 500)
        ax3.set_xticks([])
        ax3.set_yticks([])
        for i in range(len(pitch_return[3]) - 1):
            if abs(pitch_return[3][i + 1] - pitch_return[3][i]) <= 25:
                ax3.plot(pitch_return[2][i:i + 2], pitch_return[3][i:i + 2],
                         color='red', linestyle='-')
            ax3.plot(pitch_return[2][i], pitch_return[3][i], color='red',
                     markersize=3)
        plt.savefig("plot3.png", transparent=True, bbox_inches='tight',
                    pad_inches=0)

        # TTS Voice Intensity Plot
        fig4, ax4 = plt.subplots()
        ax4.set_title(f"TTS Voice Intensity - {text}")
        ax4.set_ylim(0, max(intensity_return[3]) * 1.1)
        ax4.set_xticks([])
        ax4.set_yticks([])
        for i in range(len(intensity_return[3]) - 1):
            if abs(intensity_return[3][i + 1] - intensity_return[3][i]) <= 25:
                ax4.plot(intensity_return[2][i:i + 2],
                         intensity_return[3][i:i + 2], color='purple',
                         linestyle='-')
            ax4.plot(intensity_return[2][i], intensity_return[3][i],
                     color='purple', markersize=3)
        plt.savefig("plot4.png", transparent=True, bbox_inches='tight',
                    pad_inches=0)

        # Display all figures
        # plt.show()

        img1 = Image.open("plot1.png")
        img3 = Image.open("plot3.png")
        blended_img1 = Image.blend(img1, img3, alpha=0.5)
        blended_img1.show()

        img2 = Image.open("plot2.png")
        img4 = Image.open("plot4.png")
        blended_img2 = Image.blend(img2, img4, alpha=0.5)
        blended_img2.show()


# Threading
record_thread = threading.Thread(target=record_audio)
transcribe_thread = threading.Thread(target=transcribe_audio)
plot_thread = threading.Thread(target=plot_graph)

record_thread.start()
transcribe_thread.start()
plot_thread.start()

record_thread.join()
transcribe_thread.join()
plot_thread.join()

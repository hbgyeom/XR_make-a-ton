import parselmouth
import numpy as np
import matplotlib.pyplot as plt
from gtts import gTTS
from PIL import Image

# target = "C:/Users/HBG/codes/tp/F/F03/Session3/wav_arrayMic/0052.wav"
target = "C:/Users/HBG/Desktop/0019.wav"
text = "This was easy for us."


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


def high_seg(times, freq):
    mean_freq = np.mean(freq)
    std_freq = np.std(freq)

    filtered_freq = np.where(freq > mean_freq + 2 * std_freq, 0, freq)
    return np.array(times), np.array(filtered_freq)


og_voice = parselmouth.Sound(target)

og_pitch = og_voice.to_pitch()
og_times = og_pitch.xs()
og_freq = og_pitch.selected_array['frequency']

og_times, og_freq = high_seg(og_times, og_freq)
og_times, og_freq = short_seg(og_times, og_freq, 10)

nz_indices_og = np.nonzero(og_freq)[0]
if nz_indices_og.size > 0:
    start_og, end_og = nz_indices_og[0], nz_indices_og[-1] + 1
    og_times = og_times[start_og:end_og]
    og_freq = og_freq[start_og:end_og]

og_intensity = og_voice.to_intensity()
og_intensity_times = og_intensity.xs()
# og_intensity_times = og_intensity_times[start_og:end_og]
og_intensity_values = og_intensity.values.T
# og_intensity_values = og_intensity_values[start_og:end_og]

tts = gTTS(text=text, lang="en")
tts.save("audio.mp3")

tts_voice = parselmouth.Sound("audio.mp3")

tts_pitch = tts_voice.to_pitch()
tts_times = tts_pitch.xs()
tts_freq = tts_pitch.selected_array['frequency']

tts_times, tts_freq = high_seg(tts_times, tts_freq)
tts_times, tts_freq = short_seg(tts_times, tts_freq, 10)

nz_indices_tts = np.nonzero(tts_freq)[0]
if nz_indices_tts.size > 0:
    start_tts, end_tts = nz_indices_tts[0], nz_indices_tts[-1] + 1
    tts_times = tts_times[start_tts:end_tts]
    tts_freq = tts_freq[start_tts:end_tts]

tts_intensity = tts_voice.to_intensity()
tts_intensity_times = tts_intensity.xs()
# tts_intensity_times = tts_intensity_times[start_tts:end_tts]
tts_intensity_values = tts_intensity.values.T
# tts_intensity_values = tts_intensity_values[start_tts:end_tts]

pitch_return = [og_times, og_freq, tts_times, tts_freq]
intensity_return = [og_intensity_times, og_intensity_values,
                    tts_intensity_times, tts_intensity_values]

fig1, ax1 = plt.subplots()
ax1.set_title(f"Original Voice Pitch - {text}")
ax1.set_ylim(0, 500)
ax1.set_xticks([])
ax1.set_yticks([])
for i in range(len(pitch_return[1]) - 1):
    if abs(pitch_return[1][i + 1] - pitch_return[1][i]) <= 25:
        ax1.plot(pitch_return[0][i:i + 2], pitch_return[1][i:i + 2],
                 color='blue', linestyle='-')
    ax1.plot(pitch_return[0][i], pitch_return[1][i], color='blue',
             markersize=3)
plt.savefig("plot1.png", bbox_inches='tight',
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
plt.savefig("plot2.png", bbox_inches='tight',
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
plt.savefig("plot3.png", bbox_inches='tight',
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
plt.savefig("plot4.png", bbox_inches='tight',
            pad_inches=0)

# Display all figures
plt.show()

img1 = Image.open("plot1.png")
img3 = Image.open("plot3.png")
blended_img1 = Image.blend(img1, img3, alpha=0.5)
blended_img1.show()

img2 = Image.open("plot2.png")
img4 = Image.open("plot4.png")
blended_img2 = Image.blend(img2, img4, alpha=0.5)
blended_img2.show()

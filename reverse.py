import slab
import os
import pathlib
import numpy as np
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt

SAMPLERATE = 40000
slab.Signal.set_default_samplerate(SAMPLERATE)
DIR = pathlib.Path(os.getcwd())
root_dir = DIR / "samples" / "CRM" / "original"
files = os.listdir(root_dir)
segments = [20, 40, 60, 80, 100, 120, 140]
modulation_type = "helicopter"

for file in files:
    file_path = pathlib.Path(root_dir / file)
    sound = slab.Binaural(file_path)
    for segment_length_ms in segments:
        segment_length = slab.Signal.in_samples(segment_length_ms / 1000, sound.samplerate)
        overlap = int(0.001 * SAMPLERATE)
        reversed_sound = slab.Binaural.silence(duration=sound.n_samples, samplerate=sound.samplerate)
        border_range = np.arange(-overlap, overlap + 1)
        idx = 0
        noise_idx = 0
        while idx < sound.n_samples:
            start = idx
            end = idx + segment_length
            snippet = sound.data[start:end]
            reversed_snippet = slab.Binaural(snippet[::-1], samplerate=sound.samplerate)
            reversed_sound.data[start:end] += reversed_snippet
            idx += segment_length
            # if len(border_range) < idx < sound.n_samples - len(border_range):
                # plot_range = np.arange(-overlap*3, overlap*3 + 1)
                # plt.plot(plot_range, out.data[idx + plot_range, 0], label="original", linewidth=3.0)
                #
                # border_l = out.data[idx + border_range, 0]
                # border_r = out.data[idx + border_range, 1]
                # yhat_l = savgol_filter(border_l, len(border_l), 7)
                # yhat_r = savgol_filter(border_r, len(border_r), 7)
                # out.data[idx + border_range, 0] = yhat_l
                # out.data[idx + border_range, 1] = yhat_r
                # plt.plot(plot_range, out.data[idx + plot_range, 0], label="border-savgol")

                # noise = slab.Binaural.pinknoise(duration=len(border_range))
                # noise = noise.ramp(duration=overlap)
                # out.data[idx + border_range, 0] = noise[:, 0]
                # out.data[idx + border_range, 1] = noise[:, 1]
                # plt.plot(plot_range, out.data[idx + plot_range, 0], label="border-noise", alpha=0.7)
                # plt.axvspan(border_range[0], border_range[-1], facecolor='0.2', alpha=0.1)
                # plt.legend()
                # plt.show()
        out = slab.Binaural.silence(duration=overlap + reversed_sound.n_samples, samplerate=SAMPLERATE)
        out.data[overlap:] = reversed_sound.data
        noise = slab.Binaural.pinknoise(duration=len(border_range), kind="dichotic").ramp(duration=overlap)
        while noise_idx < out.n_samples - noise.n_samples:
            start = noise_idx
            end = noise_idx + noise.n_samples
            out.data[start:end, 0] = noise[:, 0]
            out.data[start:end, 1] = noise[:, 1]
            noise_idx += int(0.02 * SAMPLERATE)
        out.left = out.left.filter(frequency=8000, kind="lp")
        out.right = out.right.filter(frequency=8000, kind="lp")
        outdir = file_path.parent.parent / modulation_type / str(str(segment_length_ms) + "ms" + "_" + modulation_type)
        pathlib.Path(outdir).mkdir(parents=True, exist_ok=True)
        outfilename = outdir / str(file_path.stem + "_seg-" + str(segment_length_ms) + "ms" + "_" + modulation_type + ".wav")
        out.write(outfilename)


import slab
import os
import pathlib
import numpy as np
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt

DIR = pathlib.Path(os.getcwd())
root_dir = DIR / "samples" / "CRM" / "original"
files = os.listdir(root_dir)
segments = [25, 50, 75, 100, 150, 200]

for file in files:
    file_path = pathlib.Path(root_dir / file)
    sound = slab.Binaural(file_path)
    for segment_length_ms in segments:
        segment_length = slab.Signal.in_samples(segment_length_ms / 1000, sound.samplerate)
        overlap = int(0.1 * segment_length)
        out = slab.Binaural.silence(duration=sound.duration, samplerate=sound.samplerate)
        border_range = np.arange(-overlap, overlap + 1)
        idx = 0
        while idx < sound.n_samples:
            start = idx
            end = idx + segment_length
            snippet = sound.data[start:end]
            reversed_snippet = slab.Binaural(snippet[::-1], samplerate=sound.samplerate)
            out.data[start:end] += reversed_snippet
            if len(border_range) < idx < sound.n_samples - len(border_range):
                border_l = out.data[idx + border_range, 0]
                border_r = out.data[idx + border_range, 1]
                yhat_l = savgol_filter(border_l, len(border_l), 7)
                yhat_r = savgol_filter(border_r, len(border_r), 7)
                out.data[idx + border_range, 0] = yhat_l
                out.data[idx + border_range, 1] = yhat_r
            idx += segment_length
        out.filter(frequency=8000, kind="lp")
        outdir = file_path.parent.parent / str(str(segment_length_ms) + "ms" + "_raw")
        pathlib.Path(outdir).mkdir(parents=True, exist_ok=True)
        outfilename = outdir / str(file_path.stem + "_seg-" + str(segment_length_ms) + "ms" + ".wav")
        out.write(outfilename)


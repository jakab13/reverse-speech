import slab
import pathlib
import os
from utils import get_file_paths

SAMPLERATE = 48828
slab.Signal.set_default_samplerate(SAMPLERATE)
DIR = pathlib.Path(os.getcwd())


stim_dir = DIR / 'samples' / 'CRM' / 'original'
out_dir = DIR / 'samples' / 'CRM' / f'original_resamp-{SAMPLERATE}'
file_paths = sorted([f for f in get_file_paths(stim_dir)])
sounds = [slab.Sound(f) for f in file_paths]
max_n_samples = max([sound.n_samples for sound in sounds])

for file_path in file_paths:
    sound = slab.Sound(file_path)
    silence_n_samples = max_n_samples - sound.n_samples
    silence = slab.Sound.silence(duration=silence_n_samples, samplerate=sound.samplerate)
    out_sound = slab.Sound.sequence(sound, silence)
    out_sound = out_sound.resample(samplerate=SAMPLERATE)
    out_filename = str(file_path.name) + f"_resamp-{SAMPLERATE}.wav"
    out_sound.write(out_dir / out_filename)
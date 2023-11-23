import slab
import os
import pathlib
import random
import numpy as np
import tkinter
from tkmacosx import Button
from functools import partial
from config import *
import pyloudnorm as pyln
import pickle

SAMPLERATE = 40000
meter = pyln.Meter(SAMPLERATE, block_size=0.200)

DIR = pathlib.Path(os.getcwd())
root_dir = DIR / "samples" / "CRM"


def get_file_paths(directory):
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            if not f.startswith('.'):
                yield pathlib.Path(os.path.join(dirpath, f))


def create_name(talker, call_sign, colour, number):
    base_string = talker + call_sign + colour + number
    name = base_string
    return name


def name_to_int(name):
    return int(name[-1]) + 1


def value_to_key(dictionary, value):
    return list(dictionary.keys())[list(NUMBERS.values()).index(value)]


def normalise_sound(sound):
    loudness = meter.integrated_loudness(sound.data)
    normalised_sound = slab.Binaural(pyln.normalize.loudness(sound.data, loudness, -20))
    return normalised_sound

def get_stimulus(params):
    talker, call_sign, colour, number, segment_length = \
        params["talker"], params["call_sign"], params["colour"], params["number"], params["segment_length"]
    file_name = create_name(talker, call_sign, colour, number)
    path = root_dir / "original" / str(file_name + ".wav")
    stimulus = slab.Binaural(path)
    return stimulus


def get_gender_mix(gender1, gender2):
    if gender1 == gender2:
        mix = gender1
    else:
        mix = "opposite"
    return mix


def get_params(stim_type="target", filter_params=None):
    global THIS_TRIAL
    params = {"stim_type": stim_type}
    # segment_length = seq.get_future_trial(THIS_TRIAL)
    segment_length = random.choice(SEGMENT_LENGTHS)
    if isinstance(filter_params, dict) and "gender" in filter_params:
        gender = filter_params["gender"]
        talker, _ = random.choice([(k, v) for (k, v) in TALKERS.items() if v == gender])
    else:
        talker, gender = random.choice(list(TALKERS.items()))
    if stim_type == "target":
        call_sign = CALL_SIGN_TARGET  # Baron
        segment_length = TARGET_SEGMENT_LENGTH
    elif stim_type == "random":
        call_sign = random.choice(list(CALL_SIGNS.values()))
    else:
        call_sign = random.choice([cs_id for (cs, cs_id) in CALL_SIGNS.items() if cs != "Baron"])
    colour = random.choice(list(COLOURS.values()))
    number = random.choice([num_string for num_name, num_string in NUMBERS.items() if num_name != "Seven"])
    params["talker"] = talker
    params["gender"] = gender
    params["call_sign"] = call_sign
    params["colour"] = colour
    params["number"] = number
    params["segment_length"] = segment_length
    return params


def random_stimulus():
    params = get_params()
    stimulus = get_stimulus(params)
    return stimulus, params


def save_ILS():
    hrtf = slab.hrtf.HRTF.kemar()
    ils = slab.Binaural.make_interaural_level_spectrum(hrtf)
    pickle.dump(ils, open('ils.pickle', 'wb'))  # save using pickle


def reverse_sound(sound, segment_length=None, overlap=0.005, split_channels=False):
    if segment_length is None:
        sound.data = sound.data[::-1]
        return sound
    elif segment_length == 0:
        return sound
    segment_length = slab.Signal.in_samples(segment_length, sound.samplerate)
    overlap = int(overlap * sound.samplerate)
    reversed_sound = slab.Binaural.silence(duration=sound.n_samples, samplerate=sound.samplerate)
    idx = random.randrange(segment_length) - segment_length
    segment_counter = 0
    while idx < sound.n_samples:
        start = max(idx - overlap, 0)
        end = min(idx + segment_length + overlap, sound.n_samples)
        snippet = sound.data[start:end]
        reversed_snippet = slab.Binaural(snippet[::-1], samplerate=sound.samplerate)
        if reversed_snippet.n_samples > overlap * 2:
            reversed_snippet = reversed_snippet.ramp(duration=overlap)
        if split_channels:
            chan = segment_counter % 2
            reversed_sound.data[start:end, chan] += reversed_snippet[:, chan]
        else:
            reversed_sound.data[start:end] += reversed_snippet
        idx += segment_length
        segment_counter += 1
    reversed_sound = reversed_sound.ramp(duration=overlap, when="offset")
    reversed_sound.left = reversed_sound.left.filter(frequency=8000, kind="lp")
    reversed_sound.right = reversed_sound.right.filter(frequency=8000, kind="lp")
    return reversed_sound


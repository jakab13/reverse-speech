import slab
import pathlib
import os
import pandas as pd
import numpy as np
from config import *

SAMPLERATE = 40000
slab.Signal.set_default_samplerate(SAMPLERATE)
DIR = pathlib.Path(os.getcwd())

COLUMN_NAMES = [
    "filename",
    "talker_id",
    "talker_gender",
    "call_sign",
    "call_sign_id",
    "colour",
    "colour_id",
    "number",
    "number_id",
    "duration",
    "RMS",
    "centroid",
    "flatness"
]


def get_file_paths(directory):
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            if not f.startswith('.'):
                yield pathlib.Path(os.path.join(dirpath, f))


def get_from_file_name(file_path, param):
    file_name = file_path.name
    match param:
        case "talker_id":
            param_idx = [0, 2]
        case "call_sign_id":
            param_idx = [2, 4]
        case "colour_id":
            param_idx = [4, 6]
        case "number_id":
            param_idx = [6, 8]
    sub_string = file_name[param_idx[0]:param_idx[1]]
    return sub_string


def id_to_name(id, param):
    match param:
        case "talker":
            name = TALKERS[id]
        case "call_sign":
            name = [k for k, v in CALL_SIGNS.items() if v == id][0]
        case "colour":
            name = [k for k, v in COLOURS.items() if v == id][0]
        case "number":
            name = [k for k, v in NUMBERS.items() if v == id][0]
    return name


def get_spectral_feature(sound, feature_name):
    feature = np.asarray(sound.spectral_feature(feature_name, mean="rms"))
    return feature.mean()


stim_dir = DIR / 'samples' / 'CRM' / 'original'
file_paths = sorted([f for f in get_file_paths(stim_dir)])
features = {f.name: {} for f in get_file_paths(stim_dir)}

for file_path in file_paths:
    sound = slab.Sound(file_path)
    talker_id = get_from_file_name(file_path, "talker_id")
    call_sign_id = get_from_file_name(file_path, "call_sign_id")
    colour_id = get_from_file_name(file_path, "colour_id")
    number_id = get_from_file_name(file_path, "number_id")
    centroid = get_spectral_feature(sound, "centroid")
    flatness = get_spectral_feature(sound, "flatness")
    features[file_path.name] = {
        "filename": file_path.name,
        "talker_id": talker_id,
        "talker_gender": id_to_name(talker_id, "talker"),
        "call_sign_id": call_sign_id,
        "call_sign": id_to_name(call_sign_id, "call_sign"),
        "colour_id": colour_id,
        "colour": id_to_name(colour_id, "colour"),
        "number_id": number_id,
        "number": id_to_name(number_id, "number"),
        "duration": sound.duration,
        "RMS": sound.level.mean(),
        "centroid": centroid,
        "flatness": flatness * 1000000
    }


df = pd.DataFrame.from_dict(features, columns=COLUMN_NAMES, orient="index")
df = df.sort_values('filename')
df = df.round(decimals=5)
df.to_csv(f'stim_features.csv')
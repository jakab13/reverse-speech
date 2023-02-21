import slab
import os
import pathlib
import random
import numpy as np
import tkinter
# from tkmacosx import Button
from functools import partial
from config import *
import pyloudnorm as pyln

DIR = pathlib.Path(os.getcwd())
root_dir = DIR / "samples" / "CRM"
SAMPLERATE = 40000
slab.set_default_samplerate(SAMPLERATE)
meter = pyln.Meter(SAMPLERATE, block_size=0.200)


def create_name(talker, call_sign, colour, number):
    base_string = talker + call_sign + colour + number
    name = base_string
    return name


def name_to_int(name):
    return int(name[-1]) + 1


def value_to_key(dictionary, value):
    return list(dictionary.keys())[list(numbers.values()).index(value)]


def normalise_sound(sound):
    loudness = meter.integrated_loudness(sound.data)
    normalised_sound = slab.Binaural(pyln.normalize.loudness(sound.data, loudness, -20))
    return normalised_sound


subject_ID = 'test'
channel_setup_seq = slab.Trialsequence(["mono", "left", "right"], n_reps=22)
# channel_setup_seq = slab.Trialsequence(["left_target", "right_target"], n_reps=22)
slab.ResultsFile.results_folder = 'results'
results_file = slab.ResultsFile()
seq = slab.Trialsequence(segment_lengths, n_reps=5)
THIS_TRIAL = 0
CALL_SIGN = None
task = dict()
master = tkinter.Tk()
master.title("Responses")
master.geometry("800x500")
myFont = tkinter.font.Font(size=20)


def generate_helicopter(duration=1.0, spike_width=0.005, segment_length=0.02, samplerate=44100, spike_idx_array=None):
    duration = slab.Signal.in_samples(duration, samplerate=samplerate)
    spike_width = slab.Signal.in_samples(spike_width, samplerate=samplerate)
    spike_half_width = int(spike_width/2)
    segment_length = slab.Signal.in_samples(segment_length, samplerate=samplerate)
    spike = slab.Binaural.pinknoise(duration=spike_width)
    spike = spike.ramp(duration=int(spike_width/2)-1)
    helicopter = slab.Binaural.silence(duration=duration)
    if spike_idx_array is None:
        spike_idx_array = range(segment_length, duration - segment_length, segment_length)
    else:
        spike_idx_array = [idx for idx in spike_idx_array if idx < duration-segment_length]
    for spike_idx in spike_idx_array:
        start = spike_idx - spike_half_width
        end = spike_idx + spike_half_width
        helicopter.data[start:end] = spike.data
    return helicopter


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
    segment_length = seq.get_future_trial(THIS_TRIAL)
    if isinstance(filter_params, dict) and "gender" in filter_params:
        gender = filter_params["gender"]
        talker, _ = random.choice([(k, v) for (k, v) in talkers.items() if v == gender])
    else:
        talker, gender = random.choice(list(talkers.items()))
    if stim_type == "target":
        call_sign = call_sign_target  # Baron
        segment_length = target_segment_length
    elif stim_type == "random":
        call_sign = random.choice(list(call_signs.values()))
    else:
        call_sign = random.choice([cs_id for (cs, cs_id) in call_signs.items() if cs != "Baron"])
    colour = random.choice(list(colours.values()))
    number = random.choice([num_string for num_name, num_string in numbers.items() if num_name != "Seven"])
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


def reverse_sound(sound, segment_length):
    segment_length = slab.Signal.in_samples(segment_length, sound.samplerate)
    overlap = int(0.005 * sound.samplerate)
    reversed_sound = slab.Binaural.silence(duration=sound.n_samples, samplerate=sound.samplerate)
    idx = 0
    while idx < sound.n_samples:
        start = idx - overlap if idx > overlap else idx
        end = idx + segment_length + overlap if idx < sound.n_samples - segment_length - overlap else sound.n_samples
        snippet = sound.data[start:end]
        reversed_snippet = slab.Binaural(snippet[::-1], samplerate=sound.samplerate)
        if reversed_snippet.n_samples > overlap * 2:
            reversed_snippet = reversed_snippet.ramp(duration=overlap)
        reversed_sound.data[start:end] += reversed_snippet
        idx += segment_length
    reversed_sound = reversed_sound.ramp(duration=overlap, when="offset")
    reversed_sound.left = reversed_sound.left.filter(frequency=8000, kind="lp")
    reversed_sound.right = reversed_sound.right.filter(frequency=8000, kind="lp")
    return reversed_sound


def combine_sounds(target, masker, add_helicopter=False):
    max_duration = max([masker.n_samples, target.n_samples])
    combined = slab.Binaural.silence(duration=max_duration, samplerate=target.samplerate)
    combined.data[:target.n_samples] = target.data
    combined.data[:masker.n_samples] += masker.data
    if add_helicopter:
        helicopter = generate_helicopter(duration=max_duration, segment_length=min(segment_lengths), samplerate=target.samplerate)
        combined.data += helicopter
    combined = normalise_sound(combined)
    return combined


def select_channels(target, masker, channel_setup="mono"):
    target.level += target_level_diff
    max_duration = max([masker.n_samples, target.n_samples])
    sound_channeled = slab.Binaural.silence(duration=max_duration, samplerate=target.samplerate)
    if channel_setup == "mono":
        sound_channeled = combine_sounds(target, masker)
    elif channel_setup == "left":
        combined = combine_sounds(target, masker)
        sound_channeled.data[:, 0] = combined.data[:, 0]
    elif channel_setup == "right":
        combined = combine_sounds(target, masker)
        sound_channeled.data[:, 1] = combined.data[:, 1]
    elif channel_setup == "left_target":
        sound_channeled.data[:target.n_samples, 0] = target.data[:, 0]
        sound_channeled.data[:masker.n_samples, 1] = masker.data[:, 1]
    elif channel_setup == "right_target":
        sound_channeled.data[:target.n_samples, 1] = target.data[:, 1]
        sound_channeled.data[:masker.n_samples, 0] = masker.data[:, 0]
    sound_channeled = normalise_sound(sound_channeled)
    return sound_channeled


def get_score(response, task):
    score = 0
    if "response_call_sign" in response:
        denum = len(call_signs) + len(colours) + len(numbers) - 1
        if response["response_call_sign"] == task["task_call_sign"]:
            score += len(call_signs) / denum
    else:
        denum = len(colours) + len(numbers) - 1
    if response["response_colour"] == task["task_colour"]:
        score += len(colours) / denum
    if response["response_number"] == task["task_number"]:
        score += (len(numbers) - 1) / denum
    return score


def run_masking_trial(response=None):
    global THIS_TRIAL
    global task
    if response is not None:
        response["score"] = get_score(response, task)
        results_file.write(response, tag="response")
        if THIS_TRIAL <= seq.n_trials:
            print(THIS_TRIAL - 1, "Response:", response["response_colour"], response["response_number"])
            print('')
    if THIS_TRIAL <= seq.n_trials:
        master.update()
    else:
        master.destroy()
    channel_setup = channel_setup_seq.get_future_trial(THIS_TRIAL)
    target_params = get_params(stim_type="target")
    masker_params = get_params(stim_type="masker")
    target = get_stimulus(target_params)
    target = reverse_sound(target, target_params["segment_length"])
    masker = get_stimulus(masker_params)
    masker = reverse_sound(masker, masker_params["segment_length"])
    output = select_channels(target, masker, channel_setup=channel_setup)
    task = {
        "subject_ID": subject_ID,
        "target_segment_length": target_segment_length,
        "masker_segment_length": masker_params["segment_length"],
        "channel_setup": channel_setup,
        "target_talker": target_params["talker"],
        "target_gender": target_params["gender"],
        "masker_talker": masker_params["talker"],
        "masker_gender": masker_params["gender"],
        "gender_mix": get_gender_mix(target_params["gender"], masker_params["gender"]),
        "masker_call_sign": value_to_key(call_signs, masker_params["call_sign"]),
        "task_colour": value_to_key(colours, target_params["colour"]),
        "task_number": value_to_key(numbers, target_params["number"]),
        "target_level_diff": target_level_diff
    }
    results_file.write(task, tag="task")
    print(THIS_TRIAL, "Task:    ", task["task_colour"], task["task_number"])
    output.play()
    THIS_TRIAL += 1


def run_single_talker_trial(response=None):
    global THIS_TRIAL
    global CALL_SIGN
    global task
    if response is not None:
        response["response_call_sign"] = CALL_SIGN
        response["score"] = get_score(response, task)
        results_file.write(response, tag="response")
        if THIS_TRIAL <= seq.n_trials:
            print(THIS_TRIAL - 1, "Response:", CALL_SIGN, response["response_colour"], response["response_number"])
            print('')
    if THIS_TRIAL <= seq.n_trials:
        master.update()
    else:
        master.destroy()
        return
    single_talker_params = get_params(stim_type="random")
    single_talker = get_stimulus(single_talker_params)
    single_talker = reverse_sound(single_talker, single_talker_params["segment_length"])
    task = {
        "subject_ID": subject_ID,
        "single_talker_segment_length": single_talker_params["segment_length"],
        "single_talker": single_talker_params["talker"],
        "single_talker_gender": single_talker_params["gender"],
        "task_call_sign": value_to_key(call_signs, single_talker_params["call_sign"]),
        "task_colour": value_to_key(colours, single_talker_params["colour"]),
        "task_number": value_to_key(numbers, single_talker_params["number"])
    }
    results_file.write(task, tag="task")
    print(THIS_TRIAL, "Task:    ", task["task_call_sign"], task["task_colour"], task["task_number"])
    single_talker.play()
    THIS_TRIAL += 1


def set_call_sign(call_sign):
    global CALL_SIGN
    CALL_SIGN = call_sign


def generate_numpad():
    buttons = [[0 for x in range(len(numbers))] for y in range(len(colours))]
    for column, c_name in enumerate(colours):
        for row, n_name in enumerate(numbers):
            response_params = {"response_colour": c_name, "response_number": n_name}
            button_text = name_to_int(numbers[n_name])
            buttons[column][row] = tkinter.Button(master,
                                          text=str(button_text),
                                          bg=col_to_hex[c_name],
                                          command=partial(run_masking_trial, response_params))
            buttons[column][row]['font'] = myFont
            buttons[column][row].grid(row=row, column=column)


def generate_name_and_numpad():
    buttons = [[0 for x in range(len(numbers))] for y in range(len(colours) + 1)]
    for row, call_sign in enumerate(call_signs):
        buttons[0][row] = tkinter.Button(master,
                                 text=call_sign,
                                         command=partial(set_call_sign, call_sign))
        buttons[0][row]['font'] = myFont
        buttons[0][row].grid(row=row, column=0)
    for column, c_name in enumerate(colours):
        for row, n_name in enumerate(numbers):
            response_params = {"response_colour": c_name, "response_number": n_name}
            button_text = name_to_int(numbers[n_name])
            buttons[column + 1][row] = tkinter.Button(master,
                                              text=str(button_text),
                                              bg=col_to_hex[c_name],
                                                      command=partial(run_single_talker_trial, response_params))
            buttons[column + 1][row]['font'] = myFont
            buttons[column + 1][row].grid(row=row, column=column + 1)


def run_masking_experiment():
    global THIS_TRIAL
    global results_file
    results_filename = "multi-talker"
    results_filename += "_target-segment-" + str(int(target_segment_length * 1000)) + "ms"
    results_filename += "_SNR-" + str(target_level_diff) + "dB"
    results_file = slab.ResultsFile(subject=subject_ID, filename=results_filename)
    THIS_TRIAL = 1
    generate_numpad()
    run_masking_trial()
    master.mainloop()


def run_single_talker_experiment():
    global THIS_TRIAL
    THIS_TRIAL = 1
    global results_file
    results_filename = "single-talker"
    results_file = slab.ResultsFile(subject=subject_ID, filename=results_filename)
    generate_name_and_numpad()
    run_single_talker_trial()
    master.mainloop()


run_masking_experiment()
# run_single_talker_experiment()


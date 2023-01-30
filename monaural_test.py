import slab
import os
import pathlib
import random
import numpy as np
import tkinter
from tkmacosx import Button
from functools import partial
from config import call_sign_target, call_signs, colours, numbers, talkers, col_to_hex, segment_lengths

DIR = pathlib.Path(os.getcwd())
root_dir = DIR / "samples" / "CRM"


def create_name(talker, call_sign, colour, number):
    base_string = talker + call_sign + colour + number
    name = base_string
    return name


def name_to_int(name):
    return int(name[-1]) + 1


def value_to_key(dictionary, value):
    return list(dictionary.keys())[list(numbers.values()).index(value)]


def normalise_sound(sound):
    sound.data = sound.data / np.max(sound.data)
    return sound


subject_ID = 'jakab'
slab.ResultsFile.results_folder = 'results'
results_file = slab.ResultsFile(subject=subject_ID)
seq = slab.Trialsequence(segment_lengths, n_reps=10)
target_level_diff = -9
THIS_TRIAL = 0
task = dict()

master = tkinter.Tk()
master.title("Responses")
master.geometry("800x500")
myFont = tkinter.font.Font(size=30)


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
    if params["stim_type"] == "target":
        path = root_dir / "original" / str(file_name + '.wav')
    else:
        path = root_dir / "reversed" / str(str(segment_length) + "ms_reversed") / str(file_name + "_seg-" + str(segment_length) + "ms" + "_reversed" + '.wav')
    stimulus = slab.Binaural(path)
    stimulus = normalise_sound(stimulus)
    return stimulus


def get_params(stim_type="target"):
    params = {"stim_type": stim_type}
    talker, gender = random.choice(list(talkers.items()))
    if stim_type == "target":
        call_sign = call_sign_target  # Baron
        segment_length = segment_lengths[0]
    else:
        call_sign = random.choice([cs_id for (cs, cs_id) in call_signs.items() if cs != "Baron"])
        segment_length = random.choice(segment_lengths)
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

def combine_sounds(target, masker, add_helicopter=True):
    max_duration = max([masker.n_samples, target.n_samples])
    combined = slab.Binaural.silence(duration=max_duration, samplerate=target.samplerate)
    combined.data[:target.n_samples] = target.data
    combined.data[:masker.n_samples] += masker.data
    if add_helicopter:
        helicopter = generate_helicopter(duration=max_duration, samplerate=target.samplerate)
        combined.data += helicopter
    combined = normalise_sound(combined)
    return combined


def run_masking_trial(event=None, add_helicopter=True):
    global THIS_TRIAL
    global task
    if event is not None:
        is_correct = False
        if event["colour"] == task["colour"] and event["number"] == task["number"]:
            is_correct = True
        event["is_correct"] = is_correct
        results_file.write(event, tag="response")
        print(THIS_TRIAL - 1, "Response:", event["colour"], event["number"])
        print('')
    master.update()
    target_params = get_params(stim_type="target")
    masker_params = get_params(stim_type="masker")
    target = get_stimulus(target_params)
    masker = get_stimulus(masker_params)
    target.level += target_level_diff
    combined = combine_sounds(target, masker, add_helicopter=add_helicopter)
    task = {
        "segment_length": masker_params["segment_length"],
        "target_talker": target_params["talker"],
        "target_gender": target_params["gender"],
        "masker_talker": masker_params["talker"],
        "masker_gender": masker_params["gender"],
        "masker_call_sign": value_to_key(call_signs, masker_params["call_sign"]),
        "colour": value_to_key(colours, target_params["colour"]),
        "number": value_to_key(numbers, target_params["number"]),
        "target_level_diff": target_level_diff
    }
    results_file.write(THIS_TRIAL, tag="trial_num")
    results_file.write(task, tag="task")
    print(THIS_TRIAL, "Task:    ", task["colour"], task["number"])
    combined.play()
    THIS_TRIAL += 1


def run_single_talker_trial(event=None):
    print(event)
    master.update()
    segment_length = random.choice(segment_lengths)
    stimulus, _, _, _, _, _ = random_stimulus(segment_length=segment_length)
    stimulus.play()


def generate_numpad():
    buttons = [[0 for x in range(len(numbers))] for y in range(len(colours))]
    for column, c_name in enumerate(colours):
        for row, n_name in enumerate(numbers):
            text_params = {"colour": c_name, "number": n_name}
            button_text = name_to_int(numbers[n_name])
            buttons[column][row] = Button(master,
                                          text=str(button_text),
                                          bg=col_to_hex[c_name],
                                          command=partial(run_masking_trial, text_params))
            buttons[column][row]['font'] = myFont
            buttons[column][row].grid(row=row, column=column)


def generate_name_and_numpad():
    buttons = [[0 for x in range(len(numbers))] for y in range(len(colours) + 1)]
    for row, call_sign in enumerate(call_signs):
        buttons[0][row] = Button(master,
                                 text=call_sign,
                                 command=partial(run_single_talker_trial, call_sign))
        buttons[0][row]['font'] = myFont
        buttons[0][row].grid(row=row, column=0)
    for column, c_name in enumerate(colours):
        for row, n_name in enumerate(numbers):
            text_params = {"colour": c_name, "number": n_name}
            button_text = name_to_int(numbers[n_name])
            buttons[column + 1][row] = Button(master,
                                              text=str(button_text),
                                              bg=col_to_hex[c_name],
                                              command=partial(run_single_talker_experiment, text_params))
            buttons[column + 1][row]['font'] = myFont
            buttons[column + 1][row].grid(row=row, column=column + 1)


def run_masking_experiment():
    global THIS_TRIAL
    THIS_TRIAL = 1
    generate_numpad()
    run_masking_trial()
    master.mainloop()


def run_single_talker_experiment():
    global THIS_TRIAL
    THIS_TRIAL = 1
    generate_name_and_numpad()
    run_single_talker_trial()
    master.mainloop()


run_masking_experiment()

# output = slab.Binaural.silence(samplerate=40000)
# silence = slab.Binaural.silence(duration=1.5, samplerate=40000)
# for i in range(10):
#     target_params = get_params(stim_type="target")
#     masker_params = get_params(stim_type="masker")
#     target = get_stimulus(target_params)
#     masker = get_stimulus(masker_params)
#     target.level += target_level_diff
#     combined = combine_sounds(target, masker, add_helicopter=True)
#     output = slab.Binaural.sequence(output, combined, silence)
# output.play()
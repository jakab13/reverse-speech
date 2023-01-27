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
root_dir = DIR / "samples" / "CRM" / "reversed"


def create_name(talker, call_sign, colour, number, segment):
    base_string = talker + call_sign + colour + number
    name = base_string + "_seg-" + str(segment) + "ms" + "_reversed" + '.wav'
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
target_level_diff = -3
THIS_TRIAL = 0

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


def random_stimulus(segment_length=25, call_sign=None, gender="random"):
    if gender == "random":
        talker, gender = random.choice(list(talkers.items()))
    else:
        talker, gender = random.choice([(t, g) for t, g in talkers.items() if g == gender])
    if call_sign == "Baron":
        call_sign = call_sign_target
    else:
        call_sign = random.choice([cs_id for (cs, cs_id) in call_signs.items() if cs != "Baron"])
    colour = random.choice(list(colours.values()))
    number = random.choice([num_string for num_name, num_string in numbers.items() if num_name != "Seven"])
    file_name = create_name(talker, call_sign, colour, number, segment_length)
    path = root_dir / str(str(segment_length) + "ms_reversed") / file_name
    stimulus = slab.Binaural(path)
    stimulus = normalise_sound(stimulus)
    return stimulus, talker, gender, call_sign, colour, number


task = dict()

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
    segment_length = random.choice(segment_lengths)
    target, target_talker, target_gender, target_call_sign, target_colour, target_number = random_stimulus(call_sign="Baron")
    masker, masker_talker, masker_gender, masker_call_sign, master_colour, master_number = random_stimulus(segment_length=segment_length, gender=target_gender)
    max_duration = max([masker.n_samples, target.n_samples])
    target.level += target_level_diff
    combined = slab.Binaural.silence(duration=max_duration, samplerate=target.samplerate)
    combined.data[:target.n_samples] = target.data
    combined.data[:masker.n_samples] += masker.data
    if add_helicopter:
        helicopter = generate_helicopter(duration=max_duration, samplerate=target.samplerate)
        combined.data += helicopter
    combined = normalise_sound(combined)
    task = {
        "segment_length": segment_length,
        "target_talker": target_talker,
        "target_gender": target_gender,
        "masker_talker": masker_talker,
        "masker_gender": masker_gender,
        "masker_call_sign": value_to_key(call_signs, masker_call_sign),
        "colour": value_to_key(colours, target_colour),
        "number": value_to_key(numbers, target_number),
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
                                 command=partial(set_call_sign, call_sign))
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

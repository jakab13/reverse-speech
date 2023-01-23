import slab
import os
import pathlib
import random
import numpy as np
import tkinter
from tkmacosx import Button
from config import (call_sign_target, call_signs, colours, numbers, talkers, col_to_hex, segment_lengths)

DIR = pathlib.Path(os.getcwd())
root_dir = DIR / "samples" / "CRM"


def create_name(talker, call_sign, colour, number, segment=None):
    base_string = talker + call_sign + colour + number
    if segment is None:
        name = base_string + ".wav"
    else:
        name = base_string + "_seg-" + str(segment) + "ms" + '.wav'
    return name


def name_to_int(name):
    return int(name[-1]) + 1


def normalise_sound(sound):
    sound.data = sound.data / np.max(sound.data)
    return sound


subject_ID = 'jakab'
slab.ResultsFile.results_folder = 'results'
results_file = slab.ResultsFile(subject=subject_ID)
seq = slab.Trialsequence(segment_lengths, n_reps=10)

master = tkinter.Tk()
master.title("Responses")
master.geometry("800x500")
myFont = tkinter.font.Font(size=30)


def button_press(event):
    print(event)


def random_stimulus(segment_length=25, call_sign=None, gender="random"):
    if gender == "random":
        talker, _ = random.choice(list(talkers.items()))
    else:
        talker, _ = random.choice([(t, g) for t, g in talkers.items() if g == gender])
    if call_sign == "Baron":
        call_sign = call_sign_target
    else:
        call_sign = random.choice([cs_id for (cs, cs_id) in call_signs.items() if cs != "Baron"])
    colour = random.choice(list(colours.values()))
    number = random.choice(list(numbers.values()))
    file_name = create_name(talker, call_sign, colour, number, segment_length)
    path = root_dir / str(str(segment_length) + "ms") / file_name
    stimulus = slab.Binaural(path)
    stimulus = normalise_sound(stimulus)
    return stimulus, talker, gender


def run_masking_experiment():
    segment_length = random.choice(segment_lengths)
    target, target_talker, target_gender = random_stimulus(call_sign="Baron")
    masker, masker_talker, masker_gender = random_stimulus(segment_length=segment_length, gender=target_gender)
    target.level -= 3
    combined = slab.Binaural.silence(duration=max([masker.n_samples, target.n_samples]), samplerate=target.samplerate)
    combined.data[:target.n_samples] = target.data
    combined.data[:masker.n_samples] += masker.data
    combined = normalise_sound(combined)
    combined.play()
    master.after(4000, run_masking_experiment)


def run_single_talker_experiment():
    segment_length = random.choice(segment_lengths)
    stimulus, _, _ = random_stimulus(segment_length=segment_length)
    stimulus.play()
    master.after(4000, run_single_talker_experiment)


def generate_numpad():
    buttons = [[0 for x in range(len(numbers))] for y in range(len(colours))]
    for column, c_name in enumerate(colours):
        for row, n_name in enumerate(numbers):
            button_text = name_to_int(numbers[n_name])
            buttons[column][row] = Button(master,
                                          text=str(button_text),
                                          bg=col_to_hex[c_name])
            buttons[column][row].bind('<Button-1>', button_press)
            buttons[column][row]['font'] = myFont
            buttons[column][row].grid(row=row, column=column)


def generate_name_and_numpad():
    buttons = [[0 for x in range(len(numbers))] for y in range(len(colours) + 1)]
    for row, call_sign in enumerate(call_signs):
        buttons[0][row] = Button(master,
                                 text=call_sign)
        buttons[0][row].bind('<Button-1>', button_press)
        buttons[0][row]['font'] = myFont
        buttons[0][row].grid(row=row, column=0)
    for column, c_name in enumerate(colours):
        for row, n_name in enumerate(numbers):
            button_text = name_to_int(numbers[n_name])
            buttons[column + 1][row] = Button(master,
                                              text=str(button_text),
                                              bg=col_to_hex[c_name])
            buttons[column + 1][row].bind('<Button-1>', button_press)
            buttons[column + 1][row]['font'] = myFont
            buttons[column + 1][row].grid(row=row, column=column + 1)


# generate_name_and_numpad()
# run_single_talker_experiment()
generate_numpad()
run_masking_experiment()
master.mainloop()

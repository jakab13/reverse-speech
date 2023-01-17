import slab
import os
import pathlib
import random
import numpy as np
import tkinter
from tkmacosx import Button
from config import (call_sign_target, masker_call_signs, colours, numbers, talkers, col_to_hex, segment_lengths)

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
buttons = [[0 for x in range(len(numbers))] for y in range(len(colours))]
myFont = tkinter.font.Font(size=30)

def button_press(event):
    print(event)


for column, c_name in enumerate(colours):
    for row, n_name in enumerate(numbers):
        button_text = name_to_int(numbers[n_name])
        buttons[column][row] = Button(master,
                                      text=str(button_text),
                                      bg=col_to_hex[c_name])
        buttons[column][row].bind('<Button-1>', button_press)
        buttons[column][row]['font'] = myFont
        buttons[column][row].grid(row=row, column=column)


def run_task():
    # is_waiting = True
    segment_length = random.choice(segment_lengths)
    talker_target, gender_target = random.choice(list(talkers.items()))
    talker_masker, gender_masker = random.choice([(t, g) for t, g in talkers.items()
                                                  if g == gender_target and t != talker_target])
    call_sign_masker = random.choice(list(masker_call_signs.values()))
    colour_target = random.choice(list(colours.values()))
    colour_masker = random.choice(list(colours.values()))
    number_target = random.choice(list(numbers.values()))
    number_masker = random.choice([n for n in numbers.values() if number_target != n])

    file_name_target = create_name(talker_target, call_sign_target, colour_target, number_target, 25)
    file_name_masker = create_name(talker_masker, call_sign_masker, colour_masker, number_masker, segment_length)
    path_target = root_dir / str(str(25) + "ms") / file_name_target
    path_masker = root_dir / str(str(segment_length) + "ms") / file_name_masker

    target = slab.Binaural(path_target)
    masker = slab.Binaural(path_masker)
    target = normalise_sound(target)
    masker = normalise_sound(masker)
    target.level -= 3

    combined = slab.Binaural.silence(duration=max([masker.n_samples, target.n_samples]), samplerate=target.samplerate)

    combined.data[:target.n_samples] = target.data
    combined.data[:masker.n_samples] += masker.data

    combined = normalise_sound(combined)
    combined.play()
    master.after(4000, run_task)


run_task()
master.mainloop()


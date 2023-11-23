import slab
import os
import pathlib
import random
import numpy as np
import tkinter
from tkmacosx import Button
from functools import partial
from config import *
from utils import *

SAMPLERATE = 40000
slab.set_default_samplerate(SAMPLERATE)

ils = pickle.load(open('ils.pickle', 'rb'))

subject_ID = 'test'
# channel_setup_seq = slab.Trialsequence(["left", "right"], n_reps=33)
channel_setup_seq = slab.Trialsequence(["left_target", "right_target"], n_reps=56)
slab.ResultsFile.results_folder = 'results'
results_file = slab.ResultsFile()
stairs = slab.Staircase(start_val=250, n_reversals=12, step_sizes=[50, 40, 30, 20, 10], min_val=20)
seq = slab.Trialsequence(SEGMENT_LENGTHS, n_reps=10)
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



def combine_sounds(target, masker, add_helicopter=False):
    max_duration = max([masker.n_samples, target.n_samples])
    combined = slab.Binaural.silence(duration=max_duration, samplerate=target.samplerate)
    combined.data[:target.n_samples] = target.data
    combined.data[:masker.n_samples] += masker.data
    if add_helicopter:
        helicopter = generate_helicopter(duration=max_duration, segment_length=min(SEGMENT_LENGTHS), samplerate=target.samplerate)
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
        denum = len(CALL_SIGNS) + len(COLOURS) + len(NUMBERS) - 1
        if response["response_call_sign"] == task["task_call_sign"]:
            score += len(CALL_SIGNS) / denum
    else:
        denum = len(COLOURS) + len(NUMBERS) - 1
    if response["response_colour"] == task["task_colour"]:
        score += len(COLOURS) / denum
    if response["response_number"] == task["task_number"]:
        score += (len(NUMBERS) - 1) / denum
    return score


def run_masking_trial(response=None):
    global THIS_TRIAL
    global task
    global stairs
    global masker_azimuth
    global masker_segment_length
    if response is not None:
        response["score"] = get_score(response, task)
        stairs.add_response(response["score"] == 1)
        stairs.plot()
        results_file.write(stairs, tag="stairs")
        results_file.write(stairs.threshold(), tag="threshold")
        results_file.write(response, tag="response")
        # if THIS_TRIAL <= seq.n_trials:
        if not stairs.finished:
            print(THIS_TRIAL - 1, "Response:", response["response_colour"], response["response_number"])
            # print("Correct:", response["score"] == 1)
            # print("Stairs", stairs.data)
            print('')
    # if THIS_TRIAL <= seq.n_trials:
    #     master.update()
    # else:
    #     master.destroy()
    if not stairs.finished:
        master.update()
    else:
        master.destroy()
    target_params = get_params(stim_type="masker")
    masker_params = get_params(stim_type="masker")
    # masker_params = get_params(stim_type="masker")
    target = get_stimulus(target_params)
    target = reverse_sound(target, target_params["segment_length"])
    target = target.externalize()
    masker = get_stimulus(masker_params)
    masker_segment_length = stairs.__next__() / 1000
    masker = reverse_sound(masker, masker_segment_length)
    masker = masker.at_azimuth(masker_azimuth, ils=ils)
    masker = masker.externalize()
    max_duration = max([masker.n_samples, target.n_samples])
    combined = slab.Binaural.silence(duration=max_duration, samplerate=target.samplerate)
    combined.data[:target.n_samples] = target.data / np.amax(np.abs(target.data))
    combined.data[:masker.n_samples] += masker.data / np.amax(np.abs(masker.data))
    combined.data = combined.data / np.amax(np.abs(combined.data))
    task = {
        "subject_ID": subject_ID,
        "target_segment_length": TARGET_SEGMENT_LENGTH,
        "masker_segment_length": masker_params["segment_length"],
        "masker_azimuth": masker_azimuth,
        "target_talker": target_params["talker"],
        "target_gender": target_params["gender"],
        "masker_talker": masker_params["talker"],
        "masker_gender": masker_params["gender"],
        "gender_mix": get_gender_mix(target_params["gender"], masker_params["gender"]),
        "masker_call_sign": value_to_key(CALL_SIGNS, masker_params["call_sign"]),
        "task_colour": value_to_key(COLOURS, target_params["colour"]),
        "task_number": value_to_key(NUMBERS, target_params["number"]),
        "target_level_diff": target_level_diff
    }
    results_file.write(task, tag="task")
    print(THIS_TRIAL, "Task:    ", task["task_colour"], task["task_number"])
    print("Masker segment length:", masker_segment_length)
    combined.play()
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
        "task_call_sign": value_to_key(CALL_SIGNS, single_talker_params["call_sign"]),
        "task_colour": value_to_key(COLOURS, single_talker_params["colour"]),
        "task_number": value_to_key(NUMBERS, single_talker_params["number"])
    }
    results_file.write(task, tag="task")
    print(THIS_TRIAL, "Task:    ", task["task_call_sign"], task["task_colour"], task["task_number"])
    single_talker.play()
    THIS_TRIAL += 1


def set_call_sign(call_sign):
    global CALL_SIGN
    CALL_SIGN = call_sign


def generate_numpad():
    buttons = [[0 for x in range(len(NUMBERS))] for y in range(len(COLOURS))]
    for column, c_name in enumerate(COLOURS):
        for row, n_name in enumerate(NUMBERS):
            response_params = {"response_colour": c_name, "response_number": n_name}
            button_text = name_to_int(NUMBERS[n_name])
            buttons[column][row] = Button(master,
                                          text=str(button_text),
                                          bg=COL_TO_HEX[c_name],
                                          command=partial(run_masking_trial, response_params))
            buttons[column][row]['font'] = myFont
            buttons[column][row].grid(row=row, column=column)


def generate_name_and_numpad():
    buttons = [[0 for x in range(len(NUMBERS))] for y in range(len(COLOURS) + 1)]
    for row, call_sign in enumerate(CALL_SIGNS):
        buttons[0][row] = Button(master,
                                 text=call_sign,
                                         command=partial(set_call_sign, call_sign))
        buttons[0][row]['font'] = myFont
        buttons[0][row].grid(row=row, column=0)
    for column, c_name in enumerate(COLOURS):
        for row, n_name in enumerate(NUMBERS):
            response_params = {"response_colour": c_name, "response_number": n_name}
            button_text = name_to_int(NUMBERS[n_name])
            buttons[column + 1][row] = Button(master,
                                              text=str(button_text),
                                              bg=COL_TO_HEX[c_name],
                                              command=partial(run_single_talker_trial, response_params))
            buttons[column + 1][row]['font'] = myFont
            buttons[column + 1][row].grid(row=row, column=column + 1)


def run_masking_experiment():
    global THIS_TRIAL
    global results_file
    results_filename = "multi-talker"
    results_filename += "_target-segment-" + str(int(TARGET_SEGMENT_LENGTH * 1000)) + "ms"
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


def run_masking_azimuth_experiment():
    global THIS_TRIAL
    global results_file
    global stairs
    global masker_azimuth
    global masker_segment_length
    results_filename = "masking-azimuth"
    results_filename += "_target-segment-" + str(int(TARGET_SEGMENT_LENGTH * 1000)) + "ms"
    results_file = slab.ResultsFile(subject=subject_ID, filename=results_filename)
    THIS_TRIAL = 1
    generate_numpad()
    masker_azimuth = 90
    run_masking_trial()
    master.mainloop()


run_masking_azimuth_experiment()
# run_masking_experiment()
# run_single_talker_experiment()


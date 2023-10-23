import slab
import pickle
import os
from utils import reverse_sound, normalise_sound, get_params, get_stimulus, random_stimulus

os.environ['TERM'] = "linux"
os.environ['TERMINFO'] = "/etc/terminfo"

ils = pickle.load(open('ils.pickle', 'rb'))  # load pickle

stairs = slab.Staircase(start_val=200, n_reversals=5, step_sizes=[50, 25, 5], min_val=30)

for segment_length in stairs:
    segment_length = segment_length / 1000
    target_params = get_params(stim_type="target")
    masker_params = get_params(stim_type="masker")
    target = get_stimulus(target_params)
    masker = get_stimulus(masker_params)
    target_reverse = reverse_sound(target, 0.03)
    masker_reverse = reverse_sound(masker, segment_length)
    masker_reverse_azi = masker_reverse.at_azimuth(45, ils=ils)
    max_duration = max([masker.n_samples, target_reverse.n_samples])
    combined = slab.Binaural.silence(duration=max_duration, samplerate=target_reverse.samplerate)
    combined.data[:target_reverse.n_samples] = target_reverse.data
    combined.data[:masker_reverse_azi.n_samples] += masker_reverse_azi.data
    combined.play()
    response = stairs.simulate_response(threshold=50)
    # with slab.key() as key:
    #     response = key.getch()
    #     print(response)
    # if response == 121:
    #     stairs.add_response(True)
    # else:
    #     stairs.add_response(False)
    stairs.add_response(response)

stairs.plot()
stairs.threshold()

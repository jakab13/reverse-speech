import os
import pathlib
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d

DIR = pathlib.Path(os.getcwd())
results_folder = DIR / "Results"
master_folder = results_folder / "master"
single_talker_file = master_folder / "MASTER_results_single-talker.csv"
# multi_talker_file = master_folder / "MASTER_results_multi-talker.csv"
df_single_talker = pd.read_csv(single_talker_file)
# df_multi_talker = pd.read_csv(multi_talker_file)

mean_syllable_duration = 0.19521027563553273
std_syllable_duration = 0.0812738311185978

subject_IDs = df_single_talker["subject_ID"].unique()

# Per subject
subject_ID = "gina"
df_single_talker_subject = df_single_talker.loc[(df_single_talker["subject_ID"] == subject_ID)]
x_data = range(15, 200, 15)
for idx in range(0, len(df_single_talker_subject), 65):
    session = df_single_talker_subject.iloc[idx:idx+65]
    mean_score_session = session.groupby("single_talker_segment_length")["score"].mean()
    mean_mean = round(mean_score_session.mean(), 2)
    y_data = list(mean_score_session * 100)
    plt.scatter(y=y_data, x=x_data, s=80)
    # mean_scores_subject.plot(style=".")
    plt.plot(x_data, y_data, label=f"Session {int(idx/65) + 1} (mean: {mean_mean})")
plt.xticks(x_data)
plt.ylim(0, 105)
plt.title(f"Intelligibility vs Segment length per session ({subject_ID})")
plt.xlabel("Segment length (ms)")
plt.ylabel("Correct (%)")
plt.legend()
plt.show()

mean_scores_subject = df_single_talker_subject.groupby("single_talker_segment_length")["score"].mean()
mean_scores_subject.plot(style=".")

# Total
# df_single_talker = df_single_talker.loc[(df_single_talker["subject_ID"] != "jakab")]
mean_scores = df_single_talker.groupby("single_talker_segment_length")["score"].mean()
std_scores = df_single_talker.groupby("single_talker_segment_length")["score"].std()
y_data = list(mean_scores*100)
y_err = std_scores * 100
cubic_interpolation_model = interp1d(x_data, y_data, kind="cubic")
X_ = np.linspace(15, 195, 500)
Y_ = cubic_interpolation_model(X_)


def sigmoid(x, L, x0, k, b):
    y = L / (1 + np.exp(-k*(x-x0))) + b
    return y


p0 = [max(y_data), np.median(x_data), -1, min(y_data)]  # this is an mandatory initial guess
popt, pcov = curve_fit(sigmoid, x_data, y_data, p0, method='dogbox')

y_sigmoid = sigmoid(x_data, *popt)

# plt.plot(X_, Y_)
plt.scatter(y=y_data, x=x_data, s=80, label="Grand average")
plt.plot(x_data, y_sigmoid, c="#ff7f0e", label="Sigmoid fit")

# plt.errorbar(x_data, y_data, yerr=y_err, fmt="o")
plt.xticks(x_data)
plt.ylim(0, 105)
plt.title("Intelligibility vs Segment length")
plt.xlabel("Segment length (ms)")
plt.ylabel("Correct (%)")
plt.legend()
plt.show()

for subject_ID in subject_IDs:
    df_single_talker_subject = df_single_talker.loc[(df_single_talker["subject_ID"] == subject_ID)]
    mean_scores_subject = df_single_talker_subject.groupby("single_talker_segment_length")["score"].mean()
    y_data = list(mean_scores_subject * 100)
    plt.scatter(y=y_data, x=x_data, s=80)
    # mean_scores_subject.plot(style=".")
    plt.plot(x_data, y_data, label=subject_ID)
plt.xticks(x_data)
plt.ylim(0, 105)
plt.title("Intelligibility vs Segment length per subject")
plt.xlabel("Segment length (ms)")
plt.ylabel("Correct (%)")
plt.legend()
plt.show()
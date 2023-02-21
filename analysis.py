import os
import pathlib
import pandas as pd

DIR = pathlib.Path(os.getcwd())
results_folder = DIR / "Results"
master_folder = results_folder / "master"
single_talker_file = master_folder / "MASTER_results_single-talker.csv"
# multi_talker_file = master_folder / "MASTER_results_multi-talker.csv"
df_single_talker = pd.read_csv(single_talker_file)
# df_multi_talker = pd.read_csv(multi_talker_file)

# Filter
df_single_talker_filter = df_single_talker.loc[df_single_talker["subject_ID"] != "jakab"]

# Per subject
subject_ID = "secondhannah"
df_single_talker_subject = df_single_talker.loc[df_single_talker["subject_ID"] == subject_ID]
mean_scores_subject = df_single_talker_subject.groupby("single_talker_segment_length")["score"].mean()
mean_scores_subject.plot(style=".")

# Total
mean_scores = df_single_talker.groupby("single_talker_segment_length")["score"].mean()
mean_scores.plot(style=".")

# anova tests go here
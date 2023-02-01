import slab
import os
import pathlib
import pandas as pd

DIR = pathlib.Path(os.getcwd())
results_folder = DIR / "Results"
subjects = [f for f in os.listdir(results_folder) if not f.startswith('.')]
subjects = [f for f in subjects if f != 'test']


def generate_df(results_file_paths):
    df = pd.DataFrame
    for results_file_path in results_file_paths:
        tasks = slab.ResultsFile.read_file(subject_path / results_file_path, tag="task")
        responses = slab.ResultsFile.read_file(subject_path / results_file_path, tag="response")
        df_tasks = pd.DataFrame(tasks)
        df_responses = pd.DataFrame(responses)
        df = pd.concat([df_tasks, df_responses], axis=1)
    return df


for subject in subjects:
    subject_path = results_folder / subject
    single_talker_file_paths = [f for f in os.listdir(subject_path) if "single-talker" in f]
    multi_talker_file_paths = [f for f in os.listdir(subject_path) if "multi-talker" in f]
    df_single_talker = generate_df(single_talker_file_paths)
    df_multi_talker = generate_df(multi_talker_file_paths)
    df_single_talker.to_csv(subject_path / str(subject + "_results_single-talker.csv"))
    df_multi_talker.to_csv(subject_path / str(subject + "_results_multi-talker.csv"))

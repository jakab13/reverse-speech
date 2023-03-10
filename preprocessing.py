import slab
import os
import pathlib
import pandas as pd


def generate_df(results_file_paths):
    df = pd.DataFrame()
    for results_file_path in results_file_paths:
        tasks = slab.ResultsFile.read_file(results_file_path, tag="task")
        if type(tasks) is not list:
            tasks = [tasks]
        responses = slab.ResultsFile.read_file(results_file_path, tag="response")
        if type(responses) is not list:
            responses = [responses]
        df_tasks = pd.DataFrame(tasks)
        df_responses = pd.DataFrame(responses)
        df_block = pd.concat([df_tasks, df_responses], axis=1)
        df = df.append(df_block, ignore_index=True)
    return df


def generate_csvs(subjects):
    df_master_single_talker = pd.DataFrame()
    df_master_multi_talker = pd.DataFrame()
    for subject in subjects:
        subject_path = results_folder / subject
        single_talker_file_paths = [subject_path / f for f in os.listdir(subject_path) if "single-talker" in f and "results" not in f]
        multi_talker_file_paths = [subject_path / f for f in os.listdir(subject_path) if "multi-talker" in f and "results" not in f]
        df_single_talker = generate_df(single_talker_file_paths)
        df_multi_talker = generate_df(multi_talker_file_paths)
        df_master_single_talker = df_master_single_talker.append(df_single_talker, ignore_index=True)
        df_master_multi_talker = df_master_multi_talker.append(df_multi_talker, ignore_index=True)
        if not df_single_talker.empty:
            df_single_talker.to_csv(master_folder / str(subject + "_results_single-talker.csv"))
        if not df_multi_talker.empty:
            df_multi_talker.to_csv(master_folder / str(subject + "_results_multi-talker.csv"))
    if not df_master_single_talker.empty:
        df_master_single_talker.to_csv(master_folder / "MASTER_results_single-talker.csv")
    if not df_master_multi_talker.empty:
        df_master_multi_talker.to_csv(master_folder / "MASTER_results_multi-talker.csv")


if __name__ == "__main__":
    DIR = pathlib.Path(os.getcwd())
    results_folder = DIR / "Results"
    master_folder = results_folder / "master"
    subjects = [f for f in os.listdir(results_folder) if not f.startswith('.') and "results" not in f]
    subjects = [f for f in subjects if f != 'test' and f != 'master']
    generate_csvs(subjects)

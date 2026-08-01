# data_loader.py
# Shared helper for reading the GitHub Archive dataset. Used by every
# week's db module so we're not all writing our own file-parsing code.
#
# Heads up: the dataset files are JSON Lines (one JSON object per line),
# not one big JSON array. json.load() on the whole file will error out.
# Some of these files are huge too (Languages.json is 400+ MB) so we read
# them one line at a time with a generator instead of loading it all into
# memory at once.

import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

DATASET_FILES = {
    "commits": "Commits.json",
    "contents": "Contents.json",
    "files": "Files.json",
    "languages": "Languages.json",
    "licenses": "Licenses.json",
    "sample_commits": "Sample_Commits.json",
    "sample_contents": "Sample_Contents.json",
    "sample_files": "Sample_Files.json",
    "sample_repos": "Sample_Repos.json",
}


def load_jsonl(filepath, limit=None):
    """Generator - reads a JSON Lines file, one record at a time.
    Pass a limit to stop early instead of reading the whole file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Could not find dataset file: {filepath}\n"
            f"Unzip GitHubArchive-Dataset.zip into the data/ folder first."
        )

    count = 0
    with open(filepath, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue  # skip bad lines instead of crashing the whole load
            count += 1
            if limit is not None and count >= limit:
                break


def load_dataset(name, limit=None):
    """Load one of the known dataset files by short name (see DATASET_FILES).
    Returns a list, so only use this for the smaller files or with a limit."""
    if name not in DATASET_FILES:
        raise ValueError(f"Unknown dataset '{name}'. Valid options: {list(DATASET_FILES.keys())}")
    filepath = os.path.join(DATA_DIR, DATASET_FILES[name])
    return list(load_jsonl(filepath, limit=limit))


def dataset_path(name):
    if name not in DATASET_FILES:
        raise ValueError(f"Unknown dataset '{name}'. Valid options: {list(DATASET_FILES.keys())}")
    return os.path.join(DATA_DIR, DATASET_FILES[name])

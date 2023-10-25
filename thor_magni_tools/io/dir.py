import os


def create_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

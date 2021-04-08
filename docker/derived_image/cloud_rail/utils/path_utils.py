import os
from typing import List


def is_hidden_folder(src_dir: str, allow_folders: List[str] = None):
    if allow_folders:
        allow = allow_folders + ['.', '..']
    else:
        allow = ['.', '..']
    dirs = os.path.abspath(src_dir).split('/')
    return any(dir_name.startswith('.') and dir_name not in allow for dir_name in dirs)
